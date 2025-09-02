import websocket
import threading
import time
import json
import requests
from datetime import datetime
import html
import os
from flask import Flask, Response

# -------------------- CONFIG --------------------

PING_INTERVAL = 15
start_pinging = False

import os

WS_URL = os.environ.get("WS_URL") or "wss://ivasms.com:2087/socket.io/?token=eyJpdiI6IlNkeGhnaEZBa3IyRDdlc215RGdsNFE9PSIsInZhbHVlIjoiZ0pIMDlDS0hHNWZEQm1scUJTR3VicG1leDF4c1BHN2U2Y3RpUXlmSHVqQmxrZnFGaDd4VVNZTWUwVU9renhPUCtGZG03SFE3YytIcDlZQzU3SW9zTmVUOE9odzNvTkdKeU9jTlJiZzZSSk82SFo1MEVweVltN2kzajZlSXBGZmtlRXY4MjNmVjQ2Z3NzUXZqUUQ2UkZ3d3ltbDh2aVJER0pLbEc3SWs1T3QzREk1RFRDTzUxZFdpRHRTNlRkaHRxSWg5Lzd6bDg0RXF6MHJibDRvQ0Q5dTFuSmp1WHdhblNJSjVnd2xGMFlKSy9ldWlWbXZxWXNrMCtHNUVIZDRCR1RLL29ma0FsRzBSalVBdkVQOWtMc1Bqc01YZmFFaHFZNkZXbm1rdG05Ylp0dlVsK3RlbjJCR2l2RTBjKzUwYlNyRnUzc04wMmNUWUFnV0ZtYW5YeUw4MWVKaHdlYWFOSkxsY3crSExHemtaNjhNb0tsaGZlaE1qQklrWHphblRNOHhKUUpXVVZwelRSN3UranRCWDZsUGkwM1dnV0RVRjM1UWY5UzhNWndCc3dZWmo0cUhBb1pqYkh3KzlZczQyNlVPNWhhd1dQQitZeHZHeXh1NkRIdmt2YzNLVzZnL3l5WjNXSUwyUlBubGZiKzA1OFZoeEQyWHE1YnliMU9iYWw5YzU0eWF1dmp0Q2dML2szL0VPUzNRPT0iLCJtYWMiOiIwNmFiZDFkMzg3ODYxYzE0ZDRhNGJmYTlkYmMzZjdmZTRiMmZjMTMwNTc0MTZlZGZjODZjNGYzODI3MDIxZjY0IiwidGFnIjoiIn0%3D&user=8d75eedc6d2833853cf8fea9790e711a&EIO=4&transport=websocket"
AUTH_MESSAGE = os.environ.get("AUTH_MESSAGE") 
PING_INTERVAL = int(os.environ.get("PING_INTERVAL", 15))  # default 25 sec

BOT_TOKEN = os.environ.get("BOT_TOKEN") or 
GROUP_ID = os.environ.get("GROUP_ID") or "-1002311125652"
CHANNEL_URL = os.environ.get("CHANNEL_URL") or "https://t.me/DDXOTP"
DEV_URL = os.environ.get("DEV_URL") or "https://t.me/vxxwo"
CHAT_URL = "https://t.me/+GUrrAxu90tk2NWY1"

# -------------------- TELEGRAM --------------------


def send_to_telegram(text):
    retries = 3
    delay = 1

    buttons = {
        "inline_keyboard": [
            [
                {"text": "☎️ Numbers", "url": CHANNEL_URL},
                {"text": "🖥️ Developer", "url": DEV_URL}
            ],
            [
                {"text": "🤝 Support Chat", "url": CHAT_URL},
                
            
            ]
        ]
    }

    payload = {
        "chat_id": GROUP_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(buttons)
    }

    for attempt in range(retries):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data=payload,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Message sent to Telegram")
                return True
            else:
                print(f"⚠️ Telegram Error [{response.status_code}]: {response.text}")
        except Exception as e:
            print(f"❌ Telegram Send Failed (Attempt {attempt+1}/{retries}):", e)
        
        if attempt < retries - 1:
            time.sleep(delay)
    return False


# -------------------- FUNCTIONS --------------------

def send_ping(ws):
    global start_pinging
    while ws.keep_running:
        if start_pinging:
            try:
                ws.send("3")
                print("📡 Ping sent (3)")
            except Exception as e:
                print("❌ Failed to send ping:", e)
                break
        time.sleep(PING_INTERVAL)

def on_open(ws):
    global start_pinging
    start_pinging = False
    print("✅ WebSocket connected")

    time.sleep(0.5)
    ws.send("40/livesms")
    print("➡️ Sent: 40/livesms")

    time.sleep(0.5)
    ws.send(f'42/livesms,["auth","{AUTH_MESSAGE}"]')  # proper auth emit
    print("🔐 Sent auth token")

    threading.Thread(target=send_ping, args=(ws,), daemon=True).start()

def on_message(ws, message):
    global start_pinging
    if message == "3":
        print("✅ Pong received")
    elif message.startswith("40/livesms"):
        print("✅ Namespace joined — starting ping")
        start_pinging = True
    elif message.startswith("42/livesms,"):
        try:
            payload = message[len("42/livesms,"):]
            data = json.loads(payload)

            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], dict):
                sms = data[1]
                raw_msg = sms.get("message", "")
                originator = sms.get("originator", "Unknown")
                recipient = sms.get("recipient", "Unknown")
                country = sms.get("country_iso", "??").upper()

                import re
                otp_match = re.search(r'\b\d{3}[- ]?\d{3}\b|\b\d{6}\b', raw_msg)
                otp = otp_match.group(0) if otp_match else "N/A"

                masked = recipient[:5] + '⁕' * (len(recipient) - 9) + recipient[-4:]
                now = datetime.now().strftime("%H:%M:%S")
                service = "WhatsApp" if "whatsapp" in raw_msg.lower() else "Unknown"

                telegram_msg = (
    f"<blockquote>{country}🔔 <b><u>0TP Alert</u></b></blockquote>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    f"<blockquote>🌍 <b>Country:</b> <code>{country}</code></blockquote>\n"
    f"<blockquote>🔑 <b>OTP:</b> <code>{otp}</code></blockquote>\n"
    f"<blockquote>🕒 <b>Time:</b> <code>{now}</code></blockquote>\n"
    f"<blockquote>📢 <b>Service:</b> <code>{originator}</code></blockquote>\n"
    f"<blockquote>📱 <b>Number:</b> <code>{masked}</code></blockquote>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "<blockquote>💬 <b>Message:</b></blockquote>\n"
    f"<blockquote><pre>{html.escape(raw_msg)}</pre></blockquote>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "<blockquote><i>⚡ Delivered instantly via DDxOTP</i></blockquote>"
)




                send_to_telegram(telegram_msg)

            else:
                print("⚠️ Unexpected data format:", data)

        except Exception as e:
            print("❌ Error parsing message:", e)
            print("Raw message:", message)

def on_error(ws, error):
    print("❌ WebSocket error:", error)

def on_close(ws, code, msg):
    global start_pinging
    start_pinging = False
    print("🔌 WebSocket closed. Reconnecting in 1s...")
    time.sleep(1)
    start_ws_thread()  # Reconnect automatically

def connect():
    print("🔄 Connecting to IVASMS WebSocket...")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://ivasms.com",
        "Referer": "https://ivasms.com/",
        "Host": "ivasms.com"
    }

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        header=[f"{k}: {v}" for k, v in headers.items()]
    )

    ws.run_forever()

def start_ws_thread():
    t = threading.Thread(target=connect, daemon=True)
    t.start()

# -------------------- FLASK WEB SERVICE --------------------

app = Flask(__name__)

@app.route("/")
def root():
    return Response("Service is running", status=200)

@app.route("/health")
def health():
    return Response("OK", status=200)

# -------------------- START --------------------

if __name__ == "__main__":
    start_ws_thread()  # Start the WebSocket in background
    port = int(os.environ.get("PORT", 8080))  # Use PORT env variable if provided
    app.run(host="0.0.0.0", port=port, threaded=True)
