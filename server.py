#!/usr/bin/env python3
"""
Edge TTS Server - бесплатная озвучка с нейронными голосами Microsoft
Запуск: python server.py
"""

import asyncio
import edge_tts
from aiohttp import web
import os

# Русские голоса Microsoft Edge (нейронные, высокое качество)
VOICES = {
    "dmitry": "ru-RU-DmitryNeural",    # Мужской
    "svetlana": "ru-RU-SvetlanaNeural", # Женский
}

DEFAULT_VOICE = "svetlana"  # Можно поменять на "dmitry"

async def synthesize(request):
    """Озвучивает текст и возвращает MP3"""
    try:
        # Получаем текст из запроса
        data = await request.json()
        text = data.get("text", "")
        voice_key = data.get("voice", DEFAULT_VOICE)
        
        if not text:
            return web.json_response({"error": "No text provided"}, status=400)
        
        # Выбираем голос
        voice = VOICES.get(voice_key, VOICES[DEFAULT_VOICE])
        
        print(f"🎤 Озвучка: '{text[:50]}...' голосом {voice}")
        
        # Генерируем аудио через Edge TTS
        communicate = edge_tts.Communicate(text, voice)
        
        # Собираем аудио данные
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        if not audio_data:
            return web.json_response({"error": "No audio generated"}, status=500)
        
        print(f"✅ Сгенерировано {len(audio_data)} байт аудио")
        
        # Возвращаем MP3
        return web.Response(
            body=audio_data,
            content_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def list_voices(request):
    """Список доступных голосов"""
    return web.json_response({
        "voices": VOICES,
        "default": DEFAULT_VOICE
    })

async def health(request):
    """Проверка здоровья сервера"""
    return web.json_response({"status": "ok", "service": "Edge TTS Server"})

def create_app():
    app = web.Application()
    app.router.add_post("/synthesize", synthesize)
    app.router.add_get("/voices", list_voices)
    app.router.add_get("/health", health)
    return app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5050))
    
    print("🚀 Edge TTS Server запускается...")
    print(f"📍 Адрес: http://0.0.0.0:{port}")
    print("🎙️ Голоса: Светлана (женский), Дмитрий (мужской)")
    print("")
    
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port)
