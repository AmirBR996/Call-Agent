from fastapi import FastAPI, Form
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv
import edge_tts
import asyncio
import uuid
import os
import logging
from rag import chat 

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

YOUR_DOMAIN = os.getenv("YOUR_DOMAIN") 

os.makedirs("/tmp/audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="/tmp/audio"), name="audio")

YOUR_DOMAIN = "https://f307-160-250-254-238.ngrok-free.app"

STATIC_AUDIO = {}

STATIC_PHRASES = {
    "welcome":  "नमस्ते! Summit College मा स्वागत छ। कृपया आफ्नो प्रश्न सोध्नुहोस्।",
    "fallback": "हामीले तपाईंको आवाज सुन्न सकेनौं। कृपया फेरि कल गर्नुहोस्।",
    "unclear":  "माफ गर्नुस्, मैले बुझिनँ। कृपया फेरि भन्नुहोस्।",
    "followup": "के तपाईंको अर्को प्रश्न छ?",
    "bye":      "धन्यवाद! Summit College मा कल गर्नुभएकोमा धन्यवाद।",
}


async def text_to_nepali_speech(text: str, filename: str = None) -> str:
    filename = filename or f"{uuid.uuid4()}.mp3"
    filepath = f"/tmp/audio/{filename}"
    communicate = edge_tts.Communicate(text=text, voice="ne-NP-HemkalaNeural")
    await communicate.save(filepath)
    return f"{YOUR_DOMAIN}/audio/{filename}"


@app.on_event("startup")
async def pregenerate_static_audio():
    logger.info("Pre-generating static audio files...")
    tasks = {
        key: text_to_nepali_speech(text, filename=f"static_{key}.mp3")
        for key, text in STATIC_PHRASES.items()
    }
    results = await asyncio.gather(*tasks.values())
    for key, url in zip(tasks.keys(), results):
        STATIC_AUDIO[key] = url
    logger.info("Static audio ready: %s", STATIC_AUDIO)


@app.post("/incoming")
async def incoming():
    logger.info("Incoming call")
    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="/process",          
        method="POST",
        language="ne-NP",
        speechTimeout="auto",
        speechModel="phone_call"
    )
    gather.play(STATIC_AUDIO["welcome"])
    response.append(gather)
    response.play(STATIC_AUDIO["fallback"])
    response.hangup()              

    return Response(content=str(response), media_type="text/xml")


@app.post("/process")                
async def process(SpeechResult: str = Form("")):   
    logger.info("SpeechResult: %s", SpeechResult)
    response = VoiceResponse()

    if not SpeechResult.strip():
        gather = Gather(
            input="speech",
            action="/process",
            method="POST",
            language="ne-NP",
            speechTimeout="auto",
            speechModel="phone_call"
        )
        gather.play(STATIC_AUDIO["unclear"])
        response.append(gather)
        response.play(STATIC_AUDIO["bye"])
        response.hangup()
        return Response(content=str(response), media_type="text/xml")

    try:
        answer = chat(SpeechResult)  
        logger.info("RAG answer: %s", answer)
    except Exception as e:
        logger.error("RAG error: %s", e)
        answer = "कृपया कलेज प्रशासन कार्यालयमा सम्पर्क गर्नुहोस्।"

    try:
        answer_url = await text_to_nepali_speech(answer)
        response.play(answer_url)
    except Exception as e:
        logger.error("TTS error: %s", e)
        response.say(answer, voice="Polly.Aditi", language="hi-IN")

    gather = Gather(
        input="speech",
        action="/process",
        method="POST",
        language="ne-NP",
        speechTimeout="auto",
        speechModel="phone_call"
    )
    gather.play(STATIC_AUDIO["followup"])
    response.append(gather)

    response.play(STATIC_AUDIO["bye"])
    response.hangup()

    return Response(content=str(response), media_type="text/xml")