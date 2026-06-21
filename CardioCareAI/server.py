"""
CardioCare AI — Production Backend Server v1.0
Cardiac Health Intelligence Platform
=============================================
DISCLAIMER: All AI output is for research/education only.
Not medical advice. Always consult a qualified cardiologist.
CARDIAC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US) immediately.
"""

import os
import sys
import json
import uuid
import logging
import datetime
import argparse
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_OK = True
except ImportError:
    print("[FATAL] Flask not installed. Run REPAIR_AND_RECOVER.bat")
    sys.exit(1)

try:
    import requests as req_lib
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import fitz
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

# ── Multi-provider AI module ─────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent / "modules"))
try:
    import ai_providers
    AI_PROVIDERS_OK = True
except ImportError:
    AI_PROVIDERS_OK = False

# ── Configuration ────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.resolve()
UPLOAD_DIR  = BASE_DIR / "uploads"
LOGS_DIR    = BASE_DIR / "logs"
DATA_DIR    = BASE_DIR / "data"
STATIC_DIR  = BASE_DIR / "static"
REPORTS_DIR = BASE_DIR / "reports_db"

for d in [UPLOAD_DIR, LOGS_DIR, DATA_DIR, STATIC_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PORT    = int(os.environ.get("CARDIOCARE_PORT", 5060))
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")  # legacy/back-compat default
# Server-side default keys per provider (optional; client can also send its own key per-request)
DEFAULT_PROVIDER_KEYS = ai_providers.get_env_keys() if AI_PROVIDERS_OK else {}
VERSION = "1.0.0"

DISCLAIMER = (
    "⚠️ AI RESEARCH DISCLAIMER: All output is AI-generated from published cardiology "
    "literature (ACC/AHA, ESC, CSI, WHO, PubMed). This is for educational research only. "
    "NOT a medical diagnosis or prescription. ALWAYS consult a qualified cardiologist "
    "before any health decision. CARDIAC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US) immediately."
)

# ── Logging ──────────────────────────────────────────────────────
log_file = LOGS_DIR / f"server_{datetime.date.today()}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("CardioCareAI")

# ── Flask App ────────────────────────────────────────────────────
app = Flask(__name__, static_folder=str(STATIC_DIR))
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
CORS(app, origins="*")

# ══════════════════════════════════════════════════════════════════
# OFFLINE CARDIOLOGY KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════════
KNOWLEDGE = {
    "coronary_artery_disease": {
        "name": "Coronary Artery Disease (CAD)",
        "prevalence": "Leading cause of death worldwide. ~20.5 million Americans affected. India: rising rapidly, earlier onset (10 years younger than Western populations on average).",
        "pathophysiology": "Atherosclerotic plaque formation narrows coronary arteries. Stable plaques (thick fibrous cap) cause stable angina. Vulnerable plaques (thin cap, lipid-rich core) prone to rupture causing acute thrombosis and MI.",
        "clinical_spectrum": ["Silent ischaemia — no symptoms, detected on testing", "Stable angina — predictable exertional chest pain, CCS Class I-IV", "Unstable angina — new/crescendo/rest pain, troponin negative", "NSTEMI — troponin positive, no ST elevation", "STEMI — ST elevation, complete coronary occlusion, emergency"],
        "investigations": ["ECG — ST/T changes, Q waves", "High-sensitivity troponin — 0/1hr or 0/2hr algorithm", "Stress ECG/Echo/Nuclear — functional ischaemia testing", "CTCA — excellent for ruling out CAD (NPV >99%)", "Coronary angiography — gold standard, with FFR for intermediate lesions"],
        "treatment": {
            "all_patients": "Aspirin 75mg lifelong, high-intensity statin (LDL <55 mg/dL target), lifestyle modification, risk factor control",
            "post_acs_dapt": "Aspirin + Ticagrelor (preferred) or Prasugrel or Clopidogrel for 12 months post-ACS",
            "beta_blocker": "Post-MI, angina symptom control, HFrEF",
            "ace_arb": "Post-MI with LV dysfunction, diabetes, hypertension",
            "revascularisation": "PCI for most lesions; CABG for left main, complex 3-vessel disease, diabetes with multivessel disease"
        }
    },
    "myocardial_infarction": {
        "name": "Acute Myocardial Infarction (Heart Attack)",
        "stemi_protocol": "FMC to ECG: <10 min. FMC to primary PCI: <90 min (PCI centre), <120 min (transfer). If unachievable: thrombolysis within 10 min of diagnosis.",
        "symptoms_classic": ["Central chest pain/pressure/tightness", "Radiation to jaw, arm, neck, back", "Sweating (diaphoresis)", "Nausea, vomiting", "Breathlessness", "Sense of impending doom"],
        "symptoms_atypical": ["Epigastric pain (mimics indigestion)", "Fatigue alone (especially women)", "Jaw pain without dental cause", "Back pain", "Silent MI in diabetics and elderly"],
        "immediate_action": "CALL EMERGENCY SERVICES IMMEDIATELY (112/999/911). Chew 300mg aspirin if not allergic. Sit/lie comfortably. GTN spray if prescribed (NOT if PDE5 inhibitor taken in 24-48hrs). Unlock door for ambulance.",
        "medications": ["Aspirin 300mg loading then 75mg lifelong", "P2Y12 inhibitor: Ticagrelor 180mg or Prasugrel 60mg loading", "Anticoagulation: UFH/LMWH/Bivalirudin", "High-intensity statin loading", "Beta-blocker, ACE inhibitor post-stabilisation"],
        "nstemi_risk_stratification": "GRACE score and TIMI score guide timing. Very high risk (shock, VT/VF, refractory ischaemia): immediate invasive <2hrs. High risk: <24hrs. Intermediate: <72hrs."
    },
    "heart_failure": {
        "name": "Heart Failure (HF)",
        "classification": "HFrEF (EF <40%), HFmrEF (EF 40-49%), HFpEF (EF ≥50%). NYHA Class I-IV based on symptom severity.",
        "biomarkers": "BNP >35 pg/mL or NT-proBNP >125 pg/mL supports diagnosis. Age-adjusted NT-proBNP thresholds for rule-in.",
        "four_pillars_hfref": ["ACE inhibitor/ARB/ARNI (sacubitril-valsartan preferred, PARADIGM-HF: 20% mortality reduction)", "Beta-blocker (carvedilol, bisoprolol, metoprolol succinate)", "MRA (spironolactone, eplerenone)", "SGLT2 inhibitor (dapagliflozin, empagliflozin) — newest pillar, benefits regardless of diabetes status"],
        "hfpef_treatment": "SGLT2 inhibitors (empagliflozin EMPEROR-Preserved, dapagliflozin DELIVER) — first proven evidence-based therapy for HFpEF.",
        "device_therapy": ["ICD — primary prevention if EF ≤35% on optimal medical therapy ≥3 months", "CRT — EF ≤35% + LBBB QRS ≥150ms", "LVAD — bridge to transplant or destination therapy in advanced HF"],
        "lifestyle": ["Sodium <2000mg/day in symptomatic HF", "Fluid restriction 1.5-2L/day if hyponatraemia/severe congestion", "Daily weight monitoring — alert if +2kg in 2-3 days", "Regular moderate exercise — HF-ACTION trial shows 15% reduction in hospitalisation"]
    },
    "hypertension": {
        "name": "Hypertension",
        "definition": "≥140/90 mmHg (clinic). ACC/AHA 2017: ≥130/80 mmHg. Hypertensive emergency: SBP ≥180 with end-organ damage.",
        "target": "<130/80 mmHg in most patients with established CVD or high risk (AHA 2017). <140/90 general population per some guidelines (ESC).",
        "lifestyle": ["DASH diet — reduces SBP 8-14 mmHg", "Sodium restriction <2300mg/day (ideally <1500mg)", "Regular aerobic exercise — SBP reduction 5-8 mmHg", "Weight loss — 1mmHg per kg lost", "Alcohol moderation", "Stop smoking"],
        "first_line_drugs": ["ACE inhibitor or ARB", "Calcium channel blocker (amlodipine)", "Thiazide diuretic (indapamide, chlorthalidone preferred over HCTZ)", "Single-pill combinations preferred for BP >20/10 above target"],
        "resistant_htn": "BP uncontrolled on 3 drugs including diuretic. 4th line: Spironolactone (PATHWAY-2 trial — most effective add-on). Screen for secondary causes: renal artery stenosis, primary aldosteronism, OSA, phaeochromocytoma.",
        "india_context": "~30% of Indian adults hypertensive. Average salt intake 10-12g/day (WHO target <5g). Often undiagnosed and undertreated — 'rule of halves' (half undiagnosed, half untreated of those diagnosed, half uncontrolled of those treated)."
    },
    "atrial_fibrillation": {
        "name": "Atrial Fibrillation (AF)",
        "prevalence": "Most common sustained arrhythmia. 33 million affected globally. Risk increases with age — 10% by age 80.",
        "anticoagulation": "CHA2DS2-VASc score: ≥2 (male) or ≥3 (female) — anticoagulate. DOACs preferred over warfarin for non-valvular AF (apixaban, rivaroxaban, dabigatran, edoxaban). Warfarin required for mechanical valves and AF with moderate-severe mitral stenosis.",
        "rate_control": "Target resting HR <110 bpm (lenient, per RACE II trial). Drugs: beta-blockers, diltiazem/verapamil, digoxin.",
        "rhythm_control": "Drugs: Flecainide/propafenone (no structural heart disease), amiodarone, sotalol, dronedarone. Catheter ablation (PVI) — 70-80% success for paroxysmal AF (CABANA, EAST-AFNET 4 trials show benefit).",
        "bleeding_risk": "HAS-BLED score assesses bleeding risk — used to identify modifiable risk factors, not to withhold anticoagulation."
    },
    "valve_disease": {
        "name": "Valvular Heart Disease",
        "aortic_stenosis": {"severity": "Severe: AVA <1.0 cm², mean gradient >40mmHg, peak velocity >4 m/s", "treatment": "TAVR now indicated across all surgical risk categories (low, intermediate, high risk per PARTNER 3, Evolut Low Risk). SAVR (surgical) still preferred in younger patients (<65-70) given uncertain TAVR valve durability data beyond 10 years."},
        "mitral_regurgitation": {"types": "Primary (degenerative — prolapse, flail) vs Secondary (functional — LV dilation, ischaemic)", "treatment": "Primary severe MR: Surgical repair preferred over replacement. Secondary MR: GDMT first, MitraClip (TEER) if symptomatic despite GDMT (COAPT trial)."},
        "mitral_stenosis": {"cause": "Predominantly rheumatic in developing countries including India", "treatment": "Balloon Mitral Valvotomy (BMV/PTMC) for favourable valve morphology (Wilkins score ≤8). Surgical valve replacement if unfavourable anatomy."}
    },
    "lipid_management": {
        "name": "Cholesterol & Lipid Management",
        "ldl_targets": {"very_high_risk": "<55 mg/dL (<1.4 mmol/L) — established ASCVD, FH, diabetes with organ damage", "high_risk": "<70 mg/dL (<1.8 mmol/L) — diabetes, CKD, multiple risk factors", "moderate_risk": "<100 mg/dL (<2.6 mmol/L)"},
        "statins": "Rosuvastatin 20-40mg (most potent, preferred in South Asians at lower doses), Atorvastatin 40-80mg. High-intensity statin = ≥50% LDL reduction.",
        "add_on_therapy": ["Ezetimibe 10mg — adds 15-20% LDL reduction (IMPROVE-IT trial)", "PCSK9 inhibitors (alirocumab, evolocumab) — 60% additional reduction (FOURIER, ODYSSEY trials)", "Inclisiran — siRNA, 2 injections/year, 50% LDL reduction", "Bempedoic acid — oral, for statin-intolerant patients"],
        "triglycerides": "Icosapent ethyl (Vascepa) 4g/day — REDUCE-IT trial: 25% CV event reduction in patients with TG >150 on statin. Fibrates for severe hypertriglyceridaemia (>500 mg/dL, pancreatitis risk).",
        "lipoprotein_a": "Genetically determined, not reduced by statins. >125 nmol/L (50mg/dL) = risk enhancer. PCSK9i reduce ~20%. Pelacarsen, olpasiran in trials specifically targeting Lp(a)."
    },
    "cardiac_diet": {
        "dash_diet": "Lowers SBP 8-14 mmHg. Rich in fruits, vegetables, whole grains, low-fat dairy, lean protein. Sodium <2300mg/day.",
        "mediterranean_diet": "PREDIMED trial: 30% reduction in major CV events. EVOO 4+ tbsp/day, vegetables, legumes, fish, nuts, whole grains, minimal red meat.",
        "ldl_lowering_foods": ["Oats/barley (beta-glucan) — LDL ↓5-10%", "Plant sterols 2g/day — LDL ↓8-10%", "Psyllium husk 10-12g/day — LDL ↓7-8%", "Almonds 30-45g/day — LDL ↓5-7%", "Walnuts 30g/day — LDL ↓5-7%"],
        "sodium_restriction": "General CVD prevention: <2300mg/day. Heart failure: <2000mg/day. Avoid processed foods, pickles, papad, canned foods, sauces.",
        "indian_cardiac_diet": "Multigrain atta, dal, vegetables, fruits (guava, pomegranate, amla), mustard/olive oil 3-4 tsp/day, limited ghee (1-2 tsp/day), avoid namkeen/mithai/fried snacks, low-fat dairy."
    },
    "exercise_cardiac": {
        "general_recommendation": "150-300 min/week moderate aerobic OR 75-150 min vigorous. Plus resistance training 2+ days/week.",
        "post_mi": "Cardiac rehabilitation reduces mortality 26-31% (Cochrane). Walking from Day 1-3 post-event if uncomplicated. Formal rehab 2-3x/week for 6-12 weeks.",
        "heart_failure_exercise": "HF-ACTION trial: moderate aerobic training safe, reduces hospitalisation 15%. Start supervised, build to 30 min moderate exercise 5x/week.",
        "hypertension_exercise": "Aerobic: SBP ↓5-8mmHg. Isometric exercise (wall sit, plank): SBP ↓8mmHg (most effective single modality per recent meta-analysis).",
        "contraindications": "Unstable angina, decompensated HF, severe symptomatic AS, uncontrolled arrhythmia, acute myocarditis/pericarditis — exercise contraindicated until stabilised."
    },
    "general_resources": {
        "india_hospitals": ["AIIMS Cardiology, New Delhi", "Apollo Hospitals (Cardiac Sciences)", "Fortis Escorts Heart Institute, Delhi", "Narayana Health, Bengaluru", "Medanta Heart Institute, Gurugram", "CMC Vellore Cardiology"],
        "emergency_numbers": {"india": "112", "uk": "999", "us": "911"},
        "guideline_bodies": ["ACC/AHA — American College of Cardiology / American Heart Association", "ESC — European Society of Cardiology", "CSI — Cardiological Society of India", "WHO — World Health Organization Cardiovascular Diseases"]
    }
}

def save_knowledge():
    with open(DATA_DIR / "cardio_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(KNOWLEDGE, f, indent=2, ensure_ascii=False)

def load_sessions():
    sf = DATA_DIR / "sessions.json"
    if sf.exists():
        with open(sf, "r") as f:
            return json.load(f)
    return {}

def save_session(sid, data):
    sessions = load_sessions()
    sessions[sid] = {**data, "updated": datetime.datetime.now().isoformat()}
    with open(DATA_DIR / "sessions.json", "w") as f:
        json.dump(sessions, f, indent=2)

def is_online():
    if not REQUESTS_OK:
        return False
    try:
        req_lib.get("https://8.8.8.8", timeout=3)
        return True
    except:
        return False

def extract_pdf_text(filepath):
    if not FITZ_OK:
        return "[PDF extraction unavailable — PyMuPDF not installed]"
    try:
        doc = fitz.open(str(filepath))
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text[:8000]
    except Exception as e:
        return f"[PDF extraction error: {e}]"

DEFAULT_SYSTEM_PROMPT = (
    "You are CardioCare AI, a cardiac health research assistant. You help patients understand "
    "cardiovascular conditions, medications, procedures, and lifestyle information from published "
    "cardiology literature. ALWAYS begin with a brief disclaimer that this is AI research. "
    "Provide thorough, evidence-based information referencing ACC/AHA, ESC, CSI guidelines where relevant. "
    "ALWAYS end with a reminder to consult a qualified cardiologist, and for any symptoms suggestive of "
    "a cardiac emergency, advise calling emergency services (112 India/999 UK/911 US) immediately. "
    "Be specific with clinical details. Never refuse to provide educational information."
)

def call_claude(prompt, system_prompt=None, max_tokens=2500, provider=None, api_key=None):
    """
    Multi-provider AI call. Defaults to 'anthropic' with the server's ANTHROPIC_API_KEY
    for backward compatibility, but accepts provider= and api_key= to route to any
    of the 5 supported providers (anthropic, openai, gemini, grok, deepseek).
    """
    if not AI_PROVIDERS_OK:
        return None, "ai_providers_module_missing"

    provider = (provider or "anthropic").lower()
    if provider not in ai_providers.PROVIDERS:
        provider = "anthropic"

    # Resolve key: explicit client key > server-side env default for that provider
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider == "anthropic" else "")

    if not effective_key or not REQUESTS_OK or not is_online():
        return None, "offline_or_no_key"

    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    text, mode = ai_providers.call_ai(provider, effective_key, prompt, system_prompt, max_tokens)
    if text is None:
        log.error(f"{provider} API error: {mode}")
        return None, mode
    return text, "live_ai"

def build_offline_response(topic, details="", patient_info=None):
    """Build comprehensive offline response from cardiology knowledge base."""
    topic_l = topic.lower()
    kb_key = None
    for key in KNOWLEDGE:
        if key.replace("_"," ") in topic_l or topic_l in key.replace("_"," ") or topic_l in KNOWLEDGE[key].get("name","").lower():
            kb_key = key
            break

    lines = [
        f"# CardioCare AI Research Report",
        f"**Topic:** {topic}",
        f"**Mode:** Offline Research (Embedded Cardiology Knowledge Base)",
        f"",
        f"> ⚠️ **DISCLAIMER:** This is AI-generated educational information from published cardiology "
        f"literature (ACC/AHA, ESC, CSI, WHO). NOT a medical diagnosis or prescription. "
        f"ALWAYS consult a qualified cardiologist before any decision. "
        f"CARDIAC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US) immediately.",
        f"",
        f"---",
        f""
    ]

    if kb_key:
        kb = KNOWLEDGE[kb_key]
        name = kb.get("name", topic)
        lines.append(f"## {name}")
        lines.append("")
        for field, value in kb.items():
            if field == "name":
                continue
            if isinstance(value, str):
                lines.append(f"**{field.replace('_',' ').title()}:** {value}")
                lines.append("")
            elif isinstance(value, list):
                lines.append(f"### {field.replace('_',' ').title()}")
                for item in value:
                    lines.append(f"- {item}")
                lines.append("")
            elif isinstance(value, dict):
                lines.append(f"### {field.replace('_',' ').title()}")
                for sub_key, sub_val in value.items():
                    if isinstance(sub_val, str):
                        lines.append(f"**{sub_key.replace('_',' ').title()}:** {sub_val}")
                    elif isinstance(sub_val, list):
                        lines.append(f"**{sub_key.replace('_',' ').title()}:**")
                        for item in sub_val:
                            lines.append(f"  - {item}")
                    lines.append("")
    else:
        lines += [
            f"## Research Overview: {topic}",
            "",
            f"Based on the embedded clinical knowledge base, here is research-based information about {topic}:",
            "",
            "**Clinical Guideline Sources:** ACC/AHA (American College of Cardiology/American Heart Association), "
            "ESC (European Society of Cardiology), CSI (Cardiological Society of India), WHO Cardiovascular Diseases.",
            "",
            "For detailed information on this specific topic, please enable live AI by adding your "
            "Anthropic API key in Settings, or consult a qualified cardiologist directly.",
            ""
        ]

    lines += [
        "---",
        "",
        "## India Cardiac Resources",
        "",
        "- **CSI India:** csi.org.in — Cardiological Society of India",
        "- **AIIMS Cardiology, New Delhi:** aiims.edu",
        "- **Apollo Hospitals Cardiac Sciences:** apollohospitals.com",
        "- **Fortis Escorts Heart Institute, Delhi**",
        "- **Narayana Health, Bengaluru:** narayanahealth.org",
        "- **Medanta Heart Institute, Gurugram**",
        "",
        "## Emergency Numbers",
        "- India: **112**",
        "- UK: **999**",
        "- US: **911**",
        "",
        "---",
        "",
        f"⚠️ **{DISCLAIMER}**"
    ]

    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(str(STATIC_DIR), filename)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", "version": VERSION,
        "online": is_online(), "api_key_set": bool(API_KEY),
        "live_ai": bool(API_KEY and is_online()),
        "pdf_extract": FITZ_OK, "image_process": PIL_OK,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route("/api/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        return jsonify({"error": "No files"}), 400
    session_id = request.form.get("session_id") or str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for f in request.files.getlist("files"):
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        safe = f"{uuid.uuid4().hex}{ext}"
        dest = session_dir / safe
        f.save(str(dest))
        extracted = ""
        ftype = "unknown"
        if ext == ".pdf":
            extracted = extract_pdf_text(dest)
            ftype = "pdf"
        elif ext in [".jpg",".jpeg",".png",".bmp",".dcm"]:
            ftype = "image"
        elif ext in [".txt",".csv"]:
            try: extracted = dest.read_text(encoding="utf-8", errors="ignore")[:5000]
            except: pass
            ftype = "text"
        results.append({"original": f.filename, "saved": safe, "type": ftype,
                        "size_kb": round(dest.stat().st_size/1024,1), "has_content": bool(extracted)})
    existing = load_sessions().get(session_id, {})
    existing_files = existing.get("files", []) + results
    save_session(session_id, {"session_id": session_id, "files": existing_files})
    return jsonify({"success": True, "session_id": session_id, "uploaded": len(results), "files": results, "disclaimer": DISCLAIMER})

@app.route("/api/analyse", methods=["POST"])
def analyse():
    data = request.json or {}
    topic        = data.get("topic", "General Cardiology")
    condition    = data.get("condition", "")
    patient_info = data.get("patient_info", {})
    section      = data.get("section", "general")
    session_id   = data.get("session_id", "")
    api_key_from_client = data.get("api_key", "")
    provider = data.get("provider", "anthropic")
    effective_key = api_key_from_client or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")

    log.info(f"Analysis: topic={topic} section={section}")

    file_context = ""
    if session_id:
        sessions = load_sessions()
        if session_id in sessions:
            files = sessions[session_id].get("files", [])
            if files:
                file_context = f"\n\nUploaded Reports ({len(files)} files):\n"
                for fi in files[:10]:
                    file_context += f"- {fi['original']} ({fi['type']}, {fi['size_kb']} KB)\n"

    prompt = f"""
Cardiac Health Research Request:
Topic/Condition: {topic}
Specific Condition: {condition}
Patient Age: {patient_info.get('age','Not specified')}
Symptoms: {patient_info.get('symptoms','Not specified')}
Current Medications: {patient_info.get('medications','None specified')}
Risk Factors: {patient_info.get('risk_factors','None specified')}
Section Requested: {section}
{file_context}

Please provide comprehensive research covering:
1. Overview and clinical context
2. Diagnosis criteria and investigations (with specific tests and normal ranges)
3. Evidence-based treatment options (medical and interventional)
4. Relevant medications with dosing information from clinical guidelines
5. Diet and lifestyle recommendations
6. When to seek emergency care
7. India-specific resources, hospitals, and guidelines (CSI)
8. Questions to ask their cardiologist
9. Recent developments and clinical trial evidence

Reference ACC/AHA, ESC, CSI guidelines. Be specific and clear about emergency warning signs.
"""
    result, mode = call_claude(prompt, provider=provider, api_key=effective_key) if (effective_key and is_online()) else (None, "offline")
    if not result:
        result = build_offline_response(topic, condition, patient_info)
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "analysis": result, "topic": topic, "disclaimer": DISCLAIMER, "timestamp": datetime.datetime.now().isoformat()})

@app.route("/api/condition/<condition_name>", methods=["GET"])
def condition_detail(condition_name):
    cn = condition_name.lower().replace("-","_").replace(" ","_")
    if cn in KNOWLEDGE:
        return jsonify({"success": True, "mode": "offline_kb", "condition": KNOWLEDGE[cn], "disclaimer": DISCLAIMER})
    provider = request.args.get("provider", "anthropic")
    api_key  = request.args.get("api_key", "")
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    prompt = f"Provide comprehensive clinical research about {condition_name} in cardiology. Include: definition, prevalence, causes, symptoms, diagnosis criteria (with specific investigations and normal ranges), evidence-based treatment options (medical and interventional), prognosis, and management guidelines from ACC/AHA, ESC, CSI."
    result, mode = call_claude(prompt, provider=provider, api_key=effective_key)
    if not result:
        result = build_offline_response(condition_name)
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/medicine", methods=["POST"])
def medicine_search():
    data = request.json or {}
    drug_name = data.get("drug_name", "")
    provider = data.get("provider", "anthropic")
    api_key  = data.get("api_key", "")
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    prompt = f"Provide detailed cardiology pharmacology research for: {drug_name}. Include: drug class, mechanism of action, indications, typical dosing, contraindications, key side effects, important drug interactions, and monitoring requirements. Reference ACC/AHA/ESC guidelines."
    result, mode = call_claude(prompt, provider=provider, api_key=effective_key)
    if not result:
        result = build_offline_response(drug_name)
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/ecg/interpret", methods=["POST"])
def interpret_ecg():
    data = request.json or {}
    findings = data.get("findings", "")
    context  = data.get("context", "")
    provider = data.get("provider", "anthropic")
    api_key  = data.get("api_key", "")
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    prompt = f"""
ECG/Cardiac Scan Interpretation Research:
Reported Findings: {findings}
Clinical Context: {context}

Please research what these findings may indicate, covering:
1. Explanation of each finding in plain English
2. Clinical significance and differential diagnoses to consider
3. What follow-up investigations may be recommended
4. Questions to ask the reporting cardiologist
5. When findings represent a cardiac emergency requiring immediate care

IMPORTANT: This is research only. Actual interpretation must be done by the requesting clinician.
If findings suggest acute MI, severe arrhythmia, or other emergency — emphasise calling 112/999/911.
"""
    result, mode = call_claude(prompt, provider=provider, api_key=effective_key)
    if not result:
        result = f"ECG/Scan interpretation research for findings: '{findings}'. This requires clinical correlation by your cardiologist. Please enable live AI for research-based interpretation, or consult your treating physician directly."
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/chat/send", methods=["POST"])
def chat_send():
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400
    provider = data.get("provider", "anthropic")
    api_key  = data.get("api_key", "")
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    if data.get("request_ai", False) and is_online() and effective_key:
        prompt = f"A cardiac health question from a patient: '{message}'\n\nProvide a compassionate, research-based response (3-4 paragraphs). Always end with reminder to consult their cardiologist, and for emergency symptoms to call 112/999/911."
        result, _ = call_claude(prompt, max_tokens=800, provider=provider, api_key=effective_key)
    else:
        result = None
    return jsonify({"success": True, "ai_response": result, "disclaimer": "Not medical advice. Consult your cardiologist. Emergency: 112/999/911."})

@app.route("/api/report/generate", methods=["POST"])
def generate_report():
    data = request.json or {}
    topic   = data.get("topic", "General")
    patient = data.get("patient_info", {})
    provider = data.get("provider", "anthropic")
    api_key  = data.get("api_key", "")
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    content = build_offline_response(topic, patient_info=patient)
    if effective_key and is_online():
        ai_content, _ = call_claude(f"Generate a comprehensive cardiac health research report for: {topic}. Patient: {patient}. Cover diagnosis, treatment options, medications, diet, exercise, and warning signs.", max_tokens=3500, provider=provider, api_key=effective_key)
        if ai_content:
            content = ai_content
    report_id = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    report = {"report_id": report_id, "generated": datetime.datetime.now().isoformat(), "topic": topic, "patient": patient, "content": content, "disclaimer": DISCLAIMER}
    with open(REPORTS_DIR / f"{report_id}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return jsonify(report)

@app.route("/api/providers", methods=["GET"])
def list_providers():
    """Returns the 5 supported AI providers so the frontend can render a selector."""
    if not AI_PROVIDERS_OK:
        return jsonify({"providers": [], "error": "ai_providers module not available"})
    providers = []
    for key, cfg in ai_providers.PROVIDERS.items():
        providers.append({
            "id": key,
            "label": cfg["label"],
            "default_model": cfg["default_model"],
            "key_prefix": cfg["key_prefix"],
            "get_key_url": cfg["get_key_url"],
            "server_default_configured": bool(DEFAULT_PROVIDER_KEYS.get(key))
        })
    return jsonify({"providers": providers, "online": is_online()})

@app.route("/api/status", methods=["GET"])
def status():
    any_key_configured = bool(API_KEY) or any(DEFAULT_PROVIDER_KEYS.values())
    return jsonify({
        "server": "running", "version": VERSION,
        "online": is_online(),
        "mode": "live_ai" if (any_key_configured and is_online()) else "offline_research",
        "api_key": "configured" if any_key_configured else "not_set",
        "capabilities": {"pdf": FITZ_OK, "images": PIL_OK, "live_ai": bool(any_key_configured and is_online()), "offline": True, "multi_provider": AI_PROVIDERS_OK},
        "knowledge_base": list(KNOWLEDGE.keys()),
        "providers": list(ai_providers.PROVIDERS.keys()) if AI_PROVIDERS_OK else [],
        "disclaimer": DISCLAIMER
    })

# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CardioCare AI Server")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--generate-static", action="store_true")
    args = parser.parse_args()

    if args.generate_static:
        log.info("Static files check complete.")
        sys.exit(0)

    save_knowledge()

    log.info("=" * 60)
    log.info(f"  CardioCare AI Server v{VERSION}")
    log.info("=" * 60)
    log.info(f"  Port:     {args.port}")
    log.info(f"  Online:   {is_online()}")
    log.info(f"  Live AI:  {'YES' if (API_KEY and is_online()) else 'NO (offline/demo mode)'}")
    log.info(f"  Static:   {STATIC_DIR}")
    log.info(f"  Uploads:  {UPLOAD_DIR}")
    log.info("=" * 60)
    log.info(f"  URL: http://localhost:{args.port}")
    log.info("=" * 60)
    log.info(DISCLAIMER)
    log.info("=" * 60)

    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True, use_reloader=False)
