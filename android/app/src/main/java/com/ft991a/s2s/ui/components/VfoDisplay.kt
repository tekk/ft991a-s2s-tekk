package com.ft991a.s2s.ui.components

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ft991a.s2s.data.models.RadioTelemetry
import com.ft991a.s2s.ui.theme.*

@Composable
fun VfoDisplay(telemetry: RadioTelemetry, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(2.dp, CyanGlow, RoundedCornerShape(12.dp)),
        colors = CardDefaults.cardColors(containerColor = SurfaceDark),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = telemetry.frequency_str,
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                color = CyanGlow
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "MODE: ${telemetry.mode}  |  POWER: ${telemetry.power_watts}W",
                fontSize = 13.sp,
                color = YaesuAmber
            )
            Spacer(modifier = Modifier.height(6.dp))

            val stateColor = when (telemetry.state) {
                "TX" -> RedTransmit
                "RX" -> GreenActive
                else -> CyanGlow
            }
            Text(
                text = "STATE: ${telemetry.state}  //  ${telemetry.callsign}",
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = stateColor
            )
        }
    }
}
