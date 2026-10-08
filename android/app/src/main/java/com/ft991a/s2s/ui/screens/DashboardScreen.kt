package com.ft991a.s2s.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ft991a.s2s.ui.components.PttButton
import com.ft991a.s2s.ui.components.SMeterBar
import com.ft991a.s2s.ui.components.VfoDisplay
import com.ft991a.s2s.ui.theme.*
import com.ft991a.s2s.viewmodel.RadioViewModel

@Composable
fun DashboardScreen(viewModel: RadioViewModel, modifier: Modifier = Modifier) {
    val telemetry by viewModel.telemetry.collectAsState()
    val isConnected by viewModel.isConnected.collectAsState()
    val host by viewModel.host.collectAsState()
    val port by viewModel.port.collectAsState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(BgDark)
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        // Connection Bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "APPLIANCE: $host:$port",
                fontSize = 12.sp,
                color = TextMuted
            )
            Text(
                text = if (isConnected) "ONLINE" else "DISCONNECTED",
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = if (isConnected) GreenActive else RedTransmit
            )
        }

        // VFO Display
        VfoDisplay(telemetry = telemetry)

        Spacer(modifier = Modifier.height(16.dp))

        // S-Meter Bar
        SMeterBar(
            rawVal = telemetry.s_meter_raw,
            label = telemetry.s_meter_label,
            threshold = telemetry.threshold
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Controls
        PttButton(
            isPttActive = telemetry.ptt_active,
            onToggle = { viewModel.togglePtt() }
        )

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = { viewModel.simulateRx(4f) },
            modifier = Modifier
                .fillMaxWidth()
                .height(44.dp),
            colors = ButtonDefaults.buttonColors(containerColor = YaesuAmber),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text(
                text = "SIMULATE RX BURST (4s)",
                color = Color.Black,
                fontWeight = FontWeight.Bold,
                fontSize = 13.sp
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Live Transcripts
        Text(
            text = "LIVE RADIO TRANSCRIPTS",
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = CyanGlow
        )

        Spacer(modifier = Modifier.height(6.dp))

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, SurfaceBorder, RoundedCornerShape(8.dp)),
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(8.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    text = "[RX Operator]: ${telemetry.user_transcript.ifEmpty { "Listening on frequency..." }}",
                    fontSize = 12.sp,
                    color = YaesuAmber
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "[TX AI Agent]: ${telemetry.ai_transcript.ifEmpty { "Standing by under Part 97." }}",
                    fontSize = 12.sp,
                    color = CyanGlow
                )
            }
        }
    }
}
