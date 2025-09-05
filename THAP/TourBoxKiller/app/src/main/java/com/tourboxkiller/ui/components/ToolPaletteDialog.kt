package com.tourboxkiller.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.tourboxkiller.data.ArtRemoteWebSocketClient

data class CSPTool(
    val id: String,
    val name: String,
    val icon: String,
    val shortcut: String? = null,
    val subTools: List<CSPSubTool> = emptyList()
)

data class CSPSubTool(
    val uuid: String,
    val name: String,
    val thumbnailPath: String? = null,
    val parentTool: String
)

@Composable
fun ToolPaletteDialog(
    isVisible: Boolean,
    tools: List<CSPTool>,
    onDismiss: () -> Unit,
    onToolSelected: (CSPTool, CSPSubTool?) -> Unit,
    webSocketClient: ArtRemoteWebSocketClient
) {
    val haptic = LocalHapticFeedback.current
    var selectedTool by remember { mutableStateOf<CSPTool?>(null) }
    
    if (isVisible) {
        Dialog(onDismissRequest = {
            // Always close dialog on outside tap or system back
            onDismiss()
        }) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(0.8f)
                    .padding(16.dp),
                shape = RoundedCornerShape(16.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp)
                ) {
                    // Header
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = if (selectedTool == null) "🛠️ CSP Tools" else "🎨 ${selectedTool!!.name}",
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold
                        )
                        
                        // No back button - just tap outside the dialog or use system back
                    }
                    
                    if (selectedTool == null) {
                        // Show main tools (Level 1)
                        Text(
                            text = "Select a tool category:",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(bottom = 16.dp)
                        )
                        
                        LazyColumn(
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            items(tools.chunked(2)) { toolPair ->
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    toolPair.forEach { tool ->
                                        ToolCard(
                                            tool = tool,
                                            modifier = Modifier.weight(1f),
                                            onClick = {
                                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                                // If no sub-tools, directly switch to main tool and close dialog
                                                if (tool.subTools.isEmpty()) {
                                                    onToolSelected(tool, null)
                                                    // Send main tool selection command
                                                    webSocketClient.sendAction("select_tool", mapOf(
                                                        "tool" to tool.id,
                                                        "tool_name" to tool.name
                                                    ))
                                                    onDismiss()
                                                } else {
                                                    // Show sub-tools if available
                                                    selectedTool = tool
                                                }
                                            }
                                        )
                                    }
                                    
                                    if (toolPair.size == 1) {
                                        Spacer(modifier = Modifier.weight(1f))
                                    }
                                }
                            }
                        }
                    } else {
                        // Show sub-tools (Level 2)
                        Text(
                            text = "${selectedTool!!.subTools.size} sub-tools available",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(bottom = 16.dp)
                        )
                        
                        LazyColumn(
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            items(selectedTool!!.subTools.chunked(2)) { subToolPair ->
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    subToolPair.forEach { subTool ->
                                        SubToolCard(
                                            subTool = subTool,
                                            modifier = Modifier.weight(1f),
                                            onClick = {
                                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                                onToolSelected(selectedTool!!, subTool)
                                                // Send sub-tool selection command
                                                webSocketClient.sendAction("select_subtool", mapOf(
                                                    "tool" to selectedTool!!.id,
                                                    "subtool_uuid" to subTool.uuid,
                                                    "subtool_name" to subTool.name
                                                ))
                                                onDismiss()
                                            }
                                        )
                                    }
                                    
                                    if (subToolPair.size == 1) {
                                        Spacer(modifier = Modifier.weight(1f))
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ToolCard(
    tool: CSPTool,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Card(
        modifier = modifier
            .height(100.dp)
            .clickable { onClick() },
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = tool.icon,
                fontSize = 32.sp
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = tool.name,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            
            if (tool.shortcut != null) {
                Text(
                    text = tool.shortcut,
                    style = MaterialTheme.typography.bodySmall,
                    fontSize = 10.sp,
                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                )
            }
        }
    }
}

@Composable
private fun SubToolCard(
    subTool: CSPSubTool,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Card(
        modifier = modifier
            .height(80.dp)
            .clickable { onClick() },
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(8.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Sub-tool icon based on name
            Box(
                modifier = Modifier
                    .size(32.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(MaterialTheme.colorScheme.primary),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = when {
                        subTool.name.contains("❓") -> "❓"
                        subTool.name.contains("✂️") -> "✂️"
                        subTool.name.contains("📋") -> "📋"
                        subTool.name.contains("📥") -> "📥"
                        subTool.name.contains("🔄") -> "🔄"
                        subTool.name.contains("➕") -> "➕"
                        subTool.name.contains("風") || subTool.name.contains("wind") -> "🌪️"
                        subTool.name.contains("水") || subTool.name.contains("water") -> "💧"
                        subTool.name.contains("煙") || subTool.name.contains("smoke") -> "💨"
                        subTool.name.contains("体液") -> "💦"
                        subTool.name.contains("ペン") || subTool.name.contains("pen") -> "🖊️"
                        subTool.name.contains("鉛筆") || subTool.name.contains("pencil") -> "✏️"
                        else -> "🖌️"
                    },
                    fontSize = 16.sp,
                    color = MaterialTheme.colorScheme.onPrimary
                )
            }
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = subTool.name,
                style = MaterialTheme.typography.bodySmall,
                fontSize = 9.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
