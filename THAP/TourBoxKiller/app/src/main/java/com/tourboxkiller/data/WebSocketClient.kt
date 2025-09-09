package com.tourboxkiller.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

data class ConnectionState(
    val isConnected: Boolean = false,
    val serverAddress: String = "",
    val lastError: String? = null
)

data class CSPFavorite(
    val key: String,
    val assigned: Boolean,
    val icon: String,
    val description: String,
    val command: String?
)

data class DetectedApp(
    val app: String?,
    val displayName: String,
    val hasFavorites: Boolean,
    val supportedTools: List<String>
)

data class KritaBrush(
    val name: String,
    val displayName: String,
    val category: String,
    val icon: String,
    val filePath: String
)

class ArtRemoteWebSocketClient {
    private val _connectionState = MutableStateFlow(ConnectionState())
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    private val _cspFavorites = MutableStateFlow<List<CSPFavorite>>(emptyList())
    val cspFavorites: StateFlow<List<CSPFavorite>> = _cspFavorites.asStateFlow()
    
    private val _detectedApp = MutableStateFlow<DetectedApp?>(null)
    val detectedApp: StateFlow<DetectedApp?> = _detectedApp.asStateFlow()
    
    private val _kritaBrushes = MutableStateFlow<List<KritaBrush>>(emptyList())
    val kritaBrushes: StateFlow<List<KritaBrush>> = _kritaBrushes.asStateFlow()
    
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .build()
    
    fun connect(serverAddress: String) {
        val request = Request.Builder()
            .url("ws://$serverAddress")
            .build()
        
        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                _connectionState.value = ConnectionState(
                    isConnected = true,
                    serverAddress = serverAddress,
                    lastError = null
                )
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _connectionState.value = ConnectionState(
                    isConnected = false,
                    serverAddress = serverAddress,
                    lastError = t.message
                )
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                android.util.Log.d("WebSocket", "📨 Received message: $text")
                try {
                    val response = JSONObject(text)
                    val action = response.optString("action")
                    android.util.Log.d("WebSocket", "🎯 Message action: $action")
                    
                    if (action == "favorites_data") {
                        // Parse favorites data from server
                        val favoritesJson = response.optJSONObject("favorites")
                        val favoritesList = mutableListOf<CSPFavorite>()
                        
                        if (favoritesJson != null) {
                            for (i in 1..12) {
                                val fKey = "F$i"
                                val favData = favoritesJson.optJSONObject(fKey)
                                
                                if (favData != null) {
                                    favoritesList.add(CSPFavorite(
                                        key = fKey,
                                        assigned = favData.optBoolean("assigned", false),
                                        icon = favData.optString("icon", "🔧"),
                                        description = favData.optString("description", "Unknown"),
                                        command = favData.optString("command", null)
                                    ))
                                }
                            }
                        }
                        
                        // Update state
                        _cspFavorites.value = favoritesList
                        android.util.Log.d("CSP_Favorites", "Updated ${favoritesList.size} favorites")
                    } else if (action == "app_detected") {
                        // Handle detected app info for UI adaptation
                        val appName = response.optString("app", null)
                        val appDisplayName = response.optString("app_name", "Unknown")
                        val hasFavorites = response.optBoolean("has_favorites", false)
                        val supportedToolsArray = response.optJSONArray("supported_tools")
                        
                        val supportedTools = mutableListOf<String>()
                        if (supportedToolsArray != null) {
                            for (i in 0 until supportedToolsArray.length()) {
                                supportedTools.add(supportedToolsArray.getString(i))
                            }
                        }
                        
                        _detectedApp.value = DetectedApp(
                            app = appName,
                            displayName = appDisplayName,
                            hasFavorites = hasFavorites,
                            supportedTools = supportedTools
                        )
                        
                        // Handle Krita brush data - COMPLETE DATABASE INTEGRATION
                        if (appName == "krita") {
                            val kritaBrushesJson = response.optJSONObject("krita_brushes")
                            if (kritaBrushesJson != null) {
                                val kritaBrushesList = mutableListOf<KritaBrush>()
                                
                                // Parse categories (all 276 brushes organized!)
                                val categoriesJson = kritaBrushesJson.optJSONObject("categories")
                                if (categoriesJson != null) {
                                    val categoryNames = categoriesJson.names()
                                    if (categoryNames != null) {
                                        for (i in 0 until categoryNames.length()) {
                                            val categoryName = categoryNames.getString(i)
                                            val brushesArray = categoriesJson.optJSONArray(categoryName)
                                            
                                            if (brushesArray != null) {
                                                for (j in 0 until brushesArray.length()) {
                                                    val brushJson = brushesArray.getJSONObject(j)
                                                    kritaBrushesList.add(KritaBrush(
                                                        name = brushJson.optString("name", "Unknown"),
                                                        displayName = brushJson.optString("display_name", brushJson.optString("name", "Unknown")),
                                                        category = categoryName,
                                                        icon = brushJson.optString("icon", "🖌️"),
                                                        filePath = brushJson.optString("filename", "")
                                                    ))
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Fallback: Parse quick_access if categories failed
                                if (kritaBrushesList.isEmpty()) {
                                    val quickAccessArray = kritaBrushesJson.optJSONArray("quick_access")
                                    if (quickAccessArray != null) {
                                        for (i in 0 until quickAccessArray.length()) {
                                            val brushJson = quickAccessArray.getJSONObject(i)
                                            kritaBrushesList.add(KritaBrush(
                                                name = brushJson.optString("name", "Unknown"),
                                                displayName = brushJson.optString("display_name", brushJson.optString("name", "Unknown")),
                                                category = brushJson.optString("category", "Other"),
                                                icon = brushJson.optString("icon", "🖌️"),
                                                filePath = brushJson.optString("file_path", "")
                                            ))
                                        }
                                    }
                                }
                                
                                _kritaBrushes.value = kritaBrushesList
                                android.util.Log.d("Krita_Brushes", "🔥 BREAKTHROUGH: Loaded ${kritaBrushesList.size} Krita brushes from database!")
                                
                                // Log categories
                                val categories = kritaBrushesList.groupBy { it.category }
                                for ((category, brushes) in categories) {
                                    android.util.Log.d("Krita_Categories", "📁 $category: ${brushes.size} brushes")
                                }
                            }
                        }
                        
                        android.util.Log.d("App_Detection", "Detected app: $appDisplayName (${supportedTools.size} tools)")
                    }
                } catch (e: Exception) {
                    android.util.Log.e("WebSocket", "Error parsing message: $text", e)
                }
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                _connectionState.value = ConnectionState(
                    isConnected = false,
                    serverAddress = serverAddress,
                    lastError = "Connection closed: $reason"
                )
            }
        }
        
        webSocket = client.newWebSocket(request, listener)
    }
    
    fun disconnect() {
        webSocket?.close(1000, "User disconnected")
        webSocket = null
        _connectionState.value = ConnectionState()
    }
    
    fun sendAction(action: String, params: Map<String, Any> = emptyMap()) {
        val message = JSONObject().apply {
            put("action", action)
            if (params.isNotEmpty()) {
                put("value", params)
            }
        }
        
        webSocket?.send(message.toString())
    }
    
    // Quick action methods for common operations
    fun zoomIn() = sendAction("zoom", mapOf("direction" to "in", "amount" to 1.5))
    fun zoomOut() = sendAction("zoom", mapOf("direction" to "out", "amount" to 1.5))
    fun undo() = sendAction("undo")
    fun redo() = sendAction("redo")
    fun rotate(degrees: Float) = sendAction("rotate", mapOf("degrees" to degrees))
    fun switchTool(tool: String) = sendAction("tool", mapOf("name" to tool))
    fun adjustBrushSize(delta: Int) = sendAction("brush_size", mapOf("delta" to delta))
    fun newLayer() = sendAction("layer", mapOf("action" to "new"))
    fun deleteLayer() = sendAction("layer", mapOf("action" to "delete"))
    fun requestFavorites() {
        android.util.Log.d("WebSocket", "🔥 Requesting CSP favorites from server...")
        sendAction("get_favorites", emptyMap())
    }
}