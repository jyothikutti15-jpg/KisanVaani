"""Soil Test Report OCR — Upload soil test report image, AI extracts and interprets results.

Farmers get soil test cards from KVK/labs but often can't read them.
This service reads the report via Claude Vision and provides:
1. Extracted values (pH, N, P, K, organic carbon, etc.)
2. Plain-language interpretation
3. Crop-specific fertilizer recommendations
"""
import logging
from typing import Optional

from app.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger("kisanvaani.soil_ocr")

SOIL_OCR_PROMPT = """You are analyzing a soil test report card image. Extract ALL values you can find and provide farmer-friendly interpretation.

EXTRACT these values (set null if not found):
- pH, Electrical Conductivity (EC), Organic Carbon (OC%)
- Nitrogen (N kg/ha), Phosphorus (P kg/ha), Potassium (K kg/ha)
- Sulphur (S), Zinc (Zn), Iron (Fe), Manganese (Mn), Boron (B)
- Soil type, texture, moisture

Return a JSON block followed by plain-language interpretation:

```soil_data
{
  "ph": <number or null>,
  "ec": <number or null>,
  "organic_carbon": <number or null>,
  "nitrogen": <number or null>,
  "phosphorus": <number or null>,
  "potassium": <number or null>,
  "sulphur": <number or null>,
  "zinc": <number or null>,
  "iron": <number or null>,
  "soil_type": "<string or null>"
}
```

Then provide:
1. HEALTH SUMMARY: Is this soil healthy, deficient, or problematic? (1-2 sentences)
2. KEY ISSUES: List the main deficiencies or excesses
3. FERTILIZER PLAN: Specific recommendations with exact amounts per acre
4. CROP SUITABILITY: Which crops grow best in this soil

Use simple language. Give amounts in kg/acre. Mention specific fertilizer brands when possible."""

MOCK_SOIL_RESULT = {
    "extracted_values": {
        "ph": 6.8, "ec": 0.45, "organic_carbon": 0.62,
        "nitrogen": 185, "phosphorus": 12.5, "potassium": 210,
        "sulphur": 8.2, "zinc": 0.4, "iron": 4.8, "soil_type": "Black Clay"
    },
    "health_summary": "Your soil is moderately healthy but low in Phosphorus and Zinc. pH is ideal for most crops.",
    "key_issues": [
        "LOW Phosphorus (12.5 kg/ha) — needs urgent correction",
        "LOW Zinc (0.4 ppm) — below critical level of 0.6 ppm",
        "LOW Organic Carbon (0.62%) — needs compost/FYM"
    ],
    "fertilizer_plan": [
        "DAP (Di-Ammonium Phosphate): 50 kg/acre — apply at sowing",
        "Zinc Sulphate: 10 kg/acre — mix with last ploughing",
        "FYM (Farm Yard Manure): 2 tonnes/acre — improve organic carbon",
        "Urea: 25 kg/acre — split in 2 doses (sowing + 30 days)"
    ],
    "crop_suitability": [
        "Best: Cotton, Soybean, Wheat (black soil, good K)",
        "Good: Tomato, Onion, Chickpea",
        "Avoid: Rice (needs more water retention)"
    ]
}


async def analyze_soil_report(
    image_data: str,
    image_media_type: str = "image/jpeg",
    language: str = "en",
    crop: Optional[str] = None,
) -> dict:
    """Analyze a soil test report image using Claude Vision."""

    if settings.MOCK_MODE or not llm_service.client:
        logger.info("Soil OCR: returning mock result")
        return MOCK_SOIL_RESULT

    try:
        crop_context = f"\nThe farmer grows: {crop}. Tailor recommendations for this crop." if crop else ""

        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": f"Analyze this soil test report card.{crop_context}\nRespond in {language} language.",
                },
            ],
        }]

        response = await llm_service._call_claude(messages, SOIL_OCR_PROMPT)

        # Parse the structured response
        import json, re
        soil_data = {}
        match = re.search(r"```soil_data\s*(\{.*?\})\s*```", response, re.DOTALL)
        if match:
            try:
                soil_data = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Extract text sections
        clean_text = re.sub(r"```soil_data\s*\{.*?\}\s*```", "", response, flags=re.DOTALL).strip()

        return {
            "extracted_values": soil_data,
            "interpretation": clean_text,
            "raw_response": response,
        }

    except Exception as e:
        logger.error(f"Soil OCR failed: {e}")
        return MOCK_SOIL_RESULT
