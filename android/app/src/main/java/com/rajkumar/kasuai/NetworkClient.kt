package com.rajkumar.kasuai

import android.content.Context
import android.util.Log
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.TimeUnit
import kotlin.math.abs

object NetworkClient {
    private const val TAG = "KasuAI_Net"
    private val JSON_MEDIA_TYPE = "application/json; charset=utf-8".toMediaType()

    // 24/7 Supabase Cloud REST API Credentials
    private const val SUPABASE_URL = "https://jfplghpfxlbatmaeokmb.supabase.co"
    private const val SUPABASE_KEY = "sb_publishable_8NIaGgFZnmM_IkDnl8atYQ_MV9gtsTq"

    // Deduplication window: 15 minutes (in milliseconds)
    private const val DEDUP_WINDOW_MS = 15 * 60 * 1000L

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    /**
     * Checks if this transaction is a duplicate in the local device cache.
     */
    private fun isLocalDuplicate(context: Context, user: String, amount: Double, identifier: String): Boolean {
        val prefs = context.getSharedPreferences("kasuai_dedup_prefs", Context.MODE_PRIVATE)
        val now = System.currentTimeMillis()
        val allEntries = prefs.all

        // Check if an expense with the same amount and user was processed within the dedup window
        for ((key, value) in allEntries) {
            val timestamp = (value as? Long) ?: 0L
            if (now - timestamp < DEDUP_WINDOW_MS) {
                // Key format: "user|amount|..."
                val parts = key.split("|")
                if (parts.size >= 2) {
                    val savedUser = parts[0]
                    val savedAmt = parts[1].toDoubleOrNull() ?: 0.0
                    if (savedUser == user && abs(savedAmt - amount) < 0.01) {
                        Log.w(TAG, "Deduplication: Matched local cache ($key) within ${(now - timestamp) / 1000}s. Skipping duplicate.")
                        return true
                    }
                }
            } else {
                // Clean up stale entries older than 2 hours
                prefs.edit().remove(key).apply()
            }
        }
        return false
    }

    /**
     * Records a transaction in the local device cache to prevent duplicate processing.
     */
    private fun recordLocalTransaction(context: Context, user: String, amount: Double, identifier: String) {
        val prefs = context.getSharedPreferences("kasuai_dedup_prefs", Context.MODE_PRIVATE)
        val key = "$user|$amount|$identifier"
        prefs.edit().putLong(key, System.currentTimeMillis()).apply()
    }

    /**
     * Checks if this transaction was already recorded in Supabase Cloud within the last 15 minutes.
     */
    private fun isCloudDuplicate(user: String, amount: Double): Boolean {
        return try {
            val encodedUser = java.net.URLEncoder.encode(user, "UTF-8")
            val endpoint = "$SUPABASE_URL/rest/v1/expenses?user=eq.$encodedUser&amount=eq.$amount&order=id.desc&limit=3"
            val request = Request.Builder()
                .url(endpoint)
                .get()
                .addHeader("apikey", SUPABASE_KEY)
                .addHeader("Authorization", "Bearer $SUPABASE_KEY")
                .build()

            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val bodyStr = response.body?.string() ?: ""
                val array = JSONArray(bodyStr)
                if (array.length() > 0) {
                    val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                    val now = Date()
                    for (i in 0 until array.length()) {
                        val item = array.getJSONObject(i)
                        val dateStr = item.optString("date", "")
                        val itemDate = try { sdf.parse(dateStr) } catch (e: Exception) { null }
                        if (itemDate != null && abs(now.time - itemDate.time) < DEDUP_WINDOW_MS) {
                            Log.w(TAG, "Deduplication: Cloud already has this expense ($dateStr, ₹$amount). Skipping duplicate insert.")
                            return true
                        }
                    }
                }
            }
            false
        } catch (e: Exception) {
            Log.e(TAG, "Cloud duplicate check error (proceeding safely): ${e.message}")
            false
        }
    }

    /**
     * Sends an expense transaction to Supabase with multi-layer deduplication.
     */
    fun sendExpense(
        context: Context,
        user: String,
        category: String,
        amount: Double,
        mode: String,
        merchant: String,
        notes: String
    ): Boolean {
        // 1. Layer 1: Check Local Android Deduplication Cache
        val identifier = "${merchant.hashCode()}_${notes.hashCode()}"
        if (isLocalDuplicate(context, user, amount, identifier)) {
            Log.i(TAG, "Skipping duplicate transaction (₹$amount, $merchant) - already handled locally.")
            return true // Return true so WorkManager doesn't retry
        }

        // 2. Layer 2: Check Cloud Supabase Database
        if (isCloudDuplicate(user, amount)) {
            Log.i(TAG, "Skipping duplicate transaction (₹$amount, $merchant) - already exists in Supabase.")
            recordLocalTransaction(context, user, amount, identifier)
            return true
        }

        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        val currentTimestamp = sdf.format(Date())

        val expArray = JSONArray().apply {
            put(JSONObject().apply {
                put("date", currentTimestamp)
                put("user", user)
                put("category", category)
                put("amount", amount)
                put("mode", mode)
                put("merchant", merchant)
                put("notes", notes)
            })
        }

        val success = postToSupabase("expenses", expArray.toString())
        if (success) {
            recordLocalTransaction(context, user, amount, identifier)
            Log.i(TAG, "Expense successfully recorded: ₹$amount to $merchant ($category)")
        }
        return success
    }

    /**
     * Sync an incoming SMS message.
     */
    fun sendSmsToServer(context: Context, sender: String, message: String): Boolean {
        val prefs = context.getSharedPreferences("kasuai_prefs", Context.MODE_PRIVATE)
        val activeUser = prefs.getString("active_user", "👤 ராஜ்குமார் (கணவர்)") ?: "👤 ராஜ்குமார் (கணவர்)"

        val parsed = SmsParser.parse(message)

        return if (parsed.isExpense && parsed.amount > 0) {
            sendExpense(
                context = context,
                user = activeUser,
                category = parsed.category,
                amount = parsed.amount,
                mode = "UPI / Mobile SMS",
                merchant = parsed.merchant,
                notes = message
            )
        } else {
            val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
            val currentTimestamp = sdf.format(Date())
            val alertArray = JSONArray().apply {
                put(JSONObject().apply {
                    put("date", currentTimestamp)
                    put("sender", sender)
                    put("category", parsed.category)
                    put("explanation", parsed.explanation)
                    put("raw_text", message)
                })
            }
            postToSupabase("other_alerts", alertArray.toString())
        }
    }

    /**
     * Sync a notification captured from Paytm, GPay, PhonePe, CRED, etc.
     */
    fun sendPaymentNotification(
        context: Context,
        amount: Double,
        merchant: String,
        category: String,
        appName: String,
        rawNotification: String
    ): Boolean {
        val prefs = context.getSharedPreferences("kasuai_prefs", Context.MODE_PRIVATE)
        val activeUser = prefs.getString("active_user", "👤 ராஜ்குமார் (கணவர்)") ?: "👤 ராஜ்குமார் (கணவர்)"

        return sendExpense(
            context = context,
            user = activeUser,
            category = category,
            amount = amount,
            mode = "$appName Notification",
            merchant = merchant,
            notes = rawNotification
        )
    }

    private fun postToSupabase(table: String, jsonArrayString: String): Boolean {
        val endpoint = "$SUPABASE_URL/rest/v1/$table"
        val body = jsonArrayString.toRequestBody(JSON_MEDIA_TYPE)

        val request = Request.Builder()
            .url(endpoint)
            .post(body)
            .addHeader("apikey", SUPABASE_KEY)
            .addHeader("Authorization", "Bearer $SUPABASE_KEY")
            .addHeader("Content-Type", "application/json")
            .addHeader("Prefer", "return=representation")
            .build()

        return try {
            val response = client.newCall(request).execute()
            val code = response.code
            val respBody = response.body?.string() ?: ""
            Log.d(TAG, "Supabase [$table] response: $code -> $respBody")
            response.isSuccessful
        } catch (e: Exception) {
            Log.e(TAG, "Failed posting to Supabase [$table]: ${e.message}")
            false
        }
    }
}
