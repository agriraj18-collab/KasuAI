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

object NetworkClient {
    private const val TAG = "KasuAI_Net"
    private val JSON_MEDIA_TYPE = "application/json; charset=utf-8".toMediaType()

    // 24/7 Supabase Cloud REST API Credentials
    private const val SUPABASE_URL = "https://jfplghpfxlbatmaeokmb.supabase.co"
    private const val SUPABASE_KEY = "sb_publishable_8NIaGgFZnmM_IkDnl8atYQ_MV9gtsTq"

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    fun sendSmsToServer(context: Context, sender: String, message: String): Boolean {
        val prefs = context.getSharedPreferences("kasuai_prefs", Context.MODE_PRIVATE)
        val activeUser = prefs.getString("active_user", "👤 ராஜ்குமார் (கணவர்)") ?: "👤 ராஜ்குமார் (கணவர்)"

        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        val currentTimestamp = sdf.format(Date())

        val parsed = SmsParser.parse(message)

        return if (parsed.isExpense && parsed.amount > 0) {
            val expArray = JSONArray().apply {
                put(JSONObject().apply {
                    put("date", currentTimestamp)
                    put("user", activeUser)
                    put("category", parsed.category)
                    put("amount", parsed.amount)
                    put("mode", "UPI / Mobile SMS")
                    put("merchant", parsed.merchant)
                    put("notes", message)
                })
            }
            postToSupabase("expenses", expArray.toString())
        } else {
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
