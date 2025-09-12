// Android Authentication Integration for Art Remote Control
// Add this to your Android app's WebSocket client

import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import android.content.Context
import android.content.SharedPreferences

/**
 * Authentication manager for Art Remote Control
 * Handles token/PIN authentication with the server
 */
class ArtRemoteAuth(private val context: Context) {
    private val prefs: SharedPreferences = context.getSharedPreferences("art_remote_auth", Context.MODE_PRIVATE)
    
    companion object {
        private const val KEY_TOKEN = "auth_token"
        private const val KEY_PIN = "auth_pin"
        private const val KEY_HOST = "server_host"
        private const val KEY_PORT = "server_port"
    }
    
    /**
     * Store authentication credentials
     */
    fun storeCredentials(token: String? = null, pin: String? = null, host: String? = null, port: Int? = null) {
        prefs.edit().apply {
            token?.let { putString(KEY_TOKEN, it) }
            pin?.let { putString(KEY_PIN, it) }
            host?.let { putString(KEY_HOST, it) }
            port?.let { putInt(KEY_PORT, it) }
            apply()
        }
    }
    
    /**
     * Get stored authentication token
     */
    fun getToken(): String? = prefs.getString(KEY_TOKEN, null)
    
    /**
     * Get stored PIN
     */
    fun getPin(): String? = prefs.getString(KEY_PIN, null)
    
    /**
     * Get stored server host
     */
    fun getHost(): String = prefs.getString(KEY_HOST, "192.168.1.100") ?: "192.168.1.100"
    
    /**
     * Get stored server port
     */
    fun getPort(): Int = prefs.getInt(KEY_PORT, 8765)
    
    /**
     * Check if we have any stored credentials
     */
    fun hasCredentials(): Boolean = getToken() != null || getPin() != null
    
    /**
     * Clear all stored credentials
     */
    fun clearCredentials() {
        prefs.edit().clear().apply()
    }
    
    /**
     * Create authentication message for server
     */
    fun createAuthMessage(clientInfo: Map<String, String> = emptyMap()): String {
        val authData = buildJsonObject {
            put("type", "authenticate")
            
            // Try token first (preferred)
            getToken()?.let { token ->
                put("token", token)
            } ?: run {
                // Fallback to PIN
                getPin()?.let { pin ->
                    put("pin", pin)
                }
            }
            
            // Add client info
            put("client_info", buildJsonObject {
                put("platform", "Android")
                put("app_version", "1.0")
                clientInfo.forEach { (key, value) ->
                    put(key, value)
                }
            })
        }
        
        return authData.toString()
    }
    
    /**
     * Parse QR code data for automatic setup
     * Format: artremote://connect?token=TOKEN&host=HOST&port=PORT
     */
    fun parseQRCode(qrData: String): Boolean {
        return try {
            if (!qrData.startsWith("artremote://connect")) return false
            
            val uri = android.net.Uri.parse(qrData)
            val token = uri.getQueryParameter("token")
            val host = uri.getQueryParameter("host")
            val port = uri.getQueryParameter("port")?.toIntOrNull()
            
            if (token != null) {
                storeCredentials(
                    token = token,
                    host = host,
                    port = port
                )
                true
            } else {
                false
            }
        } catch (e: Exception) {
            false
        }
    }
}

/**
 * Enhanced WebSocket client with authentication support
 * Integrate this with your existing WebSocket client
 */
class AuthenticatedWebSocketClient(
    private val context: Context,
    private val onConnected: () -> Unit,
    private val onMessage: (String) -> Unit,
    private val onError: (String) -> Unit
) {
    private val auth = ArtRemoteAuth(context)
    private var webSocket: okhttp3.WebSocket? = null
    private val client = okhttp3.OkHttpClient()
    
    /**
     * Connect with authentication
     */
    fun connect() {
        val host = auth.getHost()
        val port = auth.getPort()
        val url = "ws://$host:$port"
        
        val request = okhttp3.Request.Builder()
            .url(url)
            .build()
        
        webSocket = client.newWebSocket(request, object : okhttp3.WebSocketListener() {
            override fun onOpen(webSocket: okhttp3.WebSocket, response: okhttp3.Response) {
                // Wait for auth challenge from server
                // Don't call onConnected yet - wait for successful auth
            }
            
            override fun onMessage(webSocket: okhttp3.WebSocket, text: String) {
                try {
                    val message = Json.parseToJsonElement(text).jsonObject
                    val type = message["type"]?.jsonPrimitive?.content
                    
                    when (type) {
                        "auth_required" -> {
                            // Server requires authentication
                            if (auth.hasCredentials()) {
                                val authMessage = auth.createAuthMessage()
                                webSocket.send(authMessage)
                            } else {
                                onError("Authentication required but no credentials stored")
                            }
                        }
                        
                        "auth_response" -> {
                            val success = message["success"]?.jsonPrimitive?.boolean ?: false
                            if (success) {
                                onConnected()
                            } else {
                                val errorMsg = message["message"]?.jsonPrimitive?.content ?: "Authentication failed"
                                onError(errorMsg)
                            }
                        }
                        
                        else -> {
                            // Regular message - pass to handler
                            onMessage(text)
                        }
                    }
                } catch (e: Exception) {
                    // If not JSON, treat as regular message
                    onMessage(text)
                }
            }
            
            override fun onFailure(webSocket: okhttp3.WebSocket, t: Throwable, response: okhttp3.Response?) {
                onError("Connection failed: ${t.message}")
            }
        })
    }
    
    /**
     * Send command to server
     */
    fun sendCommand(action: String, value: Any? = null) {
        val command = buildJsonObject {
            put("action", action)
            value?.let { put("value", JsonPrimitive(it.toString())) }
        }
        webSocket?.send(command.toString())
    }
    
    /**
     * Disconnect
     */
    fun disconnect() {
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
    }
}

/**
 * Simple setup dialog for PIN entry
 * Add this to your Android app's UI
 */
@Composable
fun AuthSetupDialog(
    onDismiss: () -> Unit,
    onSuccess: () -> Unit,
    auth: ArtRemoteAuth
) {
    var pin by remember { mutableStateOf("") }
    var host by remember { mutableStateOf(auth.getHost()) }
    var port by remember { mutableStateOf(auth.getPort().toString()) }
    var isConnecting by remember { mutableStateOf(false) }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Connect to Art Remote Server") },
        text = {
            Column {
                Text("Enter the PIN shown on your computer:")
                
                OutlinedTextField(
                    value = pin,
                    onValueChange = { pin = it },
                    label = { Text("PIN") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                OutlinedTextField(
                    value = host,
                    onValueChange = { host = it },
                    label = { Text("Server IP") },
                    modifier = Modifier.fillMaxWidth()
                )
                
                OutlinedTextField(
                    value = port,
                    onValueChange = { port = it },
                    label = { Text("Port") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    isConnecting = true
                    auth.storeCredentials(
                        pin = pin,
                        host = host,
                        port = port.toIntOrNull() ?: 8765
                    )
                    onSuccess()
                },
                enabled = pin.isNotBlank() && !isConnecting
            ) {
                if (isConnecting) {
                    CircularProgressIndicator(modifier = Modifier.size(16.dp))
                } else {
                    Text("Connect")
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
