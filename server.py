import asyncio
import json
import sqlite3
import websockets
from datetime import datetime

# Database initialisatie
DB_FILE = "poc_radio.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Maak tabel voor gebruikers als deze niet bestaat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            naam TEXT PRIMARY KEY,
            online INTEGER DEFAULT 0,
            tijd TEXT,
            laast_gezien TEXT
        )
    """)
    # Maak tabel voor chatberichten als deze niet bestaat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tijd TEXT,
            naam TEXT,
            bericht TEXT
        )
    """)
    conn.commit()
    conn.close()

def haal_gebruikers_op():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT naam, online, tijd, laast_gezien FROM users")
    rows = cursor.fetchall()
    conn.close()
    
    gebruikers = []
    for row in rows:
        gebruikers.append({
            "naam": row[0],
            "online": bool(row[1]),
            "tijd": row[2] if row[2] else "-",
            "laast_gezien": row[3] if row[3] else "-"
        })
    return gebruikers

def haal_chat_op():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT tijd, naam, bericht FROM chat_messages ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    
    berichten = []
    for row in reversed(rows):
        berichten.append({
            "tijd": row[0],
            "naam": row[1],
            "bericht": row[2]
        })
    return berichten

def sla_bericht_op(naam, bericht):
    tijd = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (tijd, naam, bericht) VALUES (?, ?, ?)", (tijd, naam, bericht))
    conn.commit()
    conn.close()

CONNECTED_CLIENTS = set()

async def broadcast_status():
    if CONNECTED_CLIENTS:
        data = {
            "type": "status_update",
            "users": haal_gebruikers_op()
        }
        message = json.dumps(data)
        await asyncio.gather(*[client.send(message) for client in CONNECTED_CLIENTS], return_exceptions=True)

async def broadcast_chat():
    if CONNECTED_CLIENTS:
        data = {
            "type": "chat_update",
            "messages": haal_chat_op()
        }
        message = json.dumps(data)
        await asyncio.gather(*[client.send(message) for client in CONNECTED_CLIENTS], return_exceptions=True)

async def handler(websocket, path):
    # Accepteer verbindingen op de /ws route of root als fallback
    if path != "/ws" and path != "/":
        return

    CONNECTED_CLIENTS.add(websocket)
    try:
        # Stuur direct de huidige status en chatgeschiedenis naar de nieuwe bezoeker
        await websocket.send(json.dumps({"type": "status_update", "users": haal_gebruikers_op()}))
        await websocket.send(json.dumps({"type": "chat_update", "messages": haal_chat_op()}))

        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "chat":
                sla_bericht_op(data["naam"], data["bericht"])
                await broadcast_chat()
            elif data.get("type") == "request_update":
                await websocket.send(json.dumps({"type": "status_update", "users": haal_gebruikers_op()}))
    except websockets.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.remove(websocket)

async def main():
    init_db()
    # De server start op poort 10000 (standaard voor Render)
    async with websockets.serve(handler, "0.0.0.0", 10000):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
