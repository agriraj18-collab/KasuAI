package com.rajkumar.kasuai

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.Locale

class PaymentNotificationListener : NotificationListenerService() {

    companion object {
        private const val TAG = "KasuAI_NotifyListener"
        private const val CHANNEL_ID = "kasuai_alerts"

        // Packages of popular Indian Payment & Banking apps
        private val SUPPORTED_PACKAGES = mapOf(
            "net.one97.paytm" to "Paytm",
            "com.google.android.apps.nbu.paisa.user" to "Google Pay",
            "com.phonepe.app" to "PhonePe",
            "com.dreamplug.androidapp" to "CRED",
            "in.org.npci.upiapp" to "BHIM",
            "com.sbi.upi" to "BHIM SBI Pay",
            "com.icicibank.mobile" to "iMobile ICICI",
            "com.axis.mobile" to "Axis Mobile",
            "com.msf.kbank.mobile" to "Kotak Bank",
            "com.hdfcbank.payzapp" to "PayZapp HDFC"
        )

        private val AMOUNT_PATTERNS = listOf(
            Regex("(?i)(?:paid\\s+|payment\\s+of\\s+|sent\\s+|debited\\s+(?:for\\s+)?)(?:rs\\.?|inr|₹)?\\s*([\\d,]+(?:\\.\\d{1,2})?)"),
            Regex("(?i)(?:rs\\.?|inr|₹)\\s*([\\d,]+(?:\\.\\d{1,2})?)"),
            Regex("(?i)([\\d,]+(?:\\.\\d{1,2})?)\\s*(?:rs\\.?|inr|₹)"),
            Regex("(?:-\\s*)?(?:rs\\.?|inr|₹)?\\s*([\\d,]+(?:\\.\\d{1,2})?)")
        )

        // Only ignore true non-financial notifications (DO NOT ignore 'offer' or 'discount' because Paytm appends marketing text to receipts)
        private val STRICT_IGNORE = listOf(
            "login otp", "signin otp", "verification code", "security code",
            "bill due", "bill generated", "statement available", "auto-debit scheduled"
        )

        private val CREDIT_KEYWORDS = listOf(
            "received rs", "credited to", "payment received from", "money added to wallet", "cashback credited"
        )

        private var lastProcessedHash: Int = 0
        private var lastProcessedTime: Long = 0L
    }

    override fun onListenerConnected() {
        super.onListenerConnected()
        Log.i(TAG, "✅ KasuAI Payment Notification Listener Connected & Active!")
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        val pkgName = sbn.packageName ?: return
        val appName = SUPPORTED_PACKAGES[pkgName] ?: return

        val extras = sbn.notification?.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: ""
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: ""
        val bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString() ?: ""
        val fullContent = "$title | $text | $bigText".trim()

        if (fullContent.isBlank()) return

        val lower = fullContent.lowercase(Locale.ROOT)

        // Ignore true OTPs and pure login security alerts
        if (STRICT_IGNORE.any { lower.contains(it) }) {
            return
        }

        // Ignore incoming credits (e.g. money received)
        if (CREDIT_KEYWORDS.any { lower.contains(it) }) {
            return
        }

        // Prevent repeated processing of identical notification within 10 seconds
        val now = System.currentTimeMillis()
        val contentHash = fullContent.hashCode()
        if (contentHash == lastProcessedHash && (now - lastProcessedTime) < 10_000L) {
            return
        }
        lastProcessedHash = contentHash
        lastProcessedTime = now

        Log.d(TAG, "[$appName] Incoming payment notification: $fullContent")

        // Parse amount
        var amount = 0.0
        for (pattern in AMOUNT_PATTERNS) {
            val match = pattern.find(fullContent)
            if (match != null) {
                val cleanStr = match.groupValues[1].replace(",", "").trim()
                val parsed = cleanStr.toDoubleOrNull() ?: 0.0
                if (parsed > 0) {
                    amount = parsed
                    break
                }
            }
        }

        if (amount <= 0) {
            // Log unparsed alert for debugging transparency
            CoroutineScope(Dispatchers.IO).launch {
                NetworkClient.sendSmsToServer(applicationContext, "$appName (Notification)", fullContent)
            }
            return
        }

        // Parse Merchant / Payee
        var merchant = "கடை / UPI"

        // 1. Check if title itself is the payee name (e.g., "Manoharan Ponnusamy")
        val cleanTitle = title.trim()
        val lowerTitle = cleanTitle.lowercase(Locale.ROOT)
        val isGenericTitle = listOf("paytm", "payment", "successful", "debited", "paid", "upi", "alert", "transaction", "reward", "cred", "google pay", "phonepe").any { lowerTitle.contains(it) }

        if (cleanTitle.length in 3..40 && !isGenericTitle) {
            merchant = cleanTitle
        } else {
            // 2. Extract from "paid to <merchant>", "to <merchant>", "on <merchant>"
            val patterns = listOf(
                Regex("(?i)(?:paid\\s+to|payment\\s+to|sent\\s+to|purchase\\s+on)\\s+([A-Za-z0-9\\s&.'-]+?)(?:\\s+was|\\s+is|\\s+successful|\\s+using|\\s+from|\\s+via|\\s+upi|\\.|\||$)"),
                Regex("(?i)(?:to|at)\\s+([A-Za-z0-9\\s&.'-]+?)(?:\\s+successful|\\s+using|\\s+from|\\s+via|\\s+upi|\\.|\||$)")
            )
            for (p in patterns) {
                val mMatch = p.find(fullContent)
                if (mMatch != null) {
                    val candidate = mMatch.groupValues[1].trim()
                    // Avoid false positives like "claim your reward"
                    if (candidate.length in 3..40 && !candidate.contains("claim", ignoreCase = true) && !candidate.contains("reward", ignoreCase = true)) {
                        merchant = candidate
                        break
                    }
                }
            }
        }

        val category = SmsParser.categorize(merchant + " " + fullContent)

        Log.i(TAG, "Detected $appName Payment: ₹$amount to $merchant ($category)")

        // Send to Supabase in background
        CoroutineScope(Dispatchers.IO).launch {
            val success = NetworkClient.sendPaymentNotification(
                context = applicationContext,
                amount = amount,
                merchant = merchant,
                category = category,
                appName = appName,
                rawNotification = fullContent
            )

            if (success) {
                showSuccessNotification(amount, merchant, category, appName)
            }
        }
    }

    private fun showSuccessNotification(amount: Double, merchant: String, category: String, appName: String) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "KasuAI செலவு எச்சரிக்கைகள்",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            manager.createNotificationChannel(channel)
        }

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("🪙 KasuAI: ₹${amount.toInt()} ($merchant)")
            .setContentText("[$appName] $category செலவு கிளவுட் கணக்கில் சேர்க்கப்பட்டது!")
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        manager.notify((System.currentTimeMillis() % 10000).toInt(), notification)
    }
}
