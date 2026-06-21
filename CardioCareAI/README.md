# CardioCare AI v1.0
## Cardiac Health Intelligence Platform

---

## IMPORTANT MEDICAL DISCLAIMER

**THIS IS AN AI-POWERED RESEARCH AND INFORMATION TOOL ONLY.**

- All content is AI-generated from published cardiology literature (ACC/AHA, ESC, CSI, WHO, PubMed)
- Accuracy, completeness, and clinical applicability **may be incorrect or outdated**
- This is **NOT** a medical diagnosis, prescription, or clinical recommendation
- **ALWAYS** consult a qualified cardiologist before any health decision
- **CARDIAC EMERGENCY:** Chest pain, breathlessness, jaw/arm pain, palpitations, loss of consciousness — Call **112 (India) / 999 (UK) / 911 (US)** IMMEDIATELY. Do NOT use this platform during an emergency.
- The creators accept **no liability** for health decisions made without professional medical consultation

---

## Quick Start (Windows)

1. Extract the ZIP to any folder (e.g., `C:\CardioCareAI\`)
2. Double-click **`START_CardioCare_AI.bat`**
3. Everything installs automatically (2-5 minutes first time)
4. Browser opens at `http://localhost:5060`
5. Accept disclaimer and begin

---

## File Structure

```
CardioCareAI/
├── START_CardioCare_AI.bat        <- MAIN LAUNCHER
├── DIAGNOSTIC.bat                 <- System health checker
├── REPAIR_AND_RECOVER.bat         <- Fix problems
├── DOWNLOAD_OFFLINE_PACKAGES.bat  <- Save packages for offline
├── UPDATE.bat                     <- Update to latest versions
├── STOP_SERVER.bat                <- Stop the server
├── server.py                      <- Python Flask backend
├── README.md                      <- This file
├── static/
│   └── index.html                 <- Full web application
├── uploads/                       <- Your uploaded reports
├── offline_packages/              <- Cached Python packages
├── venv/                          <- Python environment (auto-created)
├── logs/                          <- Server and diagnostic logs
├── data/                          <- Knowledge base and sessions
└── reports_db/                    <- Generated AI reports
```

---

## What's Covered

### Cardiac Conditions
- Coronary Artery Disease (CAD), Acute MI, Stable/Unstable Angina
- Heart Failure (HFrEF, HFmrEF, HFpEF)
- Arrhythmias — AF, VT, SVT, Bradycardia, Heart Block
- Valve Disease — Aortic Stenosis, Mitral Regurgitation/Stenosis, Aortic Regurgitation
- Cardiomyopathies — Dilated, Hypertrophic, Restrictive
- Pericardial disease, Endocarditis, Aortic Aneurysm/Dissection
- Peripheral Arterial Disease, DVT/PE, Pulmonary Hypertension
- Congenital Heart Disease (Adult), Cardiac Arrest

### Medicines (8 Full Categories)
- Statins and lipid-lowering therapy (ezetimibe, PCSK9 inhibitors, inclisiran)
- Beta-blockers (carvedilol, metoprolol, bisoprolol)
- ACE inhibitors/ARBs/ARNI/MRA/SGLT2 inhibitors (heart failure pillars)
- Anticoagulants (DOACs, warfarin, heparins)
- Antiplatelets (aspirin, clopidogrel, ticagrelor, prasugrel)
- Diuretics (loop, thiazide, potassium-sparing)
- Antiarrhythmics (Vaughan Williams classification)
- Other key drugs (nitrates, CCBs, ivabradine, digoxin, vasopressors)

### Procedures & Surgery
- PCI/Angioplasty, stenting, primary PCI for STEMI
- CABG (bypass surgery) — graft types and indications
- TAVR/TAVI, MitraClip, transcatheter valve procedures
- Electrophysiology — catheter ablation (AF, SVT, VT), pacemakers, ICDs, CRT

### Diagnostics
- ECG systematic interpretation — normal values, key patterns (STEMI territories, LBBB, RBBB, WPW, Brugada, Long QT)
- Echocardiography parameters — EF, wall thickness, valve gradients, diastolic function
- Cardiac biomarkers — Troponin, BNP/NT-proBNP, D-dimer, CRP, Lp(a)

### Risk Assessment
- Interactive 10-year ASCVD risk calculator (research estimate)
- Risk enhancer factors (CAC score, Lp(a), family history, South Asian ethnicity)

### Lifestyle
- Heart-healthy diet principles, DASH diet, Mediterranean diet (PREDIMED evidence)
- Cholesterol/lipid-lowering foods with specific evidence
- Heart failure diet protocol (sodium/fluid restriction)
- Indian cardiac diet — practical guide with sample meal plan
- Exercise protocols by condition (post-MI, HF, AF, hypertension, HCM)

### Emergency & Rehabilitation
- Heart attack recognition (classic and atypical symptoms)
- CPR step-by-step guide
- Hypertensive emergency management
- Cardiac rehabilitation phases (Phase 1-3) with evidence

---

## Clinical Sources

All information referenced from:
- **ACC/AHA** — American College of Cardiology / American Heart Association
- **ESC** — European Society of Cardiology
- **CSI** — Cardiological Society of India
- **WHO** — World Health Organization Cardiovascular Diseases
- **PubMed** — National Library of Medicine research database
- **ClinicalTrials.gov** — Clinical trials registry

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| RAM | 4 GB | 8 GB |
| Storage | 3 GB free | 10 GB free |
| Internet | For first setup | For live AI |
| Python | Auto-installed | 3.10-3.12 |

---

## Choose Your AI Provider (5 Options)

Without any API key, the platform works in **offline research mode** using the embedded cardiology knowledge base.

To enable live AI analysis, go to **Settings** in the sidebar and pick ONE of 5 supported AI providers — each with its own free or paid API key:

| Provider | Model Used | Get a Free Key |
|----------|-----------|-----------------|
| **Claude** (Anthropic) | claude-sonnet-4 | console.anthropic.com |
| **ChatGPT** (OpenAI) | gpt-4o | platform.openai.com/api-keys |
| **Gemini** (Google) | gemini-2.0-flash | aistudio.google.com/apikey |
| **Grok** (xAI) | grok-2-latest | console.x.ai |
| **DeepSeek** | deepseek-chat | platform.deepseek.com/api_keys |

Click a provider card, paste its key, and click Save. Your key is stored **only in your browser's local storage** — it is sent directly to that provider's API and never touches any third-party server. You can switch providers at any time; each provider's key is remembered separately so you don't have to re-enter it.

If you don't add any key, simply select **Offline Mode** — the platform will use its built-in cardiology knowledge base with zero internet dependency.

---

## India-Specific Resources

| Resource | Contact |
|----------|---------|
| CSI India | csi.org.in |
| AIIMS Cardiology, New Delhi | aiims.edu |
| Apollo Hospitals (Cardiac Sciences) | apollohospitals.com |
| Fortis Escorts Heart Institute, Delhi | fortishealthcare.com |
| Narayana Health, Bengaluru | narayanahealth.org |
| Medanta Heart Institute, Gurugram | medanta.org |
| Emergency | 112 |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Double-click does nothing | Right-click → Run as Administrator |
| Python not found | Launcher downloads it automatically (needs internet) |
| Browser doesn't open | Go to http://localhost:5060 manually |
| Port in use | Run STOP_SERVER.bat, then START again |
| Package install fails | Run REPAIR_AND_RECOVER.bat → Option 2 |
| Works offline after first run | Run DOWNLOAD_OFFLINE_PACKAGES.bat once |
| Server starts but errors | Check logs\server_*.log |

---

## Legal Notice

This software is provided for research and educational purposes only. The creators make no representations about medical accuracy, completeness, or fitness for clinical use. Use of this tool does not constitute a medical consultation or professional relationship. The creators are not liable for any health outcomes arising from use of this platform. By using this software you confirm you have read and accepted the full medical disclaimer.

**CARDIAC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US) immediately. Do not rely on this software in an emergency.**

---

*CardioCare AI v1.0 — Cardiac Health Intelligence Platform*
*Research empowers. Your cardiologist heals. Use both.*
