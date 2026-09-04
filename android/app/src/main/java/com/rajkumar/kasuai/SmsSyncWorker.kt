package com.rajkumar.kasuai

import android.content.Context
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

class SmsSyncWorker(
    private val context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        val sender = inputData.getString("sender") ?: "Unknown"
        val message = inputData.getString("message") ?: ""

        if (message.isBlank()) {
            return Result.failure()
        }

        Log.d("KasuAI_Worker", "Background syncing SMS from $sender...")
        val success = NetworkClient.sendSmsToServer(context, sender, message)

        return if (success) {
            Log.d("KasuAI_Worker", "SMS synced successfully!")
            Result.success()
        } else {
            Log.w("KasuAI_Worker", "SMS sync failed. Will retry later.")
            Result.retry()
        }
    }
}
