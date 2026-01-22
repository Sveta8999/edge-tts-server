#!/usr/bin/env python3
"""
Edge TTS Server для PythonAnywhere (Flask версия)
"""

import asyncio
import edge_tts
from flask import Flask, request, jsonify, Response

# Русские голоса Microsoft Edge
VOICES = {
    "dmitry": "ru-RU-DmitryNeural",
    "svetlana": "ru-RU-SvetlanaNeural",
}

DEFAULT_VOICE = "svetlana"

app = Flask(__name__)

def run_async(coro):
    """Запускает асинхронную функцию в синхронном контексте"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def synthesize_speech(text, voice_key):
    """Генерирует аудио через Edge TTS"""
    voice = VOICES.get(voice_key, VOICES[DEFAULT_VOICE])
    communicate = edge_tts.Communicate(text, voice)
    
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    
    return audio_data

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Edge TTS Server",
        "voices": VOICES
    })

@app.route("/voices", methods=["GET"])
def list_voices():
    return jsonify({
        "voices": VOICES,
        "default": DEFAULT_VOICE
    })

@app.route("/synthesize", methods=["POST"])
def synthesize():
    try:
        data = request.get_json()
        text = data.get("text", "")
        voice = data.get("voice", DEFAULT_VOICE)
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        print(f"🎤 Озвучка: '{text[:50]}...' голосом {VOICES.get(voice, VOICES[DEFAULT_VOICE])}")
        
        # Генерируем аудио
        audio_data = run_async(synthesize_speech(text, voice))
        
        if not audio_data:
            return jsonify({"error": "No audio generated"}), 500
        
        print(f"✅ Сгенерировано {len(audio_data)} байт аудио")
        
        return Response(
            audio_data,
            mimetype="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

# Для PythonAnywhere WSGI
application = app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5050))
    print(f"🚀 Edge TTS Server запускается на порту {port}...")
    app.run(host="0.0.0.0", port=port)
