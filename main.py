# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import json, uuid

app = FastAPI()

# Allow your PWA (localhost or LAN IP) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# room_id -> list of active WebSocket connections
rooms: Dict[str, List[WebSocket]] = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    rooms.setdefault(room_id, []).append(websocket)
    print(f"Client joined room {room_id}. Total: {len(rooms[room_id])}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            # Broadcast to all other clients in the same room
            for connection in rooms[room_id]:
                if connection != websocket:
                    await connection.send_text(data)

            # Simple logging (optional)
            if msg_type == "clipboard":
                print(f"[{room_id}] Clipboard: {message.get('text')[:50]}...")
            elif msg_type in ("file_offer", "webrtc_offer", "webrtc_answer", "webrtc_ice"):
                print(f"[{room_id}] Signaling: {msg_type}")

    except WebSocketDisconnect:
        rooms[room_id].remove(websocket)
        if not rooms[room_id]:
            del rooms[room_id]
        print(f"Client left room {room_id}. Remaining: {len(rooms.get(room_id, []))}")

# Optional: generate a new room ID + pairing token
@app.get("/new-room")
async def new_room():
    room_id = str(uuid.uuid4())[:8]
    token = str(uuid.uuid4())[:6].upper()
    return {"room_id": room_id, "pairing_token": token}
