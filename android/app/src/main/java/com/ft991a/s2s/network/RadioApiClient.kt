package com.ft991a.s2s.network

import com.ft991a.s2s.data.models.RadioTelemetry
import com.ft991a.s2s.data.models.SkillItem
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException

class RadioApiClient(private var baseUrl: String = "http://192.168.1.100:80") {

    private val client = OkHttpClient.Builder().build()
    private val gson = Gson()
    private var webSocket: WebSocket? = null

    fun setHost(host: String, port: Int) {
        baseUrl = if (port == 80) "http://$host" else "http://$host:$port"
    }

    fun getBaseUrl(): String = baseUrl

    fun connectWebSocket(
        onTelemetry: (RadioTelemetry) -> Unit,
        onStatusChange: (Boolean) -> Unit
    ) {
        val wsUrl = baseUrl.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
        val request = Request.Builder().url(wsUrl).build()

        webSocket?.cancel()
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                onStatusChange(true)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val telemetry = gson.fromJson(text, RadioTelemetry::class.java)
                    if (telemetry != null) {
                        onTelemetry(telemetry)
                    }
                } catch (e: Exception) {
                    // Ignore parse errors for non-telemetry frames
                }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                onStatusChange(false)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                onStatusChange(false)
            }
        })
    }

    fun disconnectWebSocket() {
        webSocket?.close(1000, "App closed")
        webSocket = null
    }

    suspend fun setPtt(active: Boolean): Boolean = withContext(Dispatchers.IO) {
        try {
            val json = """{"active": $active}"""
            val body = json.toRequestBody("application/json".toMediaType())
            val req = Request.Builder().url("$baseUrl/api/ptt").post(body).build()
            client.newCall(req).execute().isSuccessful
        } catch (e: Exception) {
            false
        }
    }

    suspend fun simulateRx(duration: Float = 4f): Boolean = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder().url("$baseUrl/api/simulate-rx?duration=$duration").post("".toRequestBody()).build()
            client.newCall(req).execute().isSuccessful
        } catch (e: Exception) {
            false
        }
    }

    suspend fun autoDetectCatPort(): String? = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder().url("$baseUrl/api/auto-detect-port").post("".toRequestBody()).build()
            val resp = client.newCall(req).execute()
            if (resp.isSuccessful) {
                val map = gson.fromJson<Map<String, Any>>(resp.body?.string(), Map::class.java)
                map["detected_port"] as? String
            } else null
        } catch (e: Exception) {
            null
        }
    }

    suspend fun autoDetectAudio(): Boolean = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder().url("$baseUrl/api/auto-detect-audio").post("".toRequestBody()).build()
            client.newCall(req).execute().isSuccessful
        } catch (e: Exception) {
            false
        }
    }

    suspend fun fetchSkills(): List<SkillItem> = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder().url("$baseUrl/api/skills").get().build()
            val resp = client.newCall(req).execute()
            if (resp.isSuccessful) {
                val type = object : TypeToken<List<SkillItem>>() {}.type
                gson.fromJson(resp.body?.string(), type) ?: emptyList()
            } else emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun executeSkillTest(skillName: String, args: Map<String, Any>): String = withContext(Dispatchers.IO) {
        try {
            val body = gson.toJson(args).toRequestBody("application/json".toMediaType())
            val req = Request.Builder().url("$baseUrl/api/skills/$skillName/test").post(body).build()
            val resp = client.newCall(req).execute()
            resp.body?.string() ?: "No response"
        } catch (e: Exception) {
            "Error: ${e.message}"
        }
    }

    suspend fun fetchSystemPrompt(): String = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder().url("$baseUrl/api/system-prompt").get().build()
            val resp = client.newCall(req).execute()
            if (resp.isSuccessful) {
                val map = gson.fromJson<Map<String, Any>>(resp.body?.string(), Map::class.java)
                map["system_prompt"] as? String ?: ""
            } else ""
        } catch (e: Exception) {
            ""
        }
    }

    suspend fun saveSystemPrompt(prompt: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val body = gson.toJson(mapOf("system_prompt" to prompt)).toRequestBody("application/json".toMediaType())
            val req = Request.Builder().url("$baseUrl/api/system-prompt").post(body).build()
            client.newCall(req).execute().isSuccessful
        } catch (e: Exception) {
            false
        }
    }

    suspend fun updateProviders(updates: Map<String, Any>): Boolean = withContext(Dispatchers.IO) {
        try {
            val body = gson.toJson(updates).toRequestBody("application/json".toMediaType())
            val req = Request.Builder().url("$baseUrl/api/providers").post(body).build()
            client.newCall(req).execute().isSuccessful
        } catch (e: Exception) {
            false
        }
    }
}
