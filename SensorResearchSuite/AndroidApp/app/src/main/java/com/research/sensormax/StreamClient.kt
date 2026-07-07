package com.research.sensormax

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import android.util.Log
import java.io.OutputStream
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.UUID
import java.util.concurrent.Executors
import java.util.concurrent.LinkedBlockingQueue

enum class TransportMode {
    WIFI_UDP,
    USB_ADB_SERVER,
    BLUETOOTH_SPP
}

class StreamClient(private val logCallback: (String) -> Unit) {
    private var isRunning = false
    private val packetQueue = LinkedBlockingQueue<String>(5000)
    private val executor = Executors.newSingleThreadExecutor()

    private var udpSocket: DatagramSocket? = null
    private var tcpServerSocket: ServerSocket? = null
    private var tcpClientSocket: Socket? = null
    private var btSocket: BluetoothSocket? = null
    private var outputStream: OutputStream? = null

    private var currentMode: TransportMode = TransportMode.WIFI_UDP
    private var targetIp: String = "192.168.1.100"
    private var targetPort: Int = 5005

    // Standard SPP UUID for Bluetooth Serial streaming
    private val SPP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")

    fun start(mode: TransportMode, target: String, port: Int) {
        if (isRunning) stop()
        this.currentMode = mode
        this.targetIp = target
        this.targetPort = port
        this.isRunning = true
        packetQueue.clear()

        executor.execute {
            try {
                when (mode) {
                    TransportMode.WIFI_UDP -> {
                        udpSocket = DatagramSocket()
                        logCallback("Connected WiFi UDP -> $target:$port")
                    }
                    TransportMode.USB_ADB_SERVER -> {
                        // Bind server socket on phone port (e.g., 5005). Laptop connects via `adb forward tcp:5005 tcp:5005`
                        logCallback("Listening for USB ADB connection on port $port...")
                        tcpServerSocket = ServerSocket(port)
                        tcpClientSocket = tcpServerSocket?.accept()
                        outputStream = tcpClientSocket?.getOutputStream()
                        logCallback("USB ADB Connected to Laptop!")
                    }
                    TransportMode.BLUETOOTH_SPP -> {
                        val adapter = BluetoothAdapter.getDefaultAdapter()
                        if (adapter == null) {
                            logCallback("Error: No Bluetooth adapter found on device.")
                            return@execute
                        }
                        // Target can be MAC address or device name
                        var device: BluetoothDevice? = null
                        if (BluetoothAdapter.checkBluetoothAddress(target)) {
                            device = adapter.getRemoteDevice(target)
                        } else {
                            val paired = adapter.bondedDevices
                            device = paired.find { it.name.contains(target, ignoreCase = true) || it.address == target }
                        }
                        if (device == null) {
                            logCallback("Error: Bluetooth target '$target' not found in paired devices.")
                            return@execute
                        }
                        logCallback("Connecting Bluetooth SPP to ${device.name} (${device.address})...")
                        btSocket = device.createRfcommSocketToServiceRecord(SPP_UUID)
                        btSocket?.connect()
                        outputStream = btSocket?.outputStream
                        logCallback("Bluetooth SPP Connected successfully!")
                    }
                }

                // Main streaming loop
                while (isRunning) {
                    val payload = packetQueue.take()
                    val bytes = (payload + "\n").toByteArray(Charsets.UTF_8)
                    when (currentMode) {
                        TransportMode.WIFI_UDP -> {
                            val addr = InetAddress.getByName(targetIp)
                            val packet = DatagramPacket(bytes, bytes.size, addr, targetPort)
                            udpSocket?.send(packet)
                        }
                        TransportMode.USB_ADB_SERVER, TransportMode.BLUETOOTH_SPP -> {
                            outputStream?.write(bytes)
                            outputStream?.flush()
                        }
                    }
                }
            } catch (e: Exception) {
                if (isRunning) {
                    logCallback("Stream Error: ${e.message}")
                    Log.e("StreamClient", "Error in transport $mode", e)
                }
            }
        }
    }

    fun sendData(csvOrJsonString: String) {
        if (!isRunning) return
        // Non-blocking offer; drop oldest if queue is overflowing under extreme sampling rates
        if (!packetQueue.offer(csvOrJsonString)) {
            packetQueue.poll() // drop oldest
            packetQueue.offer(csvOrJsonString)
        }
    }

    fun stop() {
        isRunning = false
        try { udpSocket?.close() } catch (e: Exception) {}
        try { outputStream?.close() } catch (e: Exception) {}
        try { tcpClientSocket?.close() } catch (e: Exception) {}
        try { tcpServerSocket?.close() } catch (e: Exception) {}
        try { btSocket?.close() } catch (e: Exception) {}
        logCallback("Streaming stopped.")
    }
}
