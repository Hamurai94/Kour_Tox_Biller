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

class ArtRemoteWebSocketClient {
    private val _connectionState = MutableStateFlow(ConnectionState())
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    private val _cspFavorites = MutableStateFlow<List<CSPFavorite>>(emptyList())
    val cspFavorites: StateFlow<List<CSPFavorite>> = _cspFavorites.asStateFlow()
    
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