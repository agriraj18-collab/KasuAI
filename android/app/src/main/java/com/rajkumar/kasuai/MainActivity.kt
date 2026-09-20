package com.rajkumar.kasuai

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.RadioGroup
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.floatingactionbutton.FloatingActionButton

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var fabSettings: FloatingActionButton

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val smsGranted = permissions[Manifest.permission.RECEIVE_SMS] == true
        if (smsGranted) {
            Toast.makeText(this, "✅ KasuAI SMS அனுமதி வழங்கப்பட்டது!", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(this, "⚠️ தானியங்கி SMS பதிவிற்கு அனுமதி தேவை.", Toast.LENGTH_LONG).show()
        }
        checkNotificationListenerPermission()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        fabSettings = findViewById(R.id.fabSettings)

        checkAndRequestPermissions()
        setupWebView()

        swipeRefresh.setOnRefreshListener {
            webView.reload()
        }

        fabSettings.setOnClickListener {
            showProfileSettingsDialog()
        }

        loadDashboard()
    }

    override fun onResume() {
        super.onResume()
        // Refresh check when returning from system settings
    }

    private fun isNotificationListenerEnabled(): Boolean {
        val pkgName = packageName
        val flat = Settings.Secure.getString(contentResolver, "enabled_notification_listeners")
        return flat != null && flat.contains(pkgName)
    }

    private fun checkNotificationListenerPermission() {
        if (!isNotificationListenerEnabled()) {
            AlertDialog.Builder(this)
                .setTitle("🔔 Paytm & UPI தானியங்கி கண்காணிப்பு")
                .setMessage("Paytm, Google Pay, PhonePe ஆகியவற்றில் செலுத்தப்படும் செலவுகளுக்கு SMS வராவிட்டாலும், KasuAI தானாகக் கணக்கில் சேர்க்க Notification Access அனுமதி தேவை.\n\nஇப்போது இயக்கவா?")
                .setPositiveButton("இயக்கு (Enable)") { _, _ ->
                    startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
                }
                .setNegativeButton("பிறகு", null)
                .show()
        }
    }

    private fun checkAndRequestPermissions() {
        val permissionsToRequest = mutableListOf(
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_SMS
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val needed = permissionsToRequest.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (needed.isNotEmpty()) {
            permissionLauncher.launch(needed.toTypedArray())
        } else {
            checkNotificationListenerPermission()
        }
    }

    private fun setupWebView() {
        val settings: WebSettings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.loadWithOverviewMode = true
        settings.useWideViewPort = true
        settings.builtInZoomControls = false
        settings.displayZoomControls = false

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                swipeRefresh.isRefreshing = false
            }
        }
    }

    private fun loadDashboard() {
        val prefs = getSharedPreferences("kasuai_prefs", Context.MODE_PRIVATE)
        val serverUrl = prefs.getString("server_url", "https://kasuai-app.streamlit.app") ?: "https://kasuai-app.streamlit.app"
        webView.loadUrl(serverUrl)
    }

    private fun showProfileSettingsDialog() {
        val prefs = getSharedPreferences("kasuai_prefs", Context.MODE_PRIVATE)
        val currentUrl = prefs.getString("server_url", "https://kasuai-app.streamlit.app") ?: "https://kasuai-app.streamlit.app"
        val currentUser = prefs.getString("active_user", "👤 ராஜ்குமார் (கணவர்)") ?: "👤 ராஜ்குமார் (கணவர்)"

        val dialogView = layoutInflater.inflate(R.layout.dialog_settings, null)
        val inputUrl = dialogView.findViewById<EditText>(R.id.editServerUrl)
        val radioGroup = dialogView.findViewById<RadioGroup>(R.id.radioGroupUser)
        val textNotifyStatus = dialogView.findViewById<TextView>(R.id.textNotificationStatus)
        val btnNotification = dialogView.findViewById<Button>(R.id.btnNotificationAccess)

        val isListenerActive = isNotificationListenerEnabled()
        if (isListenerActive) {
            textNotifyStatus.text = "🟢 செயலில் உள்ளது (Active) — Paytm & UPI செலவுகள் தானாகப் பதியப்படும்"
            textNotifyStatus.setTextColor(ContextCompat.getColor(this, android.R.color.holo_green_dark))
        } else {
            textNotifyStatus.text = "🔴 அனுமதிக்கப்படவில்லை (Disabled) — Paytm செலவுகளை எடுக்க அனுமதியை இயக்கவும்"
            textNotifyStatus.setTextColor(ContextCompat.getColor(this, android.R.color.holo_red_dark))
        }

        btnNotification.setOnClickListener {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }

        inputUrl.setText(currentUrl)
        if (currentUser.contains("மனைவி")) {
            radioGroup.check(R.id.radioWife)
        } else {
            radioGroup.check(R.id.radioHusband)
        }

        AlertDialog.Builder(this)
            .setTitle("⚙️ KasuAI ஆப் அமைப்புகள்")
            .setView(dialogView)
            .setPositiveButton("சேமி") { _, _ ->
                val newUrl = inputUrl.text.toString().trim()
                val selectedUser = if (radioGroup.checkedRadioButtonId == R.id.radioWife) {
                    "👩 மனைவி (வீட்டுச் செலவு)"
                } else {
                    "👤 ராஜ்குமார் (கணவர்)"
                }

                prefs.edit()
                    .putString("server_url", newUrl)
                    .putString("active_user", selectedUser)
                    .apply()

                Toast.makeText(this, "அமைப்புகள் சேமிக்கப்பட்டன!", Toast.LENGTH_SHORT).show()
                loadDashboard()
            }
            .setNegativeButton("ரத்து", null)
            .show()
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
