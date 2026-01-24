#!/usr/bin/env python3
"""
Edge TTS Server - бесплатная озвучка с нейронными голосами Microsoft
Автоопределение языка текста
Запуск: python server.py
"""

import asyncio
import edge_tts
from aiohttp import web
import os
import re

# Голоса по языкам (нейронные, высокое качество)
LANGUAGE_VOICES = {
    "ru": "ru-RU-SvetlanaNeural",      # Русский - Светлана
    "en": "en-US-JennyNeural",         # Английский - Jenny
    "de": "de-DE-KatjaNeural",         # Немецкий - Katja
    "es": "es-ES-ElviraNeural",        # Испанский - Elvira
    "it": "it-IT-ElsaNeural",          # Итальянский - Elsa
    "fr": "fr-FR-DeniseNeural",        # Французский - Denise
    "pt": "pt-BR-FranciscaNeural",     # Португальский - Francisca
    "tr": "tr-TR-EmelNeural",          # Турецкий - Emel
    "pl": "pl-PL-ZofiaNeural",         # Польский - Zofia
    "nl": "nl-NL-ColetteNeural",       # Нидерландский - Colette
    "ja": "ja-JP-NanamiNeural",        # Японский - Nanami
    "ko": "ko-KR-SunHiNeural",         # Корейский - SunHi
    "zh": "zh-CN-XiaoxiaoNeural",      # Китайский - Xiaoxiao
    "ar": "ar-SA-ZariyahNeural",       # Арабский - Zariyah
    "hi": "hi-IN-SwaraNeural",         # Хинди - Swara
}

# Мужские голоса (альтернатива)
MALE_VOICES = {
    "ru": "ru-RU-DmitryNeural",
    "en": "en-US-GuyNeural",
    "de": "de-DE-ConradNeural",
    "es": "es-ES-AlvaroNeural",
    "it": "it-IT-DiegoNeural",
    "fr": "fr-FR-HenriNeural",
    "tr": "tr-TR-AhmetNeural",
}

DEFAULT_LANG = "ru"

# Unicode диапазоны для определения языка
LANG_PATTERNS = {
    "ru": re.compile(r'[а-яёА-ЯЁ]'),
    "en": re.compile(r'[a-zA-Z]'),
    "de": re.compile(r'[äöüßÄÖÜ]'),
    "es": re.compile(r'[ñáéíóúüÑÁÉÍÓÚÜ¿¡]'),
    "it": re.compile(r'[àèéìíîòóùúÀÈÉÌÍÎÒÓÙÚ]'),
    "fr": re.compile(r'[àâæçéèêëïîôœùûüÿÀÂÆÇÉÈÊËÏÎÔŒÙÛÜŸ]'),
    "pt": re.compile(r'[ãõáàâéêíóôúçÃÕÁÀÂÉÊÍÓÔÚÇ]'),
    "tr": re.compile(r'[şğıİçöüŞĞÇÖÜ]'),
    "pl": re.compile(r'[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]'),
    "nl": re.compile(r'[ïéèëüöäĳÏÉÈËÜÖÄĲ]'),
    "ja": re.compile(r'[\u3040-\u309F\u30A0-\u30FF]'),  # Hiragana + Katakana
    "ko": re.compile(r'[\uAC00-\uD7AF\u1100-\u11FF]'),  # Hangul
    "zh": re.compile(r'[\u4E00-\u9FFF]'),  # CJK
    "ar": re.compile(r'[\u0600-\u06FF]'),  # Arabic
    "hi": re.compile(r'[\u0900-\u097F]'),  # Devanagari
}

def detect_language(text: str) -> str:
    """Определяет язык текста по характерным символам"""
    if not text:
        return DEFAULT_LANG
    
    # Подсчитываем символы каждого языка
    lang_scores = {}
    
    for lang, pattern in LANG_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            lang_scores[lang] = len(matches)
    
    if not lang_scores:
        return DEFAULT_LANG
    
    # Приоритет для явных языков (не латиница)
    # Если есть кириллица - русский
    if "ru" in lang_scores and lang_scores["ru"] >= 2:
        return "ru"
    
    # Специфичные символы имеют приоритет над латиницей
    priority_langs = ["ja", "ko", "zh", "ar", "hi", "tr", "pl", "de", "es", "it", "fr", "pt", "nl"]
    for lang in priority_langs:
        if lang in lang_scores and lang_scores[lang] >= 1:
            return lang
    
    # Если только латиница - английский
    if "en" in lang_scores:
        return "en"
    
    return DEFAULT_LANG

async def synthesize(request):
    """Озвучивает текст и возвращает MP3"""
    try:
        # Получаем текст из запроса
        data = await request.json()
        text = data.get("text", "")
        explicit_lang = data.get("lang")  # Явно указанный язык
        use_male = data.get("male", False)  # Мужской голос
        
        if not text:
            return web.json_response({"error": "No text provided"}, status=400)
        
        # Определяем язык
        if explicit_lang and explicit_lang in LANGUAGE_VOICES:
            lang = explicit_lang
        else:
            lang = detect_language(text)
        
        # Выбираем голос
        if use_male and lang in MALE_VOICES:
            voice = MALE_VOICES[lang]
        else:
            voice = LANGUAGE_VOICES.get(lang, LANGUAGE_VOICES[DEFAULT_LANG])
        
        # ⚡ Скорость речи (чуть быстрее для отзывчивости)
        rate = data.get("rate", "+10%")  # +10% быстрее по умолчанию
        
        print(f"🎤 Озвучка [{lang}]: '{text[:50]}...' голосом {voice}")
        
        # Генерируем аудио через Edge TTS
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        
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
    """Список доступных голосов по языкам"""
    return web.json_response({
        "voices": LANGUAGE_VOICES,
        "male_voices": MALE_VOICES,
        "supported_languages": list(LANGUAGE_VOICES.keys()),
        "default_lang": DEFAULT_LANG
    })

async def health(request):
    """Проверка здоровья сервера"""
    return web.json_response({
        "status": "ok", 
        "service": "Edge TTS Server",
        "languages": len(LANGUAGE_VOICES)
    })

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
    print(f"🌍 Языки: {', '.join(LANGUAGE_VOICES.keys())}")
    print("🔍 Автоопределение языка текста")
    print("")
    
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port)
