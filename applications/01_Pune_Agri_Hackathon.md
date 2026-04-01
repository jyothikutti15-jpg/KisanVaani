# Pune Agri Hackathon 2026 — KisanVaani Submission

**Website**: https://www.puneagrihackathon.com/
**Category**: Artificial Intelligence in Agriculture
**Prize**: Rs 25 Lakh (1st) / Rs 15 Lakh (2nd)
**Deadline**: March 31, 2026
**Finale**: May 15-17, 2026, College of Agriculture, Pune

---

## 1. Problem Description

India has 150 million smallholder farmers, yet 86% have low digital literacy and most lack smartphones. Every existing agri-tech solution — mobile apps, WhatsApp chatbots, web platforms — requires a smartphone with internet access, effectively excluding the farmers who need help the most.

The consequences are devastating:
- Preventable crop losses worth Rs 90,000+ crore annually because farmers cannot identify pests and diseases in time
- Crores of eligible farmers don't know about PM-KISAN, PMFBY, or Kisan Credit Card — or don't know how to apply
- Without real-time mandi price information, farmers sell at 20-40% below peak prices
- Farmers in Vidarbha growing cotton on black soil need different advice than farmers in Telangana growing rice on red soil — but generic helplines give one-size-fits-all answers
- Farmers learn about pest outbreaks and weather events only after damage is done

Even the government's Bharat-VISTAAR platform (launched February 2026) operates only in Hindi and English in Phase-1, has no farmer memory, cannot analyze crop photos, cannot predict yields, doesn't track expenses, and doesn't proactively alert farmers before problems strike.

The core gap: No solution exists that combines voice-first access (works on basic phones), personalized farmer memory, AI photo diagnosis, crop diary with auto-reminders, expense tracking, live weather, yield prediction, loan guidance, and multi-country support in a single platform.

## 2. Concept Statement

KisanVaani ("Farmer's Voice") is the world's first comprehensive AI farm advisor combining voice-first interaction, personalized farmer memory, and 20+ agricultural features in one platform.

**How it works:** Farmer dials a phone number → speaks in Hindi, Telugu, Tamil, Swahili, or English → AI responds with specific, actionable advice in the same language. Works on any Rs 500 feature phone.

**20+ features include:** Farmer Memory (remembers name, crops, soil, past problems), Photo Diagnosis (Claude Vision AI), Crop Diary with auto-reminders, Voice Expense Tracker, Live Weather (Open-Meteo), Yield Predictor, Loan Calculator (KCC/PM-KISAN/PMFBY), KVK Locator, Mandi Price Comparison, Proactive Alerts (weather, pest, price, scheme), Community Intelligence (trending pest outbreaks), Pest Gallery with 8 pests, Multi-Country support (India, Kenya, Nigeria, Ethiopia), Admin Dashboard, and Farmer PDF Report.

15 of these features exist in NO competing product — including Bharat-VISTAAR.

## 3. Methodology

**Architecture:** `Farmer speaks → Speech-to-Text → Claude AI + Farming Context → Text-to-Speech → Farmer hears answer`

**Technology:** Python FastAPI backend, React+TypeScript frontend, Claude AI (Anthropic) for reasoning + Vision for photos, Open-Meteo for live weather, Twilio for phone calls, Browser Web Speech API for STT/TTS.

**AI Pipeline:** (1) Farmer profile lookup with memory, (2) Context enrichment with season/prices/schemes/weather, (3) Claude AI generates personalized advice in farmer's language, (4) Auto-detect expenses from speech, (5) Deliver response via voice.

**Crop Diary System:** When farmer says "I planted wheat" → system logs the entry and auto-generates 5 smart reminders (irrigation Day 21, fertilizer Day 42, pest check Day 60, pre-flowering irrigation Day 90, harvest Day 120).

**Photo Diagnosis:** Farmer uploads crop image → Claude Vision analyzes leaf color, spot patterns, insect presence → returns disease name + organic and chemical treatment with exact dosages.

All components are built, integrated, and tested with real AI — not mockups or wireframes.

## 4. Deliverables

20+ features built and tested:
1. Voice AI in 5 languages (Hindi, Telugu, Tamil, Swahili, English) — tested with real Claude AI
2. Farmer Memory — persistent profiles; AI greets by name, references crops/soil/village
3. Photo Diagnosis — Claude Vision correctly identified Early Blight on tomato
4. Crop Diary + 10 auto-generated reminders from 2 planting events
5. Expense Tracker — 4 expenses auto-detected totaling Rs 15,000 (seeds, pesticide, labor, irrigation)
6. Live Weather — real Open-Meteo data for Sehore (24.9°C), Kakamega (18.4°C), Kano (30.6°C)
7. Yield Predictor — Wheat 5 acres: 112.5 quintals (+15% irrigation, +10% black soil)
8. Loan Calculator — 4 India schemes + Kenya AFC + Nigeria ABP, all with documents and apply locations
9. KVK Locator — 3 KVKs in MP, 2 in Kenya, 2 in Nigeria with phone numbers
10. Mandi Prices — Soybean Rs 4,892/quintal with AI sell/hold recommendation
11. 8 pests in gallery with symptoms, treatments, reference images
12. 5 proactive alerts across 3 countries (weather, pest, price, scheme)
13. 5 community insights with 4 trending
14. Farmer onboarding with personalized tips
15. PDF farmer report (profile + expenses + diary + reminders)
16. Multi-country: India, Kenya, Nigeria, Ethiopia
17. Twilio phone call handling (tested IVR + speech processing)
18. Admin dashboard with charts
19. Call history with language filters (20+ calls, 5 languages)
20. Web demo with phone simulator

## 5. Feasibility (Technical & Economic)

**Technical:** Fully built and tested — 50+ API endpoints all passing, real Claude AI in 5 languages, live weather data, zero TypeScript errors, production build successful. Cost per call: Rs 3-5 (Claude ~Rs 2 + Twilio ~Rs 2). Infrastructure: Rs 2,000-5,000/month cloud server.

**Economic:** At Rs 96/farmer/year operating cost vs Rs 150/farmer/year govt contract = profitable at 50,000 farmers. Compare: one KVK visit costs Rs 200-500 in travel alone. Revenue streams: Government B2G contracts (Rs 1-10 Cr), telecom partnerships (Rs 50L-1 Cr), agri-input advertising, NGO/donor grants ($100K-1M).

Break-even: 50,000 farmers. India alone has 150 million potential users.

## 6. Scalability

**Languages:** 5 now → 15 Indian + 10 African within 12 months. Claude AI natively supports 100+ languages; adding a new language = updating one config file, zero code changes.

**Geography:** 4 countries now (India, Kenya, Nigeria, Ethiopia). Adding a new country = one JSON file with local seasons, crops, prices, schemes. Target: 10 countries in 18 months.

**Users:** Current architecture handles 10,000 farmers. PostgreSQL upgrade for 100,000. Horizontal cloud scaling for 1,000,000+. Claude AI handles unlimited concurrent requests.

**Impact at scale:** 10,000 farmers (pilot) → Rs 5-10 Cr crop loss prevented. 1 million farmers (Year 3) → Rs 500-1000 Cr. Every farmer getting timely pest advice saves Rs 5,000-50,000 per season.
