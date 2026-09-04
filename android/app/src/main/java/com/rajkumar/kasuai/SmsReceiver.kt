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
            "upi", "inr", "rs.", "rs ", "₹", "bank", "otp", 
            "mandate", "a/c", "acct", "autopay"
        )
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            if (messages.isNullOrEmpty()) return

            val sender = messages[0].originatingAddress ?: "Unknown"
            val fullBody = messages.joinToString(separator = "") { it.messageBody ?: "" }

            Log.d(TAG, "Incoming SMS from $sender: $fullBody")

            val lower = fullBody.lowercase()
            val isFinancial = FINANCIAL_KEYWORDS.any { lower.contains(it) }

            if (isFinancial) {
                Log.d(TAG, "Financial SMS detected! Scheduling KasuAI background sync...")

                // Schedule background sync worker
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

                WorkManager.getInstance(context).enqueue(syncRequest)

                // Show local status bar notification
                showNotification(context, "🪙 KasuAI தானியங்கிப் பதிவு", "வங்கி SMS பெறப்பட்டு கணக்கில் சேர்க்கப்படுகிறது...")
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
