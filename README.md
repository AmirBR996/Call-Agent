# Call Agent

FastAPI-based voice assistant for New Summit College. The app answers college-related questions over a Twilio voice call, uses a FAISS-backed retrieval layer over `data.txt`, and speaks responses with Nepali text-to-speech.

## How It Works

1. Twilio sends an incoming call to the `/incoming` webhook.
2. The app plays a Nepali welcome prompt and listens for speech.
3. The transcribed question is sent to the RAG chain in `rag.py`.
4. A short Nepali answer is generated and returned as XML TwiML.
5. Responses are converted to MP3 audio and served from `/audio`.

## Project Structure

- `main.py` - FastAPI app, Twilio webhook handlers, and text-to-speech flow.
- `rag.py` - FAISS retrieval and Groq-powered chat chain.
- `data.txt` - Knowledge base for New Summit College.
- `faiss_index/` - Saved FAISS index for faster startup.
- `requirement.txt` - Python dependencies.

## Requirements

- Python 3.10 or newer
- A Twilio phone number with voice webhook support
- A Groq API key
- A public HTTPS URL for webhook callbacks

## Environment Variables

Create a `.env` file in the project root with at least:

```env
YOUR_DOMAIN=https://your-public-domain.example
GROQ_API_KEY=your_groq_api_key
```

If you deploy behind a tunnel or reverse proxy, `YOUR_DOMAIN` must be reachable by Twilio so it can fetch generated audio files.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
```

## Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The app will serve:

- `POST /incoming` for inbound call handling
- `POST /process` for speech recognition results
- `/audio/*` for generated MP3 files

## Twilio Setup

Configure your Twilio number's Voice webhook to point to:

```text
https://your-public-domain.example/incoming
```

Use HTTPS, because Twilio requires secure webhook endpoints for production use.

## RAG Index

The first run will load `faiss_index/` if it exists. If the index is missing, the app builds it from `data.txt` and saves it back to `faiss_index/`.

## Notes

- Answers are intentionally short and in Nepali.
- The assistant is restricted to college-related questions.
- If TTS generation fails, the app falls back to spoken text via Twilio.