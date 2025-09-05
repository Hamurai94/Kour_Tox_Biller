package com.tourboxkiller.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.tourboxkiller.data.ConnectionState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConnectionCard(
    connectionState: ConnectionState,
    onConnect: (String) -> Unit,
    onDisconnect: () -> Unit
) {
    var serverAddress by remember { mutableStateOf("192.168.2.6:8765") }
    
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "Server Connection",
                style = MaterialTheme.typography.headlineSmall
            )
            
            // Connection status indicator
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                val (statusText, statusColor) = when {
                    connectionState.isConnected -> "Connected" to MaterialTheme.colorScheme.primary
                    connectionState.lastError != null -> "Error" to MaterialTheme.colorScheme.error
                    else -> "Disconnected" to MaterialTheme.colorScheme.onSurfaceVariant
                }
                
                Card(
                    modifier = Modifier.size(12.dp),
                    colors = CardDefaults.cardColors(containerColor = statusColor)
                ) {}
                
                Text(
                    text = statusText,
                    style = MaterialTheme.typography.bodyMedium,
                    color = statusColor
                )
            }
            
            if (connectionState.lastError != null) {
                Text(
                    text = connectionState.lastError,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.error
                )
            }
            
            // Server address input
            OutlinedTextField(
                value = serverAddress,
                onValueChange = { serverAddress = it },
                label = { Text("Server Address (IP:Port)") },
                placeholder = { Text("192.168.2.6:8765") },
                modifier = Modifier.fillMaxWidth(),
                enabled = !connectionState.isConnected,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                singleLine = true
            )
            
            // Connect/Disconnect button
            Button(
                onClick = {
                    if (connectionState.isConnected) {
                        onDisconnect()
                    } else {
                        onConnect(serverAddress)
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (connectionState.isConnected) 
                        MaterialTheme.colorScheme.error 
                    else 
                        MaterialTheme.colorScheme.primary
                )
            ) {
                Text(
                    text = if (connectionState.isConnected) "Disconnect" else "Connect"
                )
            }
        }
    }
}