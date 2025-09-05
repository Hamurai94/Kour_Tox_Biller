package com.tourboxkiller.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tourboxkiller.data.ArtRemoteWebSocketClient
import kotlin.math.*
import androidx.compose.material3.Slider
import kotlin.math.round

@Composable
fun TourBoxControlLayout(
    webSocketClient: ArtRemoteWebSocketClient,
    isConnected: Boolean,
    modifier: Modifier = Modifier
) {
    val haptic = LocalHapticFeedback.current
    var showToolPalette by remember { mutableStateOf(false) }
    val cspFavorites by webSocketClient.cspFavorites.collectAsState()
    
    // Convert CSPFavorite to CSPSubTool for UI
    val dynamicFavorites = cspFavorites.map { favorite ->
        CSPSubTool(
            uuid = favorite.key,
            name = "${favorite.icon} ${favorite.description}",
            parentTool = "favorites"
        )
    }
    
    // CSP Tool structure matching your actual CSP interface
    val cspTools = listOf(
        CSPTool(
            id = "pen_group",
            name = "Pen/Pencil",
            icon = "🖊️",
            shortcut = "P",
            subTools = emptyList() // CSP cycles between Pen and Pencil with P key
        ),
        CSPTool(
            id = "brush_group",
            name = "Brush/Airbrush", 
            icon = "🖌️",
            shortcut = "B",
            subTools = emptyList() // CSP cycles between Brush, Airbrush, Decoration with B key
        ),
        CSPTool(
            id = "blend_group",
            name = "Blend/Liquify",
            icon = "🌀",
            shortcut = "J",
            subTools = emptyList() // CSP cycles between Blend and Distort with J key
        ),
        CSPTool(
            id = "eraser",
            name = "Eraser",
            icon = "🧽",
            shortcut = "E",
            subTools = emptyList()
        ),
        CSPTool(
            id = "selection",
            name = "Selection",
            icon = "⬚",
            shortcut = "M",
            subTools = emptyList()
        ),
        CSPTool(
            id = "fill",
            name = "Fill/Gradient",
            icon = "🪣",
            shortcut = "G",
            subTools = emptyList() // CSP cycles between Fill and Gradient with G key
        ),
        CSPTool(
            id = "eyedropper",
            name = "Eyedropper",
            icon = "💉",
            shortcut = "I",
            subTools = emptyList()
        ),
        CSPTool(
            id = "favorites",
            name = "⭐ CSP Favorites",
            icon = "⭐",
            shortcut = "F1-F12",
            subTools = dynamicFavorites.ifEmpty {
                // Default loading state
                (1..12).map { i ->
                    CSPSubTool("F$i", "Loading F$i...", parentTool = "favorites")
                }
            }
        )
    )
    
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = "🎮 TourBox Controls",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold
            )
            
            if (!isConnected) {
                Text(
                    text = "Connect to server to enable controls",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
            }
            
            // Zoom and Rotate Sliders
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Zoom Slider
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("🔍 Zoom", style = MaterialTheme.typography.bodySmall)
                    
                    Button(
                        onClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                            webSocketClient.sendAction("scroll", mapOf("direction" to "up"))
                        },
                        enabled = isConnected,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 8.dp),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Text("🔍+", fontSize = 14.sp)
                    }
                    
                    Button(
                        onClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                            webSocketClient.sendAction("scroll", mapOf("direction" to "down"))
                        },
                        enabled = isConnected,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 8.dp),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Text("🔍-", fontSize = 14.sp)
                    }
                }
                
                // Center Undo Button
                Button(
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        webSocketClient.undo()
                    },
                    enabled = isConnected,
                    modifier = Modifier.size(80.dp),
                    shape = CircleShape,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Text("↶\nUNDO", fontSize = 10.sp, textAlign = TextAlign.Center)
                }
                
                // Rotation Buttons (CSP: - and ^ keys)
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("🔄 Rotate", style = MaterialTheme.typography.bodySmall)
                    
                    Button(
                        onClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                            webSocketClient.sendAction("rotate_left", emptyMap())
                        },
                        enabled = isConnected,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 8.dp),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Text("↺ Left", fontSize = 12.sp)
                    }
                    
                    Spacer(modifier = Modifier.height(4.dp))
                    
                    Button(
                        onClick = {
                            haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                            webSocketClient.sendAction("rotate_right", emptyMap())
                        },
                        enabled = isConnected,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 8.dp),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Text("↻ Right", fontSize = 12.sp)
                    }
                }
            }
            
            // Tool selection buttons
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                ),
                elevation = CardDefaults.cardElevation(defaultElevation = 6.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "🎨 Tools",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally)
                    ) {
                        ToolButton(
                            text = "🎨\nBRUSHES",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                showToolPalette = true
                                // Don't request favorites - go to main tools
                            },
                            modifier = Modifier.weight(1f)
                        )
                        
                        ToolButton(
                            text = "🧹\nERASER",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                webSocketClient.switchTool("eraser")
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally)
                    ) {
                        ToolButton(
                            text = "📐\nSELECT",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                webSocketClient.switchTool("select")
                            },
                            modifier = Modifier.weight(1f)
                        )
                        
                        ToolButton(
                            text = "✋\nPAN",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                webSocketClient.switchTool("pan")
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally)
                    ) {
                        ToolButton(
                            text = "🖌️+\nSIZE+",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                webSocketClient.adjustBrushSize(5)
                            },
                            modifier = Modifier.weight(1f)
                        )
                        
                        ToolButton(
                            text = "🖌️-\nSIZE-",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                webSocketClient.adjustBrushSize(-5)
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }
            
            // Layer controls
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Column(
                    modifier = Modifier.padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "📚 Layers",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally)
                    ) {
                        ToolButton(
                            text = "➕\nNEW",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                webSocketClient.sendAction("layer_new", emptyMap())
                            },
                            modifier = Modifier.weight(1f)
                        )
                        
                        ToolButton(
                            text = "📁\nFOLDER",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                webSocketClient.sendAction("layer_folder", emptyMap())
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally)
                    ) {
                        ToolButton(
                            text = "🔗\nMERGE",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                webSocketClient.sendAction("layer_merge", emptyMap())
                            },
                            modifier = Modifier.weight(1f)
                        )
                        
                        ToolButton(
                            text = "🗑️\nDELETE",
                            enabled = isConnected,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                webSocketClient.sendAction("layer_delete", emptyMap())
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }
            
            // Navigation D-Pad
            DPadControl(
                enabled = isConnected,
                webSocketClient = webSocketClient,
                haptic = haptic
            )
        }
    }
    
    // Tool Palette Dialog
    ToolPaletteDialog(
        isVisible = showToolPalette,
        tools = cspTools,
        onDismiss = { showToolPalette = false },
        onToolSelected = { tool, subTool ->
            // Handle tool/sub-tool selection
            haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
        },
        webSocketClient = webSocketClient
    )
}

@Composable
private fun ToolButton(
    text: String,
    enabled: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onClick,
        enabled = enabled,
                                modifier = modifier
            .width(100.dp)
            .height(80.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Text(
            text = text,
            fontSize = 11.sp,
            textAlign = TextAlign.Center,
            lineHeight = 12.sp
        )
    }
}

@Composable
private fun DialControl(
    label: String,
    enabled: Boolean,
    onRotate: (Float) -> Unit,
    modifier: Modifier = Modifier
) {
    var rotation by remember { mutableStateOf(0f) }
    var isDragging by remember { mutableStateOf(false) }
    
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
        modifier = modifier
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            textAlign = TextAlign.Center,
            fontWeight = FontWeight.Medium
        )
        
        Box(
            modifier = Modifier
                .size(90.dp)
                .clip(CircleShape)
                .background(
                    if (enabled) MaterialTheme.colorScheme.primaryContainer
                    else MaterialTheme.colorScheme.surfaceVariant
                )
                .border(
                    3.dp,
                    if (isDragging) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.outline,
                    CircleShape
                )
                .pointerInput(enabled) {
                    if (enabled) {
                        detectDragGestures(
                            onDragStart = {
                                isDragging = true
                            },
                            onDragEnd = {
                                isDragging = false
                                rotation = 0f
                            }
                        ) { _, dragAmount ->
                            val deltaAngle = (dragAmount.x + dragAmount.y) * 0.3f
                            rotation += deltaAngle
                            onRotate(deltaAngle)
                        }
                    }
                },
            contentAlignment = Alignment.Center
        ) {
            // Dial indicator
            Box(
                modifier = Modifier
                    .size(12.dp)
                    .offset(y = (-30).dp)
                    .clip(CircleShape)
                    .background(
                        if (enabled) MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurfaceVariant
                    )
            )
            
            // Center dot
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.onPrimaryContainer)
            )
        }
    }
}

@Composable
private fun DPadControl(
    enabled: Boolean,
    webSocketClient: ArtRemoteWebSocketClient,
    haptic: androidx.compose.ui.hapticfeedback.HapticFeedback,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(12.dp)
        ) {
            Text(
                text = "📚 Layer Navigation",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                // Up button - Layer Above
                Button(
                    onClick = { 
                        haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                        webSocketClient.sendAction("layer_up", emptyMap())
                    },
                    enabled = enabled,
                    modifier = Modifier.size(60.dp, 45.dp),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("⬆️\nLayer", fontSize = 10.sp, textAlign = TextAlign.Center)
                }
                
                // Center button - Go to Layer 1
                Button(
                    onClick = { 
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        webSocketClient.sendAction("layer_goto_first", emptyMap())
                    },
                    enabled = enabled,
                    modifier = Modifier.size(60.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.secondary
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("🏠\nLayer 1", fontSize = 10.sp, textAlign = TextAlign.Center)
                }
                
                // Down button - Layer Below
                Button(
                    onClick = { 
                        haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                        webSocketClient.sendAction("layer_down", emptyMap())
                    },
                    enabled = enabled,
                    modifier = Modifier.size(60.dp, 45.dp),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("⬇️\nLayer", fontSize = 10.sp, textAlign = TextAlign.Center)
                }
            }
        }
    }
}