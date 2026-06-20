from fastapi import FastAPI, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

model = ChatGroq(
    model_name="llama-3.1-8b-instant"
)

app = FastAPI()


@app.post("/chat")
async def chat(SpeechResult: str = Form("")):
    user_text = SpeechResult

    messages = [
    {
        "role": "system",
        "content": """
You are a helpful VOICE ASSISTANT for SUMMIT COLLEGE.

Location: Shantinagar, Kathmandu

Programs:
- +2 Science
- +2 Management
- Bachelor: CSIT, BCA, BBM

Facilities:
- Lab
- Parking
- Futsal
- Cricket net
- AC classrooms

Rules:
- Answer ONLY college-related questions
- Keep answers VERY short (1–2 sentences)
- If unsure say: Please contact the college administration office.
"""
    },
    {
        "role": "user",
        "content": user_text
    }
]

    ai_response = model.invoke(messages)

    answer = ai_response.content

    response = VoiceResponse()
    response.say(answer, voice="alice")

    gather = Gather(
        input="speech",
        action="/chat",
        method="POST"
    )

    gather.say("Do you have another question?")
    response.append(gather)

    return Response(
        content=str(response),
        media_type="text/xml"
    )