from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.llm_service import llm_service
from app.services.tts_service import tts_service
from app.services.voice_pipeline import log_call

router = APIRouter(prefix="/api/twilio", tags=["twilio"])


@router.post("/incoming")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio phone call with IVR greeting."""
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        KisanVaani mein aapka swagat hai. Kripya apna sawaal Hindi mein poochiye.
        For English, press 1.
    </Say>
    <Gather input="speech" action="/api/twilio/process-speech"
            language="hi-IN" speechTimeout="auto"
            speechModel="experimental_conversations">
        <Say voice="Polly.Aditi" language="hi-IN">
            Apna sawaal poochiye.
        </Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">
        Koi jawab nahi mila. Kripya dubara call karein. Dhanyavaad.
    </Say>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/process-speech")
async def process_speech(request: Request, db: Session = Depends(get_db)):
    """Process farmer's spoken question from Twilio."""
    form = await request.form()
    speech_result = form.get("SpeechResult", "")
    call_sid = form.get("CallSid", "unknown")
    caller = form.get("From", "")

    if not speech_result:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Mujhe aapka sawaal samajh nahi aaya. Kripya dubara bolein.
    </Say>
    <Gather input="speech" action="/api/twilio/process-speech"
            language="hi-IN" speechTimeout="auto">
        <Say voice="Polly.Aditi" language="hi-IN">Apna sawaal poochiye.</Say>
    </Gather>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Get AI response
    response_text = await llm_service.advise(
        question=speech_result,
        language="hi",
        history=[],
    )

    # Log the call
    log_call(db, call_sid, "phone", speech_result, response_text, "hi", phone=caller)

    # Respond with TTS via Twilio's Say (simpler than hosting audio)
    # Escape XML special characters
    safe_response = response_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{safe_response}</Say>
    <Gather input="speech" action="/api/twilio/process-speech"
            language="hi-IN" speechTimeout="auto">
        <Say voice="Polly.Aditi" language="hi-IN">
            Kya aapka koi aur sawaal hai?
        </Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">
        Dhanyavaad. KisanVaani ka upyog karne ke liye shukriya.
    </Say>
</Response>"""
    return Response(content=twiml, media_type="application/xml")
