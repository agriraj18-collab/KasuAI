package com.rajkumar.kasuai

import android.content.Context
import android.util.Log
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.TimeUnit

object NetworkClient {
    private const val TAG = "KasuAI_Net"
    private val JSON_MEDIA_TYPE = "application/json; charset=utf-8".toMediaType()

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    fun sendSmsToServer(context: Context, sender: String, message: String): Boolean {
        val prefs = context.getSharedPreferences("kasuai_prefs", Context.MODE_PRIVATE)
        val serverUrl = prefs.getString("server_url", "http://10.0.2.2:8080") ?: "http://10.0.2.2:8080"
        val activeUser = prefs.getString("active_user", "👤 ராஜ்குமார் (கணவர்)") ?: "👤 ராஜ்குமார் (கணவர்)"
        val apiUrl = if (serverUrl.endsWith("/")) "${serverUrl}api/sms" else "$serverUrl/api/sms"

        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        val currentTimestamp = sdf.format(Date())

        val payload = JSONObject().apply {
            put("sender", sender)
            put("message", message)
            put("user", activeUser)
            put("timestamp", currentTimestamp)
        }

        val requestBody = payload.toString().toRequestBody(JSON_MEDIA_TYPE)
        val request = Request.Builder()
            .url(apiUrl)
            .post(requestBody)
            .build()

        return try {
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""
            Log.d(TAG, "Sync Response: ${response.code} -> $responseBody")
            response.isSuccessful
        } catch (e: Exception) {
            Log.e(TAG, "Error syncing SMS to server: ${e.message}")
            false
        }
    }
}
