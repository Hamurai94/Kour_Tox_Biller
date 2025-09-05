package com.tourboxkiller.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tourboxkiller.data.ArtRemoteWebSocketClient
import com.tourboxkiller.ui.components.ConnectionCard
import com.tourboxkiller.ui.components.TourBoxControlLayout

@Composable
fun RemoteControlScreen() {
    val webSocketClient = remember { ArtRemoteWebSocketClient() }
    val connectionState by webSocketClient.connectionState.collectAsState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(bottom = 16.dp)
    ) {
        // App Title
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer
            )
        ) {
            Text(
                text = "🎨 TourBox Killer",
                style = MaterialTheme.typography.headlineLarge,
                modifier = Modifier.padding(16.dp),
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
        }
        
        // Connection Card
        ConnectionCard(
            connectionState = connectionState,
            onConnect = { address -> webSocketClient.connect(address) },
            onDisconnect = { webSocketClient.disconnect() }
        )
        
        // Main Control Layout
        TourBoxControlLayout(
            webSocketClient = webSocketClient,
            isConnected = connectionState.isConnected
        )
        
        // Status Footer
        if (connectionState.isConnected) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Text(
                    text = "✅ Connected to ${connectionState.serverAddress}\nReady to control your art software!",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(16.dp),
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}