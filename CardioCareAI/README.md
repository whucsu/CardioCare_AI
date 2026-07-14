# CardioCare AI (Fresh Build)

## Cardiology Health Intelligence Platform — Port 5045

**This is a completely fresh build.** All previous CardioCare AI versions
(ports 5060 and earlier) have been discarded and are not referenced by this
build. Architecture is based on the working GynoCare AI v2 template.

## CRITICAL CARDIAC EMERGENCY DISCLAIMER

* **STEMI/Heart attack** (chest pain radiating to arm/jaw, sweating, breathlessness): 112/999/911 IMMEDIATELY
* **Cardiac arrest** (no pulse, unresponsive, not breathing normally): Start CPR + call for AED
* **Aortic dissection** (sudden tearing chest/back pain, unequal pulses): Emergency assessment
* **Stroke (FAST)**: Face drooping, Arm weakness, Speech difficulty, Time to call emergency services
* All content is AI-generated educational research only — NOT medical advice

## Quick Start (Windows)

1. Extract ZIP to any folder
2. Double-click **START\_CardioCare\_AI.bat**
3. Auto-installs everything (2-5 min first time)
4. Browser opens at **http://localhost:5045**
5. Accept disclaimer and begin

## Security — AES-256-GCM + Software Safety Hardening

* API keys AES-256-GCM encrypted client-side before localStorage
* PBKDF2 key derivation (100,000 iterations) from device fingerprint
* XSS protection: escapeHtml(), escapeFilename(), sanitizeAIResponse()
* Backend rate limiting (30 req/60s), input sanitisation/bounding, provider whitelist
* No hardcoded secrets — all API keys from environment or client-supplied at runtime
* Opaque, non-enumerable file and report identifiers (UUID-based)
* Opaque error handling — no internal stack traces or exception details returned to client

## 6 AI Providers (All Real API Calls)

|Provider|Model|Get Key|
|-|-|-|
|Claude (Anthropic)|claude-sonnet-4-20250514|console.anthropic.com|
|ChatGPT (OpenAI)|gpt-4o|platform.openai.com/api-keys|
|Gemini (Google)|gemini-2.0-flash|aistudio.google.com/apikey|
|Grok (xAI)|grok-2-latest|console.x.ai|
|DeepSeek|deepseek-chat|platform.deepseek.com/api\_keys|
|Mistral AI|mistral-large-latest|console.mistral.ai/api-keys|

## Ambiguity Resolver

Query 2-6 AIs simultaneously (parallel) — synthesised best answer generated automatically.
Click **⚡ Ambiguity Resolver** in the Chat panel.

## Sections (15 Panels)

* **Conditions** — 20+ dropdown (coronary, heart failure, arrhythmias, valvular, cardiomyopathy, vascular)
* **Coronary Artery Disease** — 3 tabs: Overview/Risk factors, Stable angina, ACS (STEMI/NSTEMI)
* **Heart Failure** — 4 tabs: Classification/Causes, Diagnosis, HFrEF four-pillar therapy, Rheumatic heart disease
* **Hypertension** — Classification, India burden (IHCI), resistant hypertension management
* **Arrhythmias** — 4 tabs: AF (CHA2DS2-VASc), SVT, Ventricular arrhythmias, Bradyarrhythmias
* **Valvular Disease** — Aortic stenosis, mitral disease, infective endocarditis
* **Investigations** — 7-row reference table (ECG, echo, CTCA, MRI, angiography, biomarkers)
* **Emergency** — STEMI, cardiac arrest, aortic dissection, acute pulmonary oedema
* **Prevention** — Risk assessment, lipid management, lifestyle measures
* **India Context** — Premature CAD, rheumatic disease burden, CSI guidance, PM-JAY
* **Assessment** — Symptom-based AI research with risk factors field

## India Cardiac Resources

* CSI: csi.org.in | AIIMS Cardiology: aiims.edu
* PM-JAY cardiac procedure coverage | India Hypertension Control Initiative (IHCI)
* Emergency: **112**

## Clinical Sources

ACC/AHA | ESC | WHO | NICE | CSI | PubMed

*CardioCare AI — For research and educational purposes only. Not medical advice.
CARDIAC EMERGENCY: 112 (India) / 999 (UK) / 911 (US)*

