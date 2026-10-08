package com.ft991a.s2s.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ft991a.s2s.ui.theme.*
import com.ft991a.s2s.viewmodel.RadioViewModel

@Composable
fun PromptScreen(viewModel: RadioViewModel, modifier: Modifier = Modifier) {
    val systemPrompt by viewModel.systemPrompt.collectAsState()
    val statusMsg by viewModel.statusMessage.collectAsState()

    var promptText by remember { mutableStateOf(systemPrompt) }

    LaunchedEffect(systemPrompt) {
        if (systemPrompt.isNotEmpty()) {
            promptText = systemPrompt
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(BgDark)
            .padding(16.dp)
    ) {
        Text(
            text = "SYSTEM PROMPT & GUARDRAILS",
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
            color = CyanGlow
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Station guidelines strictly enforced by Part 97 prompt rules.",
            fontSize = 12.sp,
            color = TextMuted
        )

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedTextField(
            value = promptText,
            onValueChange = { promptText = it },
            label = { Text("System Prompt") },
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = CyanGlow,
                focusedTextColor = TextPrimary,
                unfocusedTextColor = TextPrimary
            )
        )

        Spacer(modifier = Modifier.height(16.dp))

        Row(modifier = Modifier.fillMaxWidth()) {
            Button(
                onClick = { viewModel.savePrompt(promptText) },
                modifier = Modifier.weight(1f).height(48.dp),
                colors = ButtonDefaults.buttonColors(containerColor = GreenActive),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text("SAVE PROMPT", color = Color.Black, fontWeight = FontWeight.Bold)
            }
        }

        if (statusMsg.isNotEmpty()) {
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = statusMsg, color = YaesuAmber, fontSize = 12.sp)
        }
    }
}
