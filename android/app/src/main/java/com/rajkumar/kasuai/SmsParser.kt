package com.rajkumar.kasuai

import java.util.Locale

data class ParsedSms(
    val isExpense: Boolean,
    val amount: Double,
    val category: String,
    val merchant: String,
    val explanation: String
)

object SmsParser {
    private val BALANCE_REGEX = Regex("(?i)(?:avl\\s*bal|avbl\\s*bal|balance|bal|acct\\s*bal)\\s*:?\\s*(?:rs\\.?|inr|₹)?\\s*[\\d,]+(?:\\.\\d{1,2})?")
    private val AMOUNT_PATTERNS = listOf(
        Regex("(?i)(?:rs\\.?|inr|₹)\\s*([\\d,]+(?:\\.\\d{1,2})?)"),
        Regex("(?i)(?:debited\\s+by|debited\\s+for|paid|spent|withdrawn)\\s*(?:rs\\.?|inr|₹)?\\s*([\\d,]+(?:\\.\\d{1,2})?)"),
        Regex("(?i)([\\d,]+(?:\\.\\d{1,2})?)\\s*(?:rs\\.?|inr|₹)")
    )
    private val DEBIT_WORDS = listOf("debited", "spent", "paid", "recharge of", "withdrawn", "transferred", "sent rs", "deducted", "vpa")

    fun parse(sms: String): ParsedSms {
        val lower = sms.lowercase(Locale.ROOT)
        val isDebit = DEBIT_WORDS.any { lower.contains(it) }
        val isOtpOrAlert = lower.contains("otp") || lower.contains("mandate") || lower.contains("statement") || (!isDebit && lower.contains("credited"))

        if (isOtpOrAlert || !isDebit) {
            val cat = if (lower.contains("credited")) "வரவு (Credit)" else "வங்கி அறிவிப்பு / OTP"
            return ParsedSms(
                isExpense = false,
                amount = 0.0,
                category = cat,
                merchant = "SMS",
                explanation = "தகவல் அறிவிப்பு செய்தி"
            )
        }

        // Strip balance patterns so available balance is not picked up as debit amount
        val sanitizedText = sms.replace(BALANCE_REGEX, " ")
        var amt = 0.0
        for (pattern in AMOUNT_PATTERNS) {
            val match = pattern.find(sanitizedText)
            if (match != null) {
                val cleanStr = match.groupValues[1].replace(",", "").trim()
                amt = cleanStr.toDoubleOrNull() ?: 0.0
                if (amt > 0) break
            }
        }

        if (amt <= 0) {
            return ParsedSms(
                isExpense = false,
                amount = 0.0,
                category = "இதர அறிவிப்பு",
                merchant = "SMS",
                explanation = "செலவுத் தொகை கண்டறியப்படவில்லை"
            )
        }

        // Extract Merchant / Payee
        var merchant = "கடை / UPI"
        val merchantMatch = Regex("(?i)(?:to|at|vpa)\\s+([A-Za-z0-9\\s&]+?)(?:\\s+on|\\s+ref|\\s+upi|\\s+a/c|\\.|\n|$)").find(sms)
        if (merchantMatch != null) {
            val mName = merchantMatch.groupValues[1].trim()
            if (mName.length in 3..40) {
                merchant = mName
            }
        }

        val category = categorize(merchant + " " + sms)

        return ParsedSms(
            isExpense = true,
            amount = amt,
            category = category,
            merchant = merchant,
            explanation = "$category - ₹$amt"
        )
    }

    fun categorize(text: String): String {
        val lower = text.lowercase(Locale.ROOT)
        return when {
            listOf("tea", "coffee", "bakery", "snack", "sweets", "juice", "cafe", "biscuit").any { lower.contains(it) } -> "டீ & சிற்றுண்டி"
            listOf("hotel", "restaurant", "catering", "cater", "bhavan", "mess", "swiggy", "zomato", "maligai", "mart", "grocery", "vegetable", "supermarket", "milk", "kirana", "rice", "store").any { lower.contains(it) } -> "மளிகை & உணவு"
            listOf("petrol", "fuel", "diesel", "iocl", "hpcl", "bpcl", "fastag", "shell", "traders", "oil", "service", "auto", "garage", "puncture", "toll").any { lower.contains(it) } -> "வாகனம் & Fuel"
            listOf("medical", "pharmacy", "hospital", "apollo", "clinic", "health", "pharma", "lab", "medicals", "doctor").any { lower.contains(it) } -> "மருத்துவம்"
            listOf("lntfin", "loan", "emi", "bajaj", "muthoot", "finance", "credit card", "hdfc bank loan", "chola", "shriram", "equitas").any { lower.contains(it) } -> "கடன்கள் & EMI"
            listOf("tangedco", "electricity", "eb bill", "water", "gas", "cylinder", "indane", "hp gas", "bharat gas").any { lower.contains(it) } -> "மின்சாரக் கட்டணம்"
            listOf("fertilizer", "tractor", "seeds", "agri", "pesticide", "harvest", "diesel farm").any { lower.contains(it) } -> "விவசாயச் செலவு"
            else -> "இதர செலவுகள்"
        }
    }
}
