package com.tourboxkiller.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFFD4AF37),        // Art Deco Gold
    secondary = Color(0xFF2C3E50),      // Deep Blue-Gray
    tertiary = Color(0xFF34495E),       // Lighter Blue-Gray
    background = Color(0xFF1A1A1A),     // Rich Dark
    surface = Color(0xFF2C3E50),        // Deep Blue-Gray
    surfaceVariant = Color(0xFF34495E), // Lighter surface
    onPrimary = Color(0xFF1A1A1A),      // Dark on gold
    onSecondary = Color(0xFFFFFFFF),    // White on blue
    onBackground = Color(0xFFE8E8E8),   // Light gray text
    onSurface = Color(0xFFE8E8E8),      // Light gray text
    error = Color(0xFFE74C3C)           // Art Deco Red
)

private val LightColorScheme = lightColorScheme(
    primary = Color(0xFF1DB954),
    secondary = Color(0xFFE0E0E0),
    tertiary = Color(0xFFF5F5F5),
    background = Color(0xFFFFFFFF),
    surface = Color(0xFFF5F5F5),
    onBackground = Color(0xFF000000),
    onSurface = Color(0xFF000000)
)

@Composable
fun TourBoxKillerTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) {
        DarkColorScheme
    } else {
        LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}