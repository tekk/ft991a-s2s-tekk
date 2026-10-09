package com.ft991a.s2s.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ft991a.s2s.data.models.RadioTelemetry
import com.ft991a.s2s.data.models.SkillItem
import com.ft991a.s2s.network.RadioApiClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class RadioViewModel : ViewModel() {

    val apiClient = RadioApiClient()

    private val _telemetry = MutableStateFlow(RadioTelemetry())
    val telemetry: StateFlow<RadioTelemetry> = _telemetry.asStateFlow()

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected.asStateFlow()

    private val _host = MutableStateFlow("192.168.1.100")
    val host: StateFlow<String> = _host.asStateFlow()

    private val _port = MutableStateFlow(80)
    val port: StateFlow<Int> = _port.asStateFlow()

    private val _skills = MutableStateFlow<List<SkillItem>>(emptyList())
    val skills: StateFlow<List<SkillItem>> = _skills.asStateFlow()

    private val _skillTestOutput = MutableStateFlow("")
    val skillTestOutput: StateFlow<String> = _skillTestOutput.asStateFlow()

    private val _systemPrompt = MutableStateFlow("")
    val systemPrompt: StateFlow<String> = _systemPrompt.asStateFlow()

    private val _statusMessage = MutableStateFlow("")
    val statusMessage: StateFlow<String> = _statusMessage.asStateFlow()

    fun updateConnection(host: String, port: Int) {
        _host.value = host
        _port.value = port
        apiClient.setHost(host, port)
        connect()
    }

    fun connect() {
        apiClient.connectWebSocket(
            onTelemetry = { telem ->
                _telemetry.value = telem
            },
            onStatusChange = { connected ->
                _isConnected.value = connected
            }
        )
        refreshData()
    }

    fun refreshData() {
        viewModelScope.launch {
            _skills.value = apiClient.fetchSkills()
            _systemPrompt.value = apiClient.fetchSystemPrompt()
        }
    }

    fun togglePtt() {
        val currentState = _telemetry.value.ptt_active
        viewModelScope.launch {
            apiClient.setPtt(!currentState)
        }
    }

    fun simulateRx(duration: Float = 4f) {
        viewModelScope.launch {
            apiClient.simulateRx(duration)
        }
    }

    fun autoDetectPort() {
        viewModelScope.launch {
            val detected = apiClient.autoDetectCatPort()
            _statusMessage.value = if (detected != null) "Detected CAT port: $detected" else "No CAT port detected"
        }
    }

    fun autoDetectAudio() {
        viewModelScope.launch {
            val ok = apiClient.autoDetectAudio()
            _statusMessage.value = if (ok) "Audio Codec auto-detected" else "Audio detection failed"
        }
    }

    fun testSkill(skillName: String, arg: String) {
        viewModelScope.launch {
            _skillTestOutput.value = "Executing $skillName..."
            val args = mutableMapOf<String, Any>()
            if (skillName == "lookup_callsign") {
                args["callsign"] = if (arg.isNotBlank()) arg else "W1AW"
            } else if (skillName == "calculate_bearing") {
                args["from_grid"] = "FN31pr"
                args["to_grid"] = if (arg.isNotBlank()) arg else "JO21"
            }
            _skillTestOutput.value = apiClient.executeSkillTest(skillName, args)
        }
    }

    fun savePrompt(prompt: String) {
        viewModelScope.launch {
            val ok = apiClient.saveSystemPrompt(prompt)
            if (ok) {
                _systemPrompt.value = prompt
                _statusMessage.value = "System prompt saved successfully"
            }
        }
    }

    fun saveProviders(
        pipelineMode: String,
        sttProvider: String,
        llmProvider: String,
        ttsProvider: String,
        language: String
    ) {
        viewModelScope.launch {
            val updates = mapOf(
                "pipeline_mode" to pipelineMode,
                "stt_provider" to sttProvider,
                "llm_provider" to llmProvider,
                "tts_provider" to ttsProvider,
                "language" to language,
                "stt_language" to language,
                "tts_language" to language
            )
            val ok = apiClient.updateProviders(updates)
            _statusMessage.value = if (ok) "Providers configuration updated" else "Failed to update providers"
        }
    }

    fun saveProviders(
        pipelineMode: String,
        sttProvider: String,
        llmProvider: String,
        ttsProvider: String,
        sttLang: String,
        ttsLang: String
    ) = saveProviders(pipelineMode, sttProvider, llmProvider, ttsProvider, sttLang)


    override fun onCleared() {
        super.onCleared()
        apiClient.disconnectWebSocket()
    }
}
