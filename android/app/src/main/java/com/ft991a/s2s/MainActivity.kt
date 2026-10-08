package com.ft991a.s2s

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import com.ft991a.s2s.ui.screens.*
import com.ft991a.s2s.ui.theme.CyanGlow
import com.ft991a.s2s.ui.theme.FT991ATheme
import com.ft991a.s2s.ui.theme.SurfaceDark
import com.ft991a.s2s.viewmodel.RadioViewModel

enum class NavigationTab(val label: String, val icon: ImageVector) {
    DASHBOARD("Radio", Icons.Default.Radio),
    PROVIDERS("AI", Icons.Default.Psychology),
    SKILLS("Skills", Icons.Default.Build),
    PROMPT("Prompt", Icons.Default.Edit),
    HARDWARE("Device", Icons.Default.Settings)
}

class MainActivity : ComponentActivity() {

    private val viewModel: RadioViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Connect WebSocket
        viewModel.connect()

        setContent {
            FT991ATheme {
                var selectedTab by remember { mutableStateOf(NavigationTab.DASHBOARD) }

                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    bottomBar = {
                        NavigationBar(containerColor = SurfaceDark) {
                            NavigationTab.values().forEach { tab ->
                                NavigationBarItem(
                                    selected = selectedTab == tab,
                                    onClick = { selectedTab = tab },
                                    icon = { Icon(tab.icon, contentDescription = tab.label) },
                                    label = { Text(tab.label) },
                                    colors = NavigationBarItemDefaults.colors(
                                        selectedIconColor = CyanGlow,
                                        selectedTextColor = CyanGlow,
                                        indicatorColor = SurfaceDark
                                    )
                                )
                            }
                        }
                    }
                ) { innerPadding ->
                    val modifier = Modifier.padding(innerPadding)
                    when (selectedTab) {
                        NavigationTab.DASHBOARD -> DashboardScreen(viewModel = viewModel, modifier = modifier)
                        NavigationTab.PROVIDERS -> ProvidersScreen(viewModel = viewModel, modifier = modifier)
                        NavigationTab.SKILLS -> SkillsScreen(viewModel = viewModel, modifier = modifier)
                        NavigationTab.PROMPT -> PromptScreen(viewModel = viewModel, modifier = modifier)
                        NavigationTab.HARDWARE -> HardwareScreen(viewModel = viewModel, modifier = modifier)
                    }
                }
            }
        }
    }
}
