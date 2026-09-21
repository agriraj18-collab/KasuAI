package com.rajkumar.kasuai

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Telephony
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.work.Constraints
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.workDataOf

class SmsReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "KasuAI_Receiver"
        private const val CHANNEL_ID = "kasuai_alerts"
        private val FINANCIAL_KEYWORDS = listOf(
            "debited", "credited", "spent", "paid", "withdrawn", 
            "upi", "inr", "rs.", "rs ", "₹", "bank", 
            "mandate", "a/c", "acct", "autopay"
        )
        private var lastReceivedHash: Int = 0
        private var lastReceivedTime: Long = 0L
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            if (messages.isNullOrEmpty()) return

            val sender = messages[0].originatingAddress ?: "Unknown"
            val fullBody = messages.joinToString(separator = "") { it.messageBody ?: "" }

            if (fullBody.isBlank()) return

            val lower = fullBody.lowercase()

            // 1. Strictly ignore all OTP messages — do not record, do not sync, do not notify
            val isOtp = lower.contains("otp") || lower.contains("one-time password") || lower.contains("verification code")
            if (isOtp) {
                Log.d(TAG, "OTP SMS ignored without recording: $sender")
                return
            }

            val now = System.currentTimeMillis()
            val msgHash = fullBody.hashCode()

            // Skip exact duplicate SMS broadcasts within 30 seconds
            if (msgHash == lastReceivedHash && (now - lastReceivedTime) < 30_000L) {
                Log.d(TAG, "Duplicate SMS broadcast ignored (hash: $msgHash)")
                return
            }
            lastReceivedHash = msgHash
            lastReceivedTime = now

            Log.d(TAG, "Incoming SMS from $sender: $fullBody")

            val isFinancial = FINANCIAL_KEYWORDS.any { lower.contains(it) }

            if (isFinancial) {
                Log.d(TAG, "Financial SMS detected! Scheduling KasuAI background sync...")

                val workData = workDataOf(
                    "sender" to sender,
                    "message" to fullBody
                )

                val constraints = Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()

                val syncRequest = OneTimeWorkRequestBuilder<SmsSyncWorker>()
                    .setConstraints(constraints)
                    .setInputData(workData)
                    .build()

                // Enqueue unique work to avoid duplicate runs
                val uniqueWorkName = "sms_sync_${Math.abs(msgHash)}"
                WorkManager.getInstance(context).enqueueUniqueWork(
                    uniqueWorkName,
                    ExistingWorkPolicy.KEEP,
                    syncRequest
                )

                // Show local status bar notification with parsed details
                val parsed = SmsParser.parse(fullBody)
                if (parsed.isExpense && parsed.amount > 0) {
                    showNotification(
                        context,
                        "🪙 KasuAI: ₹${parsed.amount.toInt()} (${parsed.merchant})",
                        "${parsed.category} செலவு கிளவுட் கணக்கில் சேர்க்கப்படுகிறது..."
                    )
                } else {
                    showNotification(
                        context,
                        "🔔 KasuAI: $sender",
                        "வங்கி அறிவிப்பு செய்தி கிளவுடில் பதியப்படுகிறது..."
                    )
                }
            }
        }
    }

    private fun showNotification(context: Context, title: String, content: String) {
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "KasuAI செலவு எச்சரிக்கைகள்",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            manager.createNotificationChannel(channel)
        }

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(content)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        manager.notify((System.currentTimeMillis() % 10000).toInt(), notification)
    }
}
