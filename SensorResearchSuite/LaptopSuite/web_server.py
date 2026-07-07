#!/usr/bin/env python3
"""
SensorMax Web Gateway Server
Bridges Oppo A33w sensor streams (UDP/TCP) to a WebSocket server for live browser rendering.
Run: python3 web_server.py --udp-port 5005 --ws-port 8765
"""

import asyncio
import socket
import json
import argparse

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")

connected_clients = set()

class UdpServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            line = data.decode('utf-8', errors='ignore').strip()
            if not line: return
            parts = [p.strip().strip('"') for p in line.split(',')]
            if len(parts) >= 4:
                payload = json.dumps({
                    "ts": int(parts[0]),
                    "type": int(parts[1]),
                    "name": parts[2],
                    "vals": [float(x) for x in parts[3:]]
                })
                # Broadcast to all connected websocket clients
                for ws in list(connected_clients):
                    asyncio.create_task(ws.send(payload))
        except Exception:
            pass

async def ws_handler(websocket, path=None):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def main(udp_port, ws_port):
    print(f"Starting UDP receiver on port {udp_port}...")
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: UdpServerProtocol(),
        local_addr=('0.0.0.0', udp_port)
    )
    print(f"Starting WebSocket server on ws://localhost:{ws_port}...")
    async with websockets.serve(ws_handler, "0.0.0.0", ws_port):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--udp-port", type=int, default=5005)
    parser.add_argument("--ws-port", type=int, default=8765)
    args = parser.parse_args()
    try:
        asyncio.run(main(args.udp_port, args.ws_port))
    except KeyboardInterrupt:
        print("Server stopped.")
