package com.research.sensormax

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Environment
import android.os.SystemClock
import android.util.Log
import java.io.BufferedWriter
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap

class SensorEngine(
    private val context: Context,
    private val logCallback: (String) -> Unit
) : SensorEventListener {

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    val allSensors: List<Sensor> = sensorManager.getSensorList(Sensor.TYPE_ALL)

    // Active sensors enabled by user
    private val enabledSensorTypes = mutableSetOf<Int>()

    // Filtering / Sensitivity settings
    var alpha: Float = 0.0f // 0.0 = Raw unfiltered, 0.9 = heavy low-pass smooth
    var deltaThreshold: Float = 0.0f // Dead zone minimum delta

    // Last filtered values and timestamps per sensor type
    private val lastFilteredValues = ConcurrentHashMap<Int, FloatArray>()
    private val lastSampleTimes = ConcurrentHashMap<Int, Long>()

    // Local CSV Recorder
    private var isRecording = false
    private var csvWriter: BufferedWriter? = null
    private var currentCsvFile: File? = null

    // Streaming callback
    var onDataReady: ((String) -> Unit)? = null

    fun getDiscoveredSensorNames(): List<Pair<Int, String>> {
        return allSensors.map { sensor ->
            Pair(sensor.type, "${sensor.name} [Type ${sensor.type}, Vendor: ${sensor.vendor}]")
        }
    }

    fun setSensorEnabled(sensorType: Int, enabled: Boolean) {
        if (enabled) {
            enabledSensorTypes.add(sensorType)
        } else {
            enabledSensorTypes.remove(sensorType)
            sensorManager.unregisterListener(this, sensorManager.getDefaultSensor(sensorType))
        }
    }

    fun startListening(rateDelay: Int) {
        stopListening()
        var registeredCount = 0
        for (type in enabledSensorTypes) {
            val sensor = sensorManager.getDefaultSensor(type)
            if (sensor != null) {
                sensorManager.registerListener(this, sensor, rateDelay)
                registeredCount++
            }
        }
        logCallback("Started listening to $registeredCount sensors at delay mode $rateDelay.")
    }

    fun stopListening() {
        sensorManager.unregisterListener(this)
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event == null) return
        val type = event.sensor.type
        val rawValues = event.values
        val nowMs = System.currentTimeMillis()

        // 1. Apply Low-Pass Smoothing Filter (if alpha > 0)
        val prevFiltered = lastFilteredValues[type]
        val filtered = FloatArray(rawValues.size)
        var maxDelta = 0.0f

        if (prevFiltered != null && prevFiltered.size == rawValues.size && alpha > 0.0f) {
            for (i in rawValues.indices) {
                filtered[i] = alpha * prevFiltered[i] + (1.0f - alpha) * rawValues[i]
                val diff = Math.abs(filtered[i] - prevFiltered[i])
                if (diff > maxDelta) maxDelta = diff
            }
        } else {
            for (i in rawValues.indices) {
                filtered[i] = rawValues[i]
                if (prevFiltered != null && i < prevFiltered.size) {
                    val diff = Math.abs(filtered[i] - prevFiltered[i])
                    if (diff > maxDelta) maxDelta = diff
                } else {
                    maxDelta = Float.MAX_VALUE
                }
            }
        }

        // 2. Apply Dead-Zone Sensitivity Threshold (if deltaThreshold > 0)
        if (prevFiltered != null && maxDelta < deltaThreshold) {
            // Drop sample because change is smaller than user configured sensitivity dead-zone
            return
        }

        lastFilteredValues[type] = filtered
        lastSampleTimes[type] = nowMs

        // Format values into compact CSV line:
        // timestamp_ms,sensor_type,sensor_name,val0,val1,val2,val3...
        val valStr = filtered.joinToString(",") { String.format(Locale.US, "%.5f", it) }
        val csvLine = "$nowMs,$type,\"${event.sensor.name}\",$valStr"

        // Send to streaming client if active
        onDataReady?.invoke(csvLine)

        // Save to local CSV file if recording
        if (isRecording && csvWriter != null) {
            try {
                csvWriter?.write(csvLine)
                csvWriter?.newLine()
            } catch (e: Exception) {
                Log.e("SensorEngine", "Error writing CSV", e)
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // No action needed for research logging
    }

    fun startLocalRecording(): File? {
        if (isRecording) stopLocalRecording()
        try {
            val dir = File(Environment.getExternalStorageDirectory(), "SensorMax_Records")
            if (!dir.exists()) dir.mkdirs()
            val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
            currentCsvFile = File(dir, "oppo_a33w_sensors_$timestamp.csv")
            csvWriter = BufferedWriter(FileWriter(currentCsvFile!!))
            
            // Header
            csvWriter?.write("Timestamp_ms,Sensor_Type,Sensor_Name,Value0,Value1,Value2,Value3,Value4,Value5\n")
            isRecording = true
            logCallback("Started local CSV recording -> ${currentCsvFile!!.absolutePath}")
            return currentCsvFile
        } catch (e: Exception) {
            logCallback("Failed to start local CSV recording: ${e.message}")
            return null
        }
    }

    fun stopLocalRecording() {
        if (!isRecording) return
        isRecording = false
        try {
            csvWriter?.flush()
            csvWriter?.close()
            logCallback("Saved local CSV file -> ${currentCsvFile?.absolutePath}")
        } catch (e: Exception) {}
        csvWriter = null
    }
}
