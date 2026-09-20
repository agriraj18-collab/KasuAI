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
            Regex("(?i)([\\d,]+(?:\\.\\d{1,2})?)\\s*(?:rs\\.?|inr|₹)")
        )

        private val IGNORE_KEYWORDS = listOf(
            "otp", "login", "security code", "cashback received",
            "promotional", "discount", "offer", "recharge successful",
            "received rs", "credited", "payment received"
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
        val fullContent = "$title $text $bigText".trim()

        if (fullContent.isBlank()) return

        val lower = fullContent.lowercase(Locale.ROOT)

        // Ignore OTP, incoming payments (credits), and promotional ads
        if (IGNORE_KEYWORDS.any { lower.contains(it) }) {
            return
        }

        // Must indicate an outgoing payment or debit
        val isDebitOrPaid = listOf("paid", "payment", "sent", "debited", "spent", "transferred").any { lower.contains(it) }
        if (!isDebitOrPaid) {
            return
        }

        // Prevent repeated processing within 10 seconds
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
            return
        }

        // Parse Merchant / Payee
        var merchant = "கடை / UPI"
        val merchantMatch = Regex("(?i)(?:to|at)\\s+([A-Za-z0-9\\s&.'-]+?)(?:\\s+successful|\\s+using|\\s+from|\\s+upi|\\s+on|\\.|\n|$)").find(fullContent)
        if (merchantMatch != null) {
            val candidate = merchantMatch.groupValues[1].trim()
            if (candidate.length in 3..45) {
                merchant = candidate
            }
        } else if (title.contains(" to ", ignoreCase = true)) {
            val parts = title.split(Regex("(?i)\\sto\\s"))
            if (parts.size >= 2) {
                val candidate = parts[1].trim()
                if (candidate.length in 3..45) {
                    merchant = candidate
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
