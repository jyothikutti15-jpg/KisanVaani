# KisanVaani — Pune Agri Hackathon 2026 Submission

## 1. Problem Description

India has 150 million smallholder farmers, yet 86% have low digital literacy and most lack smartphones. Every existing agri-tech solution — mobile apps, WhatsApp chatbots, web platforms — requires a smartphone with internet access, effectively excluding the farmers who need help the most.

The consequences are devastating:
- **Preventable crop losses worth Rs 90,000+ crore annually** because farmers cannot identify pests and diseases in time
- **Missed government benefits**: Crores of eligible farmers don't know about PM-KISAN, PMFBY, or Kisan Credit Card — or don't know how to apply
- **Poor market timing**: Without real-time mandi price information, farmers sell at 20-40% below peak prices
- **No personalized advice**: A farmer in Vidarbha growing cotton on black soil needs different advice than a farmer in Telangana growing rice on red soil — but generic helplines give one-size-fits-all answers
- **Zero proactive warnings**: Farmers learn about pest outbreaks and weather events only after damage is done

Even the government's Bharat-VISTAAR platform (launched February 2026) operates only in Hindi and English in Phase-1, has no farmer memory, cannot analyze crop photos, and doesn't proactively alert farmers before problems strike.

The core gap: **No solution exists that combines voice-first access (works on basic phones), personalized farmer memory, AI-powered photo diagnosis, proactive alerts, and multi-language support in a single platform.**

---

## 2. Concept Statement

**KisanVaani** ("Farmer's Voice") is a voice-first AI farm advisor that lets any farmer dial a phone number and get personalized, expert agricultural advice in their own language — using nothing more than a basic feature phone.

**How it works in 3 steps:**
1. **Farmer dials a number** from any phone (even a Rs 500 feature phone)
2. **Speaks their question** in Hindi, Telugu, Tamil, Swahili, or English — "Mere tamatar ke patte peele ho rahe hain, kya karoon?"
3. **AI responds with specific advice** in the same language — "Ramesh ji, yeh safed makhi ka hamla hai. Neem oil 5ml per liter paani mein milaakar patte ke neeche spray karein, har 3 din mein..."

**What makes KisanVaani unique — features no competitor offers:**

| Feature | KisanVaani | Bharat-VISTAAR | Other Apps |
|---------|-----------|----------------|------------|
| Works on basic phone (no internet) | Yes | Yes | No |
| Remembers farmer's name, crops, soil, past problems | **Yes** | No | No |
| Photo diagnosis (upload crop image for AI analysis) | **Yes** | No | Some |
| Proactive alerts (warns BEFORE pest outbreaks, weather) | **Yes** | Basic | No |
| Voice expense tracker ("Maine 2000 rupye urea pe kharch kiye") | **Yes** | No | No |
| Community intelligence (trending pest outbreaks nearby) | **Yes** | No | No |
| Multi-country (India + Kenya + Nigeria + Ethiopia) | **Yes** | India only | 1 country |
| 5 languages working today | **Yes** | 2 (Phase-1) | 1-2 |

---

## 3. Methodology

### Technical Architecture

```
Farmer speaks → Speech-to-Text (Browser/Twilio) → Claude AI + Farming Knowledge → Text-to-Speech → Farmer hears answer
```

### Technology Stack
- **AI Engine**: Claude (Anthropic) — state-of-the-art large language model with Vision capability for photo analysis
- **Backend**: Python FastAPI + SQLite database
- **Voice (Phone)**: Twilio Voice API — handles real phone calls via IVR webhooks
- **Voice (Web Demo)**: Browser Web Speech API (free, built-in) for speech-to-text and speech synthesis
- **Frontend**: React + TypeScript + Tailwind CSS with Recharts for analytics dashboard

### AI Pipeline — How Each Query is Processed

**Step 1: Farmer Profile Lookup**
When a farmer calls, the system checks if this phone number has called before. If yes, it loads their complete profile — name, crops, soil type, land size, irrigation method, past problems, and last advice given.

**Step 2: Context Enrichment**
The AI query is enriched with real-time farming context:
- Current season (Kharif/Rabi/Zaid) and active crops
- Latest mandi prices for the farmer's region
- Active government schemes with eligibility criteria
- Any active pest outbreak alerts in the farmer's district
- The farmer's personal history and ongoing issues

**Step 3: Claude AI Reasoning**
Claude receives the farmer's question + enriched context + conversation history and generates a response that is:
- In the same language as the question
- Specific (exact dosages, not vague advice)
- Personalized (references farmer's crops, soil, past issues)
- Concise (80-150 words — optimized for voice delivery)

**Step 4: Expense Detection**
If the farmer mentions spending money ("Maine 3500 rupye beej pe kharch kiye"), the AI automatically extracts the expense category, amount, crop, and description — and logs it to the farmer's expense tracker.

**Step 5: Response Delivery**
The text response is converted to speech and delivered back via phone call or browser audio.

### Photo Diagnosis Flow
1. Farmer uploads a crop photo (via WhatsApp or web demo)
2. Image is sent to Claude Vision alongside the text description
3. AI analyzes leaf color, spot patterns, insect presence, wilting signs
4. Returns diagnosis with specific treatment steps

### Proactive Alert System
- Weather alerts sourced from IMD (India), NiMet (Nigeria), KMD (Kenya)
- Pest outbreak detection from aggregated farmer queries (community intelligence)
- Price spike/crash notifications from mandi data
- Government scheme deadline reminders
- Alerts filtered by farmer's country, region, and crops

### Development Approach
- **Built and tested with real AI** — not a mockup or wireframe
- **26 features tested end-to-end** with sample farmers across 4 countries
- **Real Claude AI responses** in Hindi, Telugu, Tamil, Swahili, and English

---

## 4. Deliverables

### Working Product (Built and Tested)
1. **Voice AI Engine** — Full pipeline: speech → AI reasoning → voice response in 5 languages
2. **Farmer Memory System** — Persistent profiles storing name, crops, soil, land, irrigation, past problems, active issues
3. **Photo Diagnosis** — Upload crop image for Claude Vision AI analysis + treatment recommendations
4. **Proactive Alert Dashboard** — Weather warnings, pest outbreaks, price spikes, scheme deadlines across 4 countries
5. **Voice Expense Tracker** — Auto-detects and logs farm expenses from natural voice ("Maine 3500 rupye beej pe kharch kiye" → category: seeds, amount: 3500, crop: cotton)
6. **Community Intelligence Feed** — Aggregated trending pest/disease patterns by region with farmer count
7. **Admin Analytics Dashboard** — Total calls, language breakdown, daily timeline charts, call history with language filters
8. **Multi-Country Knowledge Base** — Country-specific crop calendars, market prices, government schemes, extension services for India, Kenya, Nigeria, Ethiopia
9. **Phone Simulator Web Demo** — Browser-based demo with mic recording, phone UI, for investor/jury presentations
10. **Twilio Phone Integration** — Real phone call handling via IVR webhooks (farmer dials → speaks → gets AI response)

### Test Results Achieved
- **20 calls** across 13 sessions in **5 languages** with **4 countries**
- **4 expenses** auto-tracked totaling Rs 15,000 (seeds, pesticide, labor, irrigation)
- **5 proactive alerts** active (weather, pest outbreak, price spike, scheme deadline)
- **5 community insights** with trending pest data from 3 countries
- **Zero TypeScript errors**, clean frontend build

---

## 5. Feasibility (Technical & Economic)

### Technical Feasibility

**Already built and working:**
- The entire platform is functional — not a concept or wireframe
- Tested with real Claude AI producing accurate Hindi, Telugu, Tamil, Swahili, and English farming advice
- Photo diagnosis tested with Claude Vision — correctly identified early blight on tomato
- Expense detection tested — accurately extracted amounts, categories, and crops from Hindi voice input

**Infrastructure requirements:**
- Cloud server: Rs 2,000-5,000/month (AWS/GCP basic instance)
- Anthropic API: ~Rs 1-3 per farmer query (Claude Sonnet)
- Twilio: Rs 1-2 per minute for phone calls
- Total per farmer call: **Rs 3-5** (very low)

**Technology maturity:**
- Claude AI: Production-ready, used by millions globally
- Twilio: Industry standard for voice, used by banks, hospitals
- FastAPI: Production-grade Python framework
- All components are battle-tested, not experimental

### Economic Feasibility

**Cost per farmer per year:**
- Average 2 calls/month × 12 months = 24 calls/year
- At Rs 4/call = **Rs 96/farmer/year** total cost
- Compare: One visit to KVK costs farmer Rs 200-500 in travel alone

**Revenue model:**
| Revenue Stream | Potential |
|----------------|-----------|
| Government contracts (per-farmer advisory fee) | Rs 100-200/farmer/year |
| Telecom partnerships (toll-free number sponsorship) | Rs 50L-1Cr/year |
| Agri-input company advertising ("Press 1 to order neem oil") | Rs 10-50/lead |
| NGO/donor funding (Gates Foundation, FAO, World Bank) | $100K-1M grants |

**Break-even**: At 50,000 farmers with government contract of Rs 150/farmer/year = Rs 75 lakh revenue vs Rs 48 lakh cost = **profitable at 50K farmers**.

---

## 6. Scalability

### Language Scalability
- **Current**: 5 languages (Hindi, Telugu, Tamil, Swahili, English)
- **Easy to add**: Claude AI natively supports 100+ languages. Adding Kannada, Marathi, Bengali, Gujarati, Punjabi requires only updating the language config file — no code changes
- **Target**: 15 Indian languages + 10 African languages within 12 months

### Geographic Scalability
- **Current**: India, Kenya, Nigeria, Ethiopia (with country-specific schemes, prices, extension services)
- **Architecture**: Country data is stored in a JSON config file. Adding a new country = adding one JSON entry with local seasons, crops, prices, schemes
- **Target**: 10 countries within 18 months (add Uganda, Tanzania, Ghana, Senegal, Bangladesh, Myanmar)

### User Scalability
- **10,000 farmers**: Single server, SQLite database — current architecture handles this
- **100,000 farmers**: Upgrade to PostgreSQL + Redis caching — 1 day of work
- **1,000,000+ farmers**: Horizontal scaling with load balancer + multiple API servers — standard cloud deployment
- Claude AI handles unlimited concurrent requests — no bottleneck

### Feature Scalability
- **Voice-based crop insurance claims**: Farmer describes damage → AI generates claim → auto-submits
- **Satellite imagery integration**: Detect crop stress from space → proactive call to farmer
- **Marketplace**: "You need neem oil — press 1 to order from nearest agri-shop"
- **Carbon credit tracking**: Log regenerative practices → help farmer earn carbon credits
- **Offline mode**: Edge AI on feature phones via USSD for zero-connectivity areas

### Partnership Scalability
- **State agriculture departments**: Deploy as official advisory service per district
- **FPOs (Farmer Producer Organizations)**: Bulk advisory for member farmers
- **Agricultural universities**: Research partnership for crop-specific advice
- **International**: FAO, CGIAR, World Bank agriculture programs

### Impact at Scale
| Scale | Farmers Reached | Potential Crop Loss Prevented |
|-------|----------------|-------------------------------|
| Pilot (6 months) | 10,000 | Rs 5-10 Crore |
| Year 1 | 100,000 | Rs 50-100 Crore |
| Year 3 | 1,000,000 | Rs 500-1000 Crore |
| Year 5 | 10,000,000 | Rs 5,000+ Crore |

**Every farmer who gets timely pest advice saves Rs 5,000-50,000 per season in prevented crop loss.** At scale, KisanVaani can prevent thousands of crores in agricultural losses annually.
