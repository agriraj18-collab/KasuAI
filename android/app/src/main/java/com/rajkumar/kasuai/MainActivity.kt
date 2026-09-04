package com.rajkumar.kasuai

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import android.widget.RadioGroup
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
        val serverUrl = prefs.getString("server_url", "http://10.0.2.2:8501") ?: "http://10.0.2.2:8501"
        webView.loadUrl(serverUrl)
    }

    private fun showProfileSettingsDialog() {
        val prefs = getSharedPreferences("kasuai_prefs", Context.MODE_PRIVATE)
        val currentUrl = prefs.getString("server_url", "http://10.0.2.2:8501") ?: "http://10.0.2.2:8501"
        val currentUser = prefs.getString("active_user", "👤 ராஜ்குமார் (கணவர்)") ?: "👤 ராஜ்குமார் (கணவர்)"

        val dialogView = layoutInflater.inflate(R.layout.dialog_settings, null)
        val inputUrl = dialogView.findViewById<EditText>(R.id.editServerUrl)
        val radioGroup = dialogView.findViewById<RadioGroup>(R.id.radioGroupUser)

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
