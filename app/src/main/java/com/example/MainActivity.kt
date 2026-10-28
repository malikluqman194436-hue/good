package com.example

import android.annotation.SuppressLint
import android.graphics.Bitmap
import android.graphics.Color
import android.os.Bundle
import android.util.Log
import android.view.View
import android.view.ViewGroup
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.viewinterop.AndroidView
import com.example.ui.theme.MyApplicationTheme

class MainActivity : ComponentActivity() {

  private var gameWebView: WebView? = null

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    enableEdgeToEdge()
    setContent {
      MyApplicationTheme {
        Scaffold(
          modifier = Modifier.fillMaxSize(),
          containerColor = androidx.compose.ui.graphics.Color(0xFF101113),
          contentWindowInsets = WindowInsets(0, 0, 0, 0)
        ) { _ ->
          SkyCarGameView(
            onWebViewReady = { webView ->
              gameWebView = webView
            },
            modifier = Modifier
              .fillMaxSize()
              .windowInsetsPadding(WindowInsets.safeDrawing)
          )
        }
      }
    }
  }

  override fun onResume() {
    super.onResume()
    gameWebView?.onResume()
  }

  override fun onPause() {
    super.onPause()
    gameWebView?.onPause()
  }

  override fun onDestroy() {
    gameWebView?.destroy()
    gameWebView = null
    super.onDestroy()
  }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun SkyCarGameView(
  onWebViewReady: (WebView) -> Unit,
  modifier: Modifier = Modifier
) {
  val context = LocalContext.current
  val webView = remember {
    WebView(context).apply {
      layoutParams = ViewGroup.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT,
        ViewGroup.LayoutParams.MATCH_PARENT
      )
      setBackgroundColor(Color.parseColor("#101113"))
      isVerticalScrollBarEnabled = false
      isHorizontalScrollBarEnabled = false
      overScrollMode = View.OVER_SCROLL_NEVER

      settings.apply {
        javaScriptEnabled = true
        domStorageEnabled = true
        databaseEnabled = true
        allowFileAccess = true
        allowContentAccess = true
        allowFileAccessFromFileURLs = true
        allowUniversalAccessFromFileURLs = true
        useWideViewPort = true
        loadWithOverviewMode = true
        cacheMode = WebSettings.LOAD_DEFAULT
        mediaPlaybackRequiresUserGesture = false
      }

      webChromeClient = object : WebChromeClient() {
        override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
          val level = consoleMessage?.messageLevel()
          val msg = consoleMessage?.message() ?: ""
          val source = consoleMessage?.sourceId() ?: ""
          val line = consoleMessage?.lineNumber() ?: 0
          Log.d("SkyCarJS", "[$level] $msg (line: $line, src: $source)")
          return true
        }
      }

      webViewClient = object : WebViewClient() {
        override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
          super.onPageStarted(view, url, favicon)
          Log.d("SkyCarWebView", "Started loading: $url")
        }

        override fun onPageFinished(view: WebView?, url: String?) {
          super.onPageFinished(view, url)
          Log.d("SkyCarWebView", "Page finished loading: $url")
        }

        override fun onReceivedError(
          view: WebView?,
          request: WebResourceRequest?,
          error: WebResourceError?
        ) {
          super.onReceivedError(view, request, error)
          Log.e(
            "SkyCarWebView",
            "Error loading url: ${request?.url}, code: ${error?.errorCode}, desc: ${error?.description}"
          )
        }
      }

      loadUrl("file:///android_asset/index.html")
    }
  }

  DisposableEffect(webView) {
    onWebViewReady(webView)
    onDispose {
      // WebView lifecycle is bounded by the activity
    }
  }

  Box(
    modifier = modifier
      .fillMaxSize()
      .background(androidx.compose.ui.graphics.Color(0xFF101113))
  ) {
    AndroidView(
      factory = { webView },
      modifier = Modifier
        .fillMaxSize()
        .testTag("sky_car_canvas_view")
    )
  }
}
