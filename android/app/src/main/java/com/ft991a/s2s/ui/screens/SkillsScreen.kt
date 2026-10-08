package com.ft991a.s2s.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
fun SkillsScreen(viewModel: RadioViewModel, modifier: Modifier = Modifier) {
    val skills by viewModel.skills.collectAsState()
    val testOutput by viewModel.skillTestOutput.collectAsState()

    var selectedSkill by remember { mutableStateOf("lookup_callsign") }
    var skillArg by remember { mutableStateOf("W1AW") }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(BgDark)
            .padding(16.dp)
    ) {
        Text(
            text = "AGENT SKILLS & TOOLS",
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
            color = CyanGlow
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text("Registered Skills:", fontSize = 12.sp, color = TextMuted)
        Spacer(modifier = Modifier.height(4.dp))

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .height(160.dp)
                .border(1.dp, SurfaceBorder, RoundedCornerShape(8.dp)),
            colors = CardDefaults.cardColors(containerColor = SurfaceDark)
        ) {
            LazyColumn(modifier = Modifier.padding(8.dp)) {
                items(skills) { s ->
                    Column(modifier = Modifier.padding(vertical = 4.dp)) {
                        Text(text = "• ${s.name}", fontWeight = FontWeight.Bold, color = CyanGlow, fontSize = 13.sp)
                        Text(text = s.description, color = TextPrimary, fontSize = 11.sp)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text("Test Skill Execution:", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = YaesuAmber)
        Spacer(modifier = Modifier.height(6.dp))

        OutlinedTextField(
            value = selectedSkill,
            onValueChange = { selectedSkill = it },
            label = { Text("Skill Name (lookup_callsign, get_solar_propagation, etc.)") },
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = CyanGlow)
        )

        Spacer(modifier = Modifier.height(6.dp))

        OutlinedTextField(
            value = skillArg,
            onValueChange = { skillArg = it },
            label = { Text("Argument (e.g. Callsign)") },
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = CyanGlow)
        )

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = { viewModel.testSkill(selectedSkill, skillArg) },
            modifier = Modifier.fillMaxWidth().height(44.dp),
            colors = ButtonDefaults.buttonColors(containerColor = CyanGlow),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text("EXECUTE SKILL TEST", color = Color.Black, fontWeight = FontWeight.Bold)
        }

        Spacer(modifier = Modifier.height(10.dp))

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .border(1.dp, SurfaceBorder, RoundedCornerShape(8.dp)),
            colors = CardDefaults.cardColors(containerColor = SurfaceDark)
        ) {
            Column(modifier = Modifier.padding(10.dp)) {
                Text(text = "Execution Result:", fontSize = 11.sp, color = TextMuted)
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = testOutput.ifEmpty { "Awaiting skill test execution..." },
                    fontSize = 11.sp,
                    color = TextPrimary
                )
            }
        }
    }
}
