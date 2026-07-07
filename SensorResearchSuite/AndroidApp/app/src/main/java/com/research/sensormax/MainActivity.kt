package com.research.sensormax

import android.Manifest
import android.content.pm.PackageManager
import android.hardware.SensorManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private lateinit var sensorEngine: SensorEngine
    private lateinit var streamClient: StreamClient

    private lateinit var tvStatus: TextView
    private lateinit var tvLog: TextView
    private lateinit var rgTransport: RadioGroup
    private lateinit var etTargetIp: EditText
    private lateinit var etTargetPort: EditText
    private lateinit var spinnerRate: Spinner
    private lateinit var seekDelta: SeekBar
    private lateinit var seekAlpha: SeekBar
    private lateinit var tvSensitivityLabel: TextView
    private lateinit var tvAlphaLabel: TextView
    private lateinit var llSensorList: LinearLayout
    private lateinit var btnToggleStream: Button
    private lateinit var btnToggleRecord: Button

    private var isStreaming = false
    private var isRecording = false

    private val handler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvStatus = findViewById(R.id.tvStatus)
        tvLog = findViewById(R.id.tvLog)
        rgTransport = findViewById(R.id.rgTransport)
        etTargetIp = findViewById(R.id.etTargetIp)
        etTargetPort = findViewById(R.id.etTargetPort)
        spinnerRate = findViewById(R.id.spinnerRate)
        seekDelta = findViewById(R.id.seekDelta)
        seekAlpha = findViewById(R.id.seekAlpha)
        tvSensitivityLabel = findViewById(R.id.tvSensitivityLabel)
        tvAlphaLabel = findViewById(R.id.tvAlphaLabel)
        llSensorList = findViewById(R.id.llSensorList)
        btnToggleStream = findViewById(R.id.btnToggleStream)
        btnToggleRecord = findViewById(R.id.btnToggleRecord)

        checkPermissions()

        streamClient = StreamClient { msg -> appendLog(msg) }
        sensorEngine = SensorEngine(this) { msg -> appendLog(msg) }

        sensorEngine.onDataReady = { csvLine ->
            if (isStreaming) {
                streamClient.sendData(csvLine)
            }
        }

        setupUI()
        populateSensorCheckboxes()
    }

    private fun setupUI() {
        val rates = arrayOf("Fastest (0ms - Hardware Limit)", "Game (~20ms)", "UI (~60ms)", "Normal (~200ms)")
        spinnerRate.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, rates)
        spinnerRate.setSelection(0) // Default to fastest

        seekDelta.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                val delta = progress / 10.0f
                sensorEngine.deltaThreshold = delta
                tvSensitivityLabel.text = "Dead Zone Delta (Δ threshold): ${String.format("%.2f", delta)} (Max Sensitivity = 0.00)"
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })

        seekAlpha.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                val alpha = progress / 100.0f
                sensorEngine.alpha = alpha
                tvAlphaLabel.text = "Low-Pass Smoothing (α): ${String.format("%.2f", alpha)} (0.00 = Raw Hardware Output)"
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })

        btnToggleStream.setOnClickListener {
            if (!isStreaming) {
                startStreaming()
            } else {
                stopStreaming()
            }
        }

        btnToggleRecord.setOnClickListener {
            if (!isRecording) {
                val file = sensorEngine.startLocalRecording()
                if (file != null) {
                    isRecording = true
                    btnToggleRecord.text = "STOP RECORDING"
                    btnToggleRecord.setBackgroundColor(0xFF8E24AA.toInt())
                    applyRateAndStartListening()
                }
            } else {
                sensorEngine.stopLocalRecording()
                isRecording = false
                btnToggleRecord.text = "RECORD LOCAL CSV"
                btnToggleRecord.setBackgroundColor(0xFFC62828.toInt())
                if (!isStreaming) sensorEngine.stopListening()
            }
        }
    }

    private fun populateSensorCheckboxes() {
        val discovered = sensorEngine.getDiscoveredSensorNames()
        llSensorList.removeAllViews()
        appendLog("Discovered ${discovered.size} sensors on this Oppo A33w.")

        for ((type, desc) in discovered) {
            val cb = CheckBox(this)
            cb.text = desc
            cb.textSize = 13f
            // By default, enable Accelerometer (1), Gyroscope (4), Magnetometer (2), Light (5), Proximity (8)
            val defaultEnable = type in listOf(1, 2, 4, 5, 8, 9, 10, 11)
            cb.isChecked = defaultEnable
            sensorEngine.setSensorEnabled(type, defaultEnable)

            cb.setOnCheckedChangeListener { _, isChecked ->
                sensorEngine.setSensorEnabled(type, isChecked)
                if (isStreaming || isRecording) {
                    applyRateAndStartListening()
                }
            }
            llSensorList.addView(cb)
        }
    }

    private fun startStreaming() {
        val target = etTargetIp.text.toString().trim()
        val portStr = etTargetPort.text.toString().trim()
        val port = portStr.toIntOrNull() ?: 5005

        val mode = when (rgTransport.checkedRadioButtonId) {
            R.id.rbWifi -> TransportMode.WIFI_UDP
            R.id.rbUsb -> TransportMode.USB_ADB_SERVER
            R.id.rbBt -> TransportMode.BLUETOOTH_SPP
            else -> TransportMode.WIFI_UDP
        }

        streamClient.start(mode, target, port)
        applyRateAndStartListening()
        isStreaming = true
        btnToggleStream.text = "STOP STREAMING"
        btnToggleStream.setBackgroundColor(0xFFE65100.toInt())
        tvStatus.text = "Status: STREAMING ($mode) -> $target:$port"
    }

    private fun stopStreaming() {
        streamClient.stop()
        if (!isRecording) {
            sensorEngine.stopListening()
        }
        isStreaming = false
        btnToggleStream.text = "START STREAMING"
        btnToggleStream.setBackgroundColor(0xFF2E7D32.toInt())
        tvStatus.text = "Status: Ready"
    }

    private fun applyRateAndStartListening() {
        val rateDelay = when (spinnerRate.selectedItemPosition) {
            0 -> SensorManager.SENSOR_DELAY_FASTEST
            1 -> SensorManager.SENSOR_DELAY_GAME
            2 -> SensorManager.SENSOR_DELAY_UI
            else -> SensorManager.SENSOR_DELAY_NORMAL
        }
        sensorEngine.startListening(rateDelay)
    }

    private fun appendLog(msg: String) {
        handler.post {
            val current = tvLog.text.toString()
            val lines = current.split("\n")
            val trimmed = if (lines.size > 50) lines.takeLast(49).joinToString("\n") else current
            tvLog.text = "$trimmed\n> $msg"
        }
    }

    private fun checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val perms = arrayOf(
                Manifest.permission.WRITE_EXTERNAL_STORAGE,
                Manifest.permission.READ_EXTERNAL_STORAGE,
                Manifest.permission.BLUETOOTH,
                Manifest.permission.BLUETOOTH_ADMIN
            )
            val needed = perms.filter { ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED }
            if (needed.isNotEmpty()) {
                ActivityCompat.requestPermissions(this, needed.toTypedArray(), 101)
            }
        }
    }
}
