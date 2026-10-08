package com.ft991a.s2s.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ft991a.s2s.ui.theme.*

@Composable
fun SMeterBar(
    rawVal: Int,
    label: String,
    threshold: Int,
    modifier: Modifier = Modifier
) {
    val progress = (rawVal.coerceIn(0, 255) / 255f)
    val barColor = if (rawVal >= threshold) GreenActive else YaesuAmber

    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "S-METER (THRESHOLD: S4)",
                fontSize = 11.sp,
                color = TextMuted
            )
            Text(
                text = "$label ($rawVal / 255)",
                fontSize = 11.sp,
                color = CyanGlow
            )
        }
        Spacer(modifier = Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = { progress },
            modifier = Modifier
                .fillMaxWidth()
                .height(14.dp)
                .clip(RoundedCornerShape(4.dp)),
            color = barColor,
            trackColor = Color(0xFF18243B)
        )
    }
}
