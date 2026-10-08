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

@Composable
fun HardwareScreen(viewModel: RadioViewModel, modifier: Modifier = Modifier) {
    val host by viewModel.host.collectAsState()
    val port by viewModel.port.collectAsState()
    val statusMsg by viewModel.statusMessage.collectAsState()

    var inputHost by remember { mutableStateOf(host) }
    var inputPort by remember { mutableStateOf(port.toString()) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(BgDark)
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "HARDWARE & CONNECTION",
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
            color = CyanGlow
        )

        Spacer(modifier = Modifier.height(16.dp))

        Text("SBC Appliance Network Endpoint:", fontSize = 12.sp, color = TextMuted)
        Spacer(modifier = Modifier.height(4.dp))

        Row(modifier = Modifier.fillMaxWidth()) {
            OutlinedTextField(
                value = inputHost,
                onValueChange = { inputHost = it },
                label = { Text("IP Address") },
                modifier = Modifier.weight(2f),
                colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = CyanGlow)
            )
            Spacer(modifier = Modifier.width(8.dp))
            OutlinedTextField(
                value = inputPort,
                onValueChange = { inputPort = it },
                label = { Text("Port") },
                modifier = Modifier.weight(1f),
                colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = CyanGlow)
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        Button(
            onClick = {
                val p = inputPort.toIntOrNull() ?: 80
                viewModel.updateConnection(inputHost, p)
            },
            modifier = Modifier.fillMaxWidth().height(48.dp),
            colors = ButtonDefaults.buttonColors(containerColor = CyanGlow),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text("CONNECT TO APPLIANCE", color = Color.Black, fontWeight = FontWeight.Bold)
        }

        Spacer(modifier = Modifier.height(24.dp))

        Text("Hardware Discovery on Appliance:", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = YaesuAmber)
        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = { viewModel.autoDetectPort() },
            modifier = Modifier.fillMaxWidth().height(44.dp),
            colors = ButtonDefaults.buttonColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text("AUTO-DETECT FT-991A CAT PORT (CP2105)", color = CyanGlow)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = { viewModel.autoDetectAudio() },
            modifier = Modifier.fillMaxWidth().height(44.dp),
            colors = ButtonDefaults.buttonColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text("AUTO-DETECT USB AUDIO CODEC", color = CyanGlow)
        }

        if (statusMsg.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = statusMsg, color = YaesuAmber, fontSize = 12.sp)
        }
    }
}
