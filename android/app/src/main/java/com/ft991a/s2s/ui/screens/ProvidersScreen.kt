package com.ft991a.s2s.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ft991a.s2s.ui.theme.*
import com.ft991a.s2s.viewmodel.RadioViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProvidersScreen(viewModel: RadioViewModel, modifier: Modifier = Modifier) {
    val telemetry by viewModel.telemetry.collectAsState()
    val statusMsg by viewModel.statusMessage.collectAsState()

    val supportedLanguages = listOf(
        "en (English)",
        "sk (Slovak)",
        "cs (Czech)",
        "de (German)",
        "fr (French)",
        "es (Spanish)",
        "pl (Polish)",
        "it (Italian)",
        "uk (Ukrainian)",
        "ja (Japanese)",
        "nl (Dutch)",
        "pt (Portuguese)",
        "ru (Russian)",
        "sv (Swedish)",
        "hu (Hungarian)",
        "hr (Croatian)"
    )

    var pipelineMode by remember { mutableStateOf(telemetry.pipeline_mode) }
    var sttProvider by remember { mutableStateOf(telemetry.stt_provider) }
    var llmProvider by remember { mutableStateOf(telemetry.llm_provider) }
    var ttsProvider by remember { mutableStateOf(telemetry.tts_provider) }
    var selectedLanguage by remember { mutableStateOf("en (English)") }
    var langExpanded by remember { mutableStateOf(false) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(BgDark)
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "AI PIPELINE & PROVIDERS",
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
            color = CyanGlow
        )

        Spacer(modifier = Modifier.height(16.dp))

        Text("Pipeline Architecture Mode:", fontSize = 12.sp, color = TextMuted)
        Row(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
            Button(
                onClick = { pipelineMode = "realtime" },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (pipelineMode == "realtime") CyanGlow else SurfaceDark
                ),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.weight(1f)
            ) {
                Text("Realtime S2S", color = if (pipelineMode == "realtime") Color.Black else TextPrimary)
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(
                onClick = { pipelineMode = "cascaded" },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (pipelineMode == "cascaded") CyanGlow else SurfaceDark
                ),
                shape = RoundedCornerShape(6.dp),
                modifier = Modifier.weight(1f)
            ) {
                Text("Cascaded", color = if (pipelineMode == "cascaded") Color.Black else TextPrimary)
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedTextField(
            value = sttProvider,
            onValueChange = { sttProvider = it },
            label = { Text("STT Provider (deepgram, openai, mock)") },
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = CyanGlow)
        )

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = llmProvider,
            onValueChange = { llmProvider = it },
            label = { Text("LLM Provider (openai, groq, anthropic, google, ollama)") },
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = CyanGlow)
        )

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = ttsProvider,
            onValueChange = { ttsProvider = it },
            label = { Text("TTS Provider (cartesia, elevenlabs, openai)") },
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = CyanGlow)
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Unified STT & TTS Language Single Dropdown
        ExposedDropdownMenuBox(
            expanded = langExpanded,
            onExpandedChange = { langExpanded = !langExpanded },
            modifier = Modifier.fillMaxWidth()
        ) {
            OutlinedTextField(
                value = selectedLanguage,
                onValueChange = {},
                readOnly = true,
                label = { Text("Language (STT & TTS Unified)") },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = langExpanded) },
                colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = CyanGlow),
                modifier = Modifier.menuAnchor().fillMaxWidth()
            )
            ExposedDropdownMenu(
                expanded = langExpanded,
                onDismissRequest = { langExpanded = false }
            ) {
                supportedLanguages.forEach { lang ->
                    DropdownMenuItem(
                        text = { Text(lang) },
                        onClick = {
                            selectedLanguage = lang
                            langExpanded = false
                        }
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        Button(
            onClick = {
                val langCode = selectedLanguage.substringBefore(" ").trim()
                viewModel.saveProviders(pipelineMode, sttProvider, llmProvider, ttsProvider, langCode)
            },
            modifier = Modifier.fillMaxWidth().height(48.dp),
            colors = ButtonDefaults.buttonColors(containerColor = GreenActive),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text("SAVE PROVIDER PREFERENCES", color = Color.Black, fontWeight = FontWeight.Bold)
        }

        if (statusMsg.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(text = statusMsg, color = YaesuAmber, fontSize = 12.sp)
        }
    }
}

