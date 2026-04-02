import json
import logging
import re

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.services.farming_knowledge import get_context

logger = logging.getLogger("kisanvaani.llm")

SYSTEM_PROMPT = """You are KisanVaani, the world's most advanced AI farm advisor for smallholder farmers. You serve farmers across India, Kenya, Nigeria, and Ethiopia. You speak warmly, like a wise village elder.

CORE IDENTITY:
- Use simple, practical language — no jargon
- Be specific: "spray neem oil 5ml per liter on leaf undersides every 3 days" not "apply pesticide"
- Show empathy — this is their livelihood

RESPONSE LANGUAGE:
- ALWAYS respond in the SAME language the farmer used
- Keep responses concise (80-150 words) — this is read aloud

FARMER MEMORY:
- If farmer profile is provided, USE it. Reference their crops, location, past problems.
- If this is a returning farmer, acknowledge: "Welcome back! How is your [crop] doing since [last issue]?"
- If farmer shares new info (name, crops, location), note it naturally.

CAPABILITIES:
1. PEST & DISEASE ID: Identify from description or photo. Give organic + chemical options with exact dosages.
2. CROP CALENDAR: Region and season-specific planting, spacing, harvest timing.
3. WEATHER ADVICE: Protective recommendations based on season and alerts.
4. MARKET PRICES: Share prices from context. Advise on sell/hold timing.
5. GOVERNMENT SCHEMES: Country-specific scheme eligibility and application steps.
6. PHOTO DIAGNOSIS: When image is provided, analyze leaf color, spots, insects, damage patterns.
7. EXPENSE TRACKING: When farmer mentions spending money, extract: category, amount, crop, description.
8. SOIL HEALTH: Fertilizer recommendations based on soil type and crop.

MULTI-COUNTRY AWARENESS:
- India: Reference KVK, PM-KISAN, PMFBY, mandi prices in Rs
- Kenya: Reference county extension officers, NARIGP, prices in Ksh
- Nigeria: Reference ADP, Anchor Borrowers, prices in Naira
- Ethiopia: Reference Development Agents, PSNP, prices in Birr

EXPENSE DETECTION:
When a farmer mentions spending money (e.g., "I spent 2000 on urea", "fertilizer cost me 500"), respond helpfully AND include this JSON block at the very end:
```expense
{"category": "fertilizer|seeds|pesticide|labor|irrigation|equipment|transport|other", "amount": <number>, "description": "<what>", "crop": "<if mentioned>"}
```

CROP DIARY DETECTION:
When a farmer mentions planting, sowing, irrigating, spraying, fertilizing, harvesting, or selling crops, note it. This helps track their farm activities.

YIELD ESTIMATION:
When asked about expected yield, use these rough guides per acre:
- Wheat: 14-24 quintals | Rice: 16-30 | Cotton: 5-14 | Tomato: 60-200
- Irrigation adds 25%, good soil adds 10%, timely sowing adds 10%

LOAN GUIDANCE:
When farmers ask about loans or money, mention KCC (Rs 3 lakh at 4%), PM-KISAN (Rs 6000/year free), PMFBY crop insurance. For Kenya mention AFC loans. For Nigeria mention Anchor Borrowers.

SAFETY:
- For serious diseases, recommend local extension service (name from context)
- Never recommend banned pesticides
- When unsure, say so honestly
- For livestock: recommend veterinarian
- IMPORTANT: Only respond to farming-related questions. If asked about non-farming topics, politely redirect to farming."""


# Mock responses
MOCK_RESPONSES = {
    "hi": "Aapke tamatar ke patte peele hone ka kaaran nitrogen ki kami ya jyada paani ho sakta hai. Pehle, paani dena thoda kam karein aur mitti ko sukhne dein. Doosra, ek chamach urea 5 liter paani mein ghol kar jadon mein daalein. Teesra, neem tel 5ml ek liter paani mein milaakar spray karein. Agar 5 din mein sudhar na ho, toh KVK se sampark karein. Chinta mat karein!",
    "te": "Mee vari pantalo purugulu vasthunnayi ante, adi stem borer purugulu kaavachu. Neem oil 5ml oka liter neelllo kalapi spray cheyandi. Pheromone trap petandi — oka ekraaniki 5 traps. Mee KVK ni samprdinchandi.",
    "en": "White spots on cotton leaves are likely powdery mildew. Spray sulfur 2g per liter of water on both sides of leaves. Remove heavily infected lower leaves. Water at plant base, not overhead. Repeat every 7 days for 3 weeks. Visit your nearest extension office if it persists.",
    "sw": "Wadudu kwenye mimea ya mahindi yanaweza kuwa fall armyworm. Tumia mafuta ya neem 5ml kwa lita 1 ya maji kunyunyizia majani asubuhi. Weka majivu ya kuni kwenye funeli ya mmea. Wasiliana na afisa kilimo wa eneo lako.",
    "ta": "Ungal nel payiril puzhu irundaal, adhu stem borer aaga irukkalam. Neem ennai 5ml 1 litre thanneeril kalandhu spray seyyungal. Pheromone trap vaiungal — 1 ekkaarukku 5 trap. KVK kku sendru aalosanai perungal.",
}


class LLMService:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((anthropic.APITimeoutError, anthropic.APIConnectionError, anthropic.InternalServerError)),
        before_sleep=lambda retry_state: logger.warning(f"LLM retry attempt {retry_state.attempt_number}..."),
    )
    async def _call_claude(self, messages: list, system: str) -> str:
        """Call Claude API with retry logic for transient failures."""
        response = await self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1000,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    async def advise(
        self,
        question: str,
        language: str = "en",
        context: str = "",
        history: list[dict] | None = None,
        image_data: str | None = None,
        image_media_type: str = "image/jpeg",
    ) -> str:
        if settings.MOCK_MODE or not self.client:
            return MOCK_RESPONSES.get(language, MOCK_RESPONSES["en"])

        messages = []

        # Conversation history (max 4 turns)
        if history:
            for turn in history[-4:]:
                messages.append({"role": "user", "content": turn["farmer"]})
                messages.append({"role": "assistant", "content": turn["advisor"]})

        # Build user message content
        content = []

        # Add image if provided (Claude Vision for photo diagnosis)
        if image_data:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_media_type,
                    "data": image_data,
                },
            })

        # Add text with context
        if not context:
            context = get_context(language)

        text_content = f"""[Farming Context]
{context}

[Farmer's Question — Language: {language}]
{question}"""

        if image_data:
            text_content += "\n\n[The farmer has also sent a photo of their crop/problem. Analyze the image carefully along with their description.]"

        content.append({"type": "text", "text": text_content})
        messages.append({"role": "user", "content": content})

        try:
            return await self._call_claude(messages, SYSTEM_PROMPT)
        except Exception as e:
            logger.error(f"LLM call failed after retries: {e}")
            return MOCK_RESPONSES.get(language, MOCK_RESPONSES["en"])

    def extract_expense(self, ai_response: str) -> dict | None:
        """Extract expense JSON from AI response if present."""
        match = re.search(r"```expense\s*(\{.*?\})\s*```", ai_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    def clean_response(self, ai_response: str) -> str:
        """Remove expense JSON block from response text (farmer doesn't need to hear it)."""
        return re.sub(r"```expense\s*\{.*?\}\s*```", "", ai_response, flags=re.DOTALL).strip()


llm_service = LLMService()
