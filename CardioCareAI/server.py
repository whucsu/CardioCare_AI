"""
CardioCare AI - Production Backend Server (Fresh Build)
Cardiology Health Intelligence Platform
Port: 5045
=========================================
DISCLAIMER: All AI output is for research/education only.
Not medical advice. Always consult a qualified cardiologist.
CARDIAC EMERGENCY (chest pain, breathlessness, palpitations with
collapse, signs of heart attack or stroke): Call 112 (India) /
999 (UK) / 911 (US) immediately.
"""

import os, sys, json, uuid, time, hashlib, logging, datetime, argparse
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("[FATAL] Flask not installed. Run REPAIR_AND_RECOVER.bat"); sys.exit(1)

try:
    import requests as req_lib; REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    import fitz; FITZ_OK = True
except ImportError:
    FITZ_OK = False

try:
    from PIL import Image; PIL_OK = True
except ImportError:
    PIL_OK = False

sys.path.insert(0, str(Path(__file__).parent / "modules"))
try:
    import ai_providers; AI_PROVIDERS_OK = True
except ImportError:
    AI_PROVIDERS_OK = False

BASE_DIR    = Path(__file__).parent.resolve()
UPLOAD_DIR  = BASE_DIR / "uploads"
LOGS_DIR    = BASE_DIR / "logs"
DATA_DIR    = BASE_DIR / "data"
STATIC_DIR  = BASE_DIR / "static"
REPORTS_DIR = BASE_DIR / "reports_db"

for d in [UPLOAD_DIR, LOGS_DIR, DATA_DIR, STATIC_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── SOFTWARESAFETY: no hardcoded secrets — all keys from env or client-supplied at runtime ──
PORT    = int(os.environ.get("CARDIOCARE_PORT", 5045))
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DEFAULT_PROVIDER_KEYS = ai_providers.get_env_keys() if AI_PROVIDERS_OK else {}
VERSION = "1.0.0"

DISCLAIMER = (
    "WARNING - AI RESEARCH DISCLAIMER: All output is AI-generated from published "
    "cardiology literature (ACC/AHA, ESC, WHO, NICE, CSI, PubMed). "
    "For educational research only. NOT a substitute for professional cardiac "
    "examination, diagnosis, or treatment. ALWAYS consult a qualified cardiologist. "
    "CARDIAC EMERGENCY (chest pain, sudden breathlessness, collapse, signs of "
    "heart attack or stroke): Call 112 (India) / 999 (UK) / 911 (US) immediately."
)

log_file = LOGS_DIR / f"server_{datetime.date.today()}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("CardioCareAI")

app = Flask(__name__, static_folder=str(STATIC_DIR))
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
CORS(app, origins="*")  # local single-user tool; no auth/session/cookie state to protect

_RATE_STORE = {}

def _get_client_id():
    return hashlib.sha256((request.remote_addr or "127.0.0.1").encode()).hexdigest()[:16]

def rate_limit_check():
    """SOFTWARESAFETY: route throttling on all endpoints."""
    cid = _get_client_id(); now = time.time()
    _RATE_STORE.setdefault(cid, [])
    _RATE_STORE[cid] = [t for t in _RATE_STORE[cid] if now - t < 60]
    if len(_RATE_STORE[cid]) >= 30: return False
    _RATE_STORE[cid].append(now); return True

def sanitise_api_key(key):
    """SOFTWARESAFETY: treat all client input as untrusted — validate and strip."""
    if not key or not isinstance(key, str): return ""
    key = key.strip()
    if len(key) > 512: return ""
    s = "".join(c for c in key if 0x21 <= ord(c) <= 0x7E)
    return s if len(s) >= 10 else ""

def validate_provider(p):
    """SOFTWARESAFETY: whitelist validation — reject anything not in the known set."""
    valid = {"anthropic","openai","gemini","grok","deepseek","mistral"}
    return p.lower() if p and p.lower() in valid else "anthropic"

def sanitise_text_field(val, max_len=500):
    """SOFTWARESAFETY: bound and strip all free-text client input before use in prompts/logs."""
    if not val or not isinstance(val, str): return ""
    return val.strip()[:max_len]

# ═══════════════════════════════════════════════════════════════
# CARDIOLOGY KNOWLEDGE BASE
# Sources: ACC/AHA Guidelines, ESC Guidelines, WHO, NICE,
#          Cardiological Society of India (CSI), PubMed
# ═══════════════════════════════════════════════════════════════
KNOWLEDGE = {
    "coronary_artery_disease": {
        "name": "Coronary Artery Disease (CAD)",
        "definition": "Atherosclerotic narrowing of coronary arteries reducing myocardial blood supply. Leading cause of death globally. India: CAD occurs 5-10 years earlier and progresses more aggressively than in Western populations, with higher rates in urban areas.",
        "risk_factors": "Non-modifiable: age, male sex, family history of premature CAD (before 55 men/65 women). Modifiable: hypertension, diabetes, dyslipidaemia (elevated LDL, low HDL, high Lp(a) common in Indians), smoking, obesity (South Asians have higher cardiometabolic risk at lower BMI), sedentary lifestyle. South Asian ethnicity is an independent risk factor requiring lower treatment thresholds per several guidelines.",
        "stable_angina": "Predictable chest pain on exertion, relieved by rest or GTN within minutes. Central/retrosternal, may radiate to arm/jaw/neck. Investigation: CT coronary angiography (CTCA) first-line per NICE for stable chest pain. Management: beta-blockers or calcium channel blockers first-line, aspirin, statin. Revascularisation (PCI/CABG) for refractory symptoms.",
        "acute_coronary_syndrome": "ACS spectrum: unstable angina, NSTEMI, STEMI. STEMI: EMERGENCY requiring immediate reperfusion - primary PCI (door-to-balloon under 90 minutes) or thrombolysis if PCI unavailable within 120 minutes. NSTEMI/unstable angina: GRACE score guides timing of invasive strategy. Management: dual antiplatelet therapy, anticoagulation, beta-blocker, high-intensity statin. Post-MI: cardiac rehabilitation, lifelong secondary prevention.",
    },
    "heart_failure": {
        "name": "Heart Failure",
        "classification": "HFrEF (EF≤40%), HFmrEF (EF 41-49%), HFpEF (EF≥50% - increasingly common, SGLT2 inhibitors now show benefit). NYHA functional classification I-IV based on symptom severity.",
        "aetiology": "Ischaemic heart disease (most common globally), hypertensive heart disease (major contributor in India), dilated cardiomyopathy, valvular heart disease (rheumatic heart disease remains significant in India, unlike Western countries where it is now rare), arrhythmia-induced, chemotherapy-induced cardiotoxicity.",
        "diagnosis": "NT-proBNP/BNP (excellent negative predictive value), echocardiography (essential - EF, valvular function, chamber size), ECG, chest X-ray. Cardiac MRI for tissue characterisation if infiltrative disease suspected.",
        "hfref_treatment": "Four pillars of HFrEF therapy (initiated and up-titrated in parallel): ACE inhibitor/ARB or ARNI (sacubitril-valsartan preferred), Beta-blocker (bisoprolol, carvedilol, metoprolol succinate only), Mineralocorticoid receptor antagonist (spironolactone/eplerenone), SGLT2 inhibitor (dapagliflozin/empagliflozin - benefit regardless of diabetes status). Device therapy: ICD for primary prevention (EF≤35%), CRT for dyssynchrony.",
        "rheumatic_heart_disease": "Rheumatic heart disease remains significant in India, following inadequately treated group A streptococcal pharyngitis leading to rheumatic fever and valvular damage (mitral valve most commonly affected). Secondary prevention: long-term penicillin prophylaxis (benzathine penicillin IM every 3-4 weeks).",
    },
    "hypertension": {
        "name": "Hypertension",
        "classification": "Per ACC/AHA 2017: Normal <120/80, Elevated 120-129/<80, Stage 1 130-139/80-89, Stage 2 ≥140/90. Hypertensive emergency: severe BP elevation WITH acute target organ damage - requires immediate controlled BP reduction in hospital.",
        "india_burden": "Prevalence estimated 25-30% of Indian adults, with awareness/treatment/control rates significantly lower than high-income countries. High dietary salt intake (often 2-3x WHO limit) major contributor. India Hypertension Control Initiative (IHCI) works to improve control rates through standardized primary care protocols.",
        "investigation": "Confirm with out-of-office measurement (ABPM/home BP). Assess target organ damage: ECG/echo (LVH), urine ACR and eGFR (renal), fundoscopy (retinopathy). Screen for secondary causes if young age or resistant hypertension: renal artery stenosis, primary hyperaldosteronism, phaeochromocytoma.",
        "management": "Lifestyle: sodium restriction under 5-6g/day, DASH diet, exercise, weight loss. Pharmacological: ACE-I/ARB, calcium channel blocker, thiazide-like diuretic - usually combination therapy needed. Resistant hypertension: add spironolactone (PATHWAY-2 trial), assess adherence, consider secondary causes.",
    },
    "arrhythmias": {
        "name": "Cardiac Arrhythmias",
        "atrial_fibrillation": "Most common sustained arrhythmia. Major concern: 5x increased stroke risk from left atrial appendage thrombus. Stroke risk assessment: CHA2DS2-VASc score guides anticoagulation. DOACs (apixaban, rivaroxaban, dabigatran, edoxaban) preferred over warfarin for most patients. Rate control: beta-blockers or verapamil/diltiazem first-line. Catheter ablation increasingly first-line for symptomatic paroxysmal AF.",
        "svt": "Supraventricular tachycardia: regular narrow-complex tachycardia, often AVNRT or AVRT. Acute: vagal manoeuvres first-line, IV adenosine if fails, DC cardioversion if unstable. Long-term: catheter ablation curative for recurrent symptomatic SVT.",
        "ventricular_arrhythmias": "VT: life-threatening if sustained/unstable - immediate DC cardioversion. VF: CARDIAC ARREST - immediate CPR and defibrillation. ICD for secondary prevention after survived cardiac arrest or sustained VT with structural heart disease.",
        "bradyarrhythmias": "Sinus node dysfunction, AV block (first/second/third degree). Mobitz II and complete heart block are indications for permanent pacemaker.",
    },
    "valvular_disease": {
        "name": "Valvular Heart Disease",
        "aortic_stenosis": "Most common valvular disease in developed countries; rheumatic aetiology remains significant in India. Classic triad (poor prognosis if present): exertional angina, syncope, breathlessness. Severe AS: valve area <1.0cm². Management: TAVI increasingly used across risk spectrum, surgical AVR for suitable candidates.",
        "mitral_disease": "Mitral stenosis predominantly rheumatic (especially relevant in India). Percutaneous balloon mitral valvotomy is treatment of choice for suitable anatomy. Mitral regurgitation: surgical repair preferred over replacement where feasible.",
        "endocarditis": "Diagnosis: modified Duke criteria (blood cultures + echocardiographic findings). Management: prolonged IV antibiotics (4-6 weeks), surgery for heart failure/uncontrolled infection/large vegetations. Antibiotic prophylaxis for dental procedures now only for highest-risk patients.",
    },
    "cardiomyopathy": {
        "name": "Cardiomyopathies",
        "hcm": "Hypertrophic cardiomyopathy: genetic condition causing unexplained LV hypertrophy. Leading cause of sudden cardiac death in young athletes. Risk stratification for sudden death guides ICD decision (family history of SCD, unexplained syncope, extreme LV hypertrophy). Management: beta-blockers, septal reduction therapy for significant LVOT obstruction, mavacamten (novel option).",
        "dcm": "Dilated cardiomyopathy: LV dilation and systolic dysfunction not explained by ischaemia. Causes: idiopathic/genetic, alcohol-related (often reversible), peripartum, viral myocarditis sequelae, chemotherapy-induced. Management follows standard HFrEF pathway; reversible causes should always be sought.",
        "restrictive_infiltrative": "Restrictive cardiomyopathy: impaired ventricular filling due to stiff myocardium. Causes: amyloidosis (ATTR amyloid increasingly recognised in elderly, now treatable with tafamidis), sarcoidosis, haemochromatosis. Diagnosis: echo, cardiac MRI, technetium bone scintigraphy for ATTR amyloid.",
    },
    "cardiac_investigations": {
        "name": "Cardiac Investigations",
        "ecg_basics": "12-lead ECG: fundamental first-line investigation. Key patterns: STEMI (ST elevation in contiguous leads), NSTEMI/ischaemia (ST depression, T inversion), new LBBB (STEMI-equivalent with chest pain), AF (absent P waves, irregularly irregular), long QT, Brugada pattern.",
        "echocardiography": "Transthoracic echo (TTE): first-line cardiac imaging - chamber size/function, valve structure, pericardial effusion. Transoesophageal echo (TOE): better views of posterior structures, used for endocarditis assessment and pre-cardioversion thrombus exclusion.",
        "advanced_imaging": "CT coronary angiography (CTCA): excellent negative predictive value, first-line per NICE for stable chest pain. Cardiac MRI: gold-standard for ventricular volumes/function and tissue characterisation. Invasive coronary angiography: gold-standard anatomical assessment, allows immediate PCI.",
        "biomarkers": "Troponin (high-sensitivity): gold-standard for myocardial injury. Elevated troponin is NOT synonymous with type 1 MI - can be elevated in renal failure, sepsis, PE, myocarditis (clinical context essential). NT-proBNP/BNP: excellent for excluding heart failure.",
    },
    "cardiac_emergency": {
        "name": "Cardiac Emergencies",
        "stemi_recognition": "ACUTE CORONARY SYNDROME - MEDICAL EMERGENCY. Classic symptoms: central crushing chest pain/pressure, radiating to left arm/jaw/neck/back, sweating, nausea, breathlessness. Atypical presentations common in women, elderly, diabetics. IMMEDIATE ACTION: call emergency services, chew aspirin 300mg if available and no contraindication, do not drive yourself to hospital.",
        "cardiac_arrest": "No pulse, unresponsive, not breathing normally (agonal gasping is NOT normal breathing - still start CPR). IMMEDIATE ACTION: call for emergency help, start chest compressions immediately (100-120/min, depth 5-6cm), use AED as soon as available, continue CPR until emergency services arrive.",
        "acute_heart_failure": "Acute pulmonary oedema: severe breathlessness (worse lying flat), frothy pink sputum, extreme distress. EMERGENCY: sit patient upright, high-flow oxygen, IV diuretics, nitrates if BP adequate, identify and treat precipitant.",
        "aortic_dissection": "EMERGENCY, high mortality if untreated. Sudden severe tearing/ripping chest or back pain, unequal pulses/BP between arms. Type A (ascending): surgical emergency. CT aortography crucial - thrombolysis would be catastrophic if dissection present.",
        "massive_pe": "Massive/high-risk pulmonary embolism causes acute right heart strain and haemodynamic compromise. Symptoms: sudden severe breathlessness, pleuritic chest pain, collapse. Haemodynamically unstable PE requires thrombolysis or catheter-directed therapy.",
    },
    "prevention_lifestyle": {
        "name": "Cardiovascular Prevention & Lifestyle",
        "risk_assessment": "CV risk calculators (ASCVD, QRISK3, SCORE2) have been noted to underestimate risk in South Asian populations - several guidelines recommend lower treatment thresholds for South Asian ethnicity given demonstrated excess cardiovascular risk independent of traditional risk factors.",
        "lipid_management": "Statins first-line for primary and secondary prevention. Very high-risk patients target LDL <55mg/dL per contemporary guidelines. PCSK9 inhibitors for very high-risk not at target despite maximal statin+ezetimibe. Lp(a) increasingly recognised as important independent risk factor, commonly elevated in South Asians.",
        "diabetes_cv_risk": "Diabetes significantly amplifies cardiovascular risk, particularly relevant given India's high diabetes burden. SGLT2 inhibitors and GLP-1 receptor agonists have demonstrated cardiovascular benefit beyond glycaemic control.",
        "lifestyle_measures": "Regular physical activity (150+ min/week moderate intensity), Mediterranean/DASH diet, smoking cessation (single most impactful intervention), weight management targeting visceral adiposity. Cardiac rehabilitation post-MI demonstrably improves outcomes and is underutilised.",
    },
    "india_cardiology": {
        "name": "Cardiology in India",
        "burden_epidemiology": "Cardiovascular disease is the leading cause of death in India, over a quarter of all deaths. CAD events occur approximately 5-10 years earlier than Western countries. Contributing factors: high diabetes/metabolic syndrome prevalence, abdominal obesity at lower BMI thresholds, tobacco use, elevated Lp(a), high dietary salt intake.",
        "treatment_access": "Significant tertiary cardiac care in major cities (AIIMS, private hospitals) offering PCI, CABG, TAVI comparable to international standards. Rural-urban disparity persists for timely primary PCI access. Ayushman Bharat (PM-JAY) provides insurance coverage for eligible families. Generic cardiac medications widely available at substantially lower cost.",
        "rheumatic_disease_burden": "Rheumatic heart disease remains a significant public health issue in India, in contrast to high-income countries where it has become rare. Community-based echocardiographic screening programmes in some states aim to detect subclinical RHD earlier.",
        "csi_guidelines": "The Cardiological Society of India (CSI) publishes India-specific guidance adapting international guidelines to account for Indian epidemiological features - lower BMI/waist circumference thresholds for obesity, earlier statin initiation given premature CAD risk, attention to the aggressive dyslipidaemia pattern common in Indian patients.",
    },
}

def save_knowledge():
    with open(DATA_DIR / "cardio_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(KNOWLEDGE, f, indent=2, ensure_ascii=False)

def load_sessions():
    sf = DATA_DIR / "sessions.json"
    if sf.exists():
        with open(sf) as f: return json.load(f)
    return {}

def save_session(sid, data):
    sessions = load_sessions()
    sessions[sid] = {**data, "updated": datetime.datetime.now().isoformat()}
    with open(DATA_DIR / "sessions.json", "w") as f: json.dump(sessions, f, indent=2)

def is_online():
    if not REQUESTS_OK: return False
    try: req_lib.get("https://8.8.8.8", timeout=3); return True
    except: return False

def extract_pdf_text(filepath):
    if not FITZ_OK: return "[PDF extraction unavailable]"
    try:
        doc = fitz.open(str(filepath))
        text = "".join(page.get_text() for page in doc)
        doc.close(); return text[:8000]
    except Exception:
        # SOFTWARESAFETY: never leak internal exception/stack trace details to caller
        return "[PDF extraction error]"

DEFAULT_SYSTEM = (
    "You are CardioCare AI, an expert cardiology health research assistant. "
    "Help patients understand cardiac conditions, investigations, medications, "
    "and heart health from published cardiology literature. "
    "ALWAYS start with a brief AI research disclaimer. "
    "Reference ACC/AHA, ESC, WHO, NICE, CSI (Cardiological Society of India) guidelines. "
    "ALWAYS end reminding them to consult a qualified cardiologist. "
    "For cardiac emergencies (chest pain, cardiac arrest, aortic dissection, "
    "massive PE, acute heart failure): advise immediate 112/999/911 or A&E attendance. "
    "For Indian patients: reference CSI guidance, note premature/aggressive CAD risk "
    "in South Asians, mention rheumatic heart disease relevance, and PM-JAY where relevant."
)

def call_ai(prompt, system_prompt=None, max_tokens=2500, provider=None, api_key=None):
    if not AI_PROVIDERS_OK: return None, "ai_providers_missing"
    provider = validate_provider(provider)
    effective_key = (sanitise_api_key(api_key) or
                     DEFAULT_PROVIDER_KEYS.get(provider, "") or
                     (API_KEY if provider == "anthropic" else ""))
    if not effective_key or not REQUESTS_OK or not is_online():
        return None, "offline_or_no_key"
    text, mode = ai_providers.call_ai(
        provider, effective_key, prompt, system_prompt or DEFAULT_SYSTEM, max_tokens
    )
    if text is None:
        log.error(f"{provider} API error: {mode}")
        return None, mode
    return text, "live_ai"

def build_offline_response(topic, patient_info=None):
    topic_l = topic.lower()
    kb_key = next(
        (k for k in KNOWLEDGE
         if k.replace("_", " ") in topic_l or topic_l in k.replace("_", " ")
         or any(w in topic_l for w in k.split("_"))),
        None
    )
    lines = [
        "# CardioCare AI Research Report",
        f"**Topic:** {topic}",
        "**Mode:** Offline Research (Embedded Cardiology Knowledge Base)",
        "",
        "> DISCLAIMER: AI-generated educational information. NOT medical advice. "
        "ALWAYS consult a qualified cardiologist. "
        "CARDIAC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US).",
        "", "---", ""
    ]
    if kb_key:
        kb = KNOWLEDGE[kb_key]
        lines.append(f"## {kb.get('name', topic)}\n")
        for field, value in kb.items():
            if field == "name": continue
            if isinstance(value, str):
                lines += [f"**{field.replace('_', ' ').title()}:** {value}", ""]
    else:
        lines += [f"## Research Overview: {topic}", "",
                  f"Enable live AI in Settings for detailed research on {topic}.", ""]
    lines += [
        "---",
        "## India Cardiac Care Resources",
        "- CSI: Cardiological Society of India (csi.org.in)",
        "- AIIMS Cardiology: aiims.edu",
        "- PM-JAY: cardiac procedure insurance coverage",
        "- India Hypertension Control Initiative (IHCI)",
        "- Emergency: 112",
        "",
        f"WARNING - {DISCLAIMER}"
    ]
    return "\n".join(lines)

@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(str(STATIC_DIR), filename)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": VERSION,
                    "online": is_online(), "pdf_extract": FITZ_OK,
                    "timestamp": datetime.datetime.now().isoformat()})

@app.route("/api/upload", methods=["POST"])
def upload():
    if "files" not in request.files: return jsonify({"error": "No files"}), 400
    session_id = request.form.get("session_id") or str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id; session_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for f in request.files.getlist("files"):
        if not f.filename: continue
        ext = Path(f.filename).suffix.lower()
        # SOFTWARESAFETY: never trust client filename — generate opaque server-side name
        safe = f"{uuid.uuid4().hex}{ext}"; dest = session_dir / safe; f.save(str(dest))
        extracted = extract_pdf_text(dest) if ext == ".pdf" else ""
        results.append({"original": f.filename, "saved": safe,
                        "type": "pdf" if ext == ".pdf" else ("image" if ext in [".jpg",".jpeg",".png"] else "text"),
                        "size_kb": round(dest.stat().st_size/1024, 1), "has_content": bool(extracted)})
    existing = load_sessions().get(session_id, {})
    save_session(session_id, {"session_id": session_id, "files": existing.get("files",[]) + results})
    return jsonify({"success": True, "session_id": session_id,
                    "uploaded": len(results), "files": results, "disclaimer": DISCLAIMER})

@app.route("/api/analyse", methods=["POST"])
def analyse():
    data = request.json or {}
    if not rate_limit_check(): return jsonify({"error": "Rate limit exceeded"}), 429
    topic = sanitise_text_field(data.get("topic", "General Cardiology"), 200)
    condition = sanitise_text_field(data.get("condition", ""), 200)
    patient_info = data.get("patient_info", {}) if isinstance(data.get("patient_info"), dict) else {}
    provider = validate_provider(data.get("provider", "anthropic"))
    effective_key = (sanitise_api_key(data.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    prompt = (
        f"Cardiology Research Request: {topic} / {condition}\n"
        f"Patient: Age {sanitise_text_field(str(patient_info.get('age','NR')),10)}, "
        f"Symptoms: {sanitise_text_field(str(patient_info.get('symptoms','NR')),300)}, "
        f"Duration: {sanitise_text_field(str(patient_info.get('duration','NR')),100)}, "
        f"Risk factors: {sanitise_text_field(str(patient_info.get('risk_factors','NR')),300)}\n"
        f"Medications/History: {sanitise_text_field(str(patient_info.get('history','none')),300)}\n"
        "Cover: clinical overview, differential diagnosis, investigations, "
        "evidence-based treatment options, red flags/warning signs, "
        "India-specific context (CSI, South Asian CVD risk), "
        "questions to ask the cardiologist. Reference ACC/AHA, ESC, NICE, CSI."
    )
    result, mode = (call_ai(prompt, provider=provider, api_key=effective_key)
                    if (effective_key and is_online()) else (None,"offline"))
    if not result: result = build_offline_response(topic, patient_info); mode = "offline"
    return jsonify({"success": True, "mode": mode, "analysis": result,
                    "topic": topic, "disclaimer": DISCLAIMER,
                    "timestamp": datetime.datetime.now().isoformat()})

@app.route("/api/condition/<condition_name>")
def condition_detail(condition_name):
    cn = sanitise_text_field(condition_name, 100).lower().replace("-","_").replace(" ","_")
    if cn in KNOWLEDGE:
        return jsonify({"success": True, "mode": "offline_kb",
                        "condition": KNOWLEDGE[cn], "disclaimer": DISCLAIMER})
    provider = validate_provider(request.args.get("provider","anthropic"))
    effective_key = (sanitise_api_key(request.args.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    safe_name = sanitise_text_field(condition_name, 100)
    prompt = (f"Comprehensive cardiology research on {safe_name}: "
              "definition, prevalence, pathophysiology, clinical features, diagnosis, "
              "evidence-based management, prognosis. Reference ACC/AHA, ESC, NICE, CSI.")
    result, mode = call_ai(prompt, provider=provider, api_key=effective_key)
    if not result: result = build_offline_response(safe_name); mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/cardio/assess", methods=["POST"])
def assess_cardio():
    data = request.json or {}
    if not rate_limit_check(): return jsonify({"error": "Rate limit exceeded"}), 429
    symptom = sanitise_text_field(data.get("symptom",""), 300)
    duration = sanitise_text_field(data.get("duration",""), 100)
    age = sanitise_text_field(str(data.get("age","")), 10)
    risk_factors = sanitise_text_field(data.get("risk_factors",""), 300)
    history = sanitise_text_field(data.get("history",""), 300)
    provider = validate_provider(data.get("provider","anthropic"))
    effective_key = (sanitise_api_key(data.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    if not symptom:
        return jsonify({"error": "Symptom field is required"}), 400
    prompt = (
        f"Cardiology Assessment Research:\n"
        f"Chief Symptom: {symptom}\nDuration: {duration}\n"
        f"Age: {age}\nRisk Factors: {risk_factors}\nHistory: {history}\n"
        "Provide: possible causes (most likely to least likely), "
        "urgency of assessment needed, red flags requiring emergency care, "
        "what the cardiologist will likely do, questions to ask. "
        "This is educational research — must consult cardiologist for actual diagnosis."
    )
    result, mode = call_ai(prompt, provider=provider, api_key=effective_key)
    if not result:
        result = (f"Cardiology assessment research for: {symptom}. "
                  "Enable live AI in Settings for personalised research. "
                  "For any concerning cardiac symptom, see your cardiologist promptly. "
                  "For emergencies (chest pain, breathlessness, collapse): 112/999/911.")
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/chat/send", methods=["POST"])
def chat_send():
    data = request.json or {}
    if not rate_limit_check(): return jsonify({"error": "Rate limit exceeded"}), 429
    message = sanitise_text_field(data.get("message",""), 1000)
    if not message: return jsonify({"error": "Empty message"}), 400
    provider = validate_provider(data.get("provider","anthropic"))
    effective_key = (sanitise_api_key(data.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    result = None
    if data.get("request_ai") and is_online() and effective_key:
        result, _ = call_ai(
            f"Cardiology patient question: '{message}'. "
            "3-4 paragraphs, compassionate and evidence-based. "
            "Include India-specific guidance where relevant. "
            "End with cardiologist consultation reminder. "
            "For emergencies (chest pain, cardiac arrest, aortic dissection): 112/999/911 immediately.",
            max_tokens=800, provider=provider, api_key=effective_key)
    return jsonify({"success": True, "ai_response": result,
                    "disclaimer": "Not medical advice. Consult your cardiologist."})

@app.route("/api/report/generate", methods=["POST"])
def generate_report():
    data = request.json or {}
    if not rate_limit_check(): return jsonify({"error": "Rate limit exceeded"}), 429
    topic = sanitise_text_field(data.get("topic","General Cardiology"), 200)
    patient = data.get("patient_info", {}) if isinstance(data.get("patient_info"), dict) else {}
    provider = validate_provider(data.get("provider","anthropic"))
    effective_key = (sanitise_api_key(data.get("api_key","")) or
                     DEFAULT_PROVIDER_KEYS.get(provider,"") or
                     (API_KEY if provider=="anthropic" else ""))
    content = build_offline_response(topic, patient)
    if effective_key and is_online():
        ai_content, _ = call_ai(
            f"Generate comprehensive cardiology research report for: {topic}. "
            f"Patient: {patient}. Cover diagnosis, treatment options, follow-up, prevention.",
            max_tokens=3500, provider=provider, api_key=effective_key)
        if ai_content: content = ai_content
    # SOFTWARESAFETY: opaque, non-sequential identifier — not a predictable/enumerable integer ID
    report_id = f"report_{uuid.uuid4().hex}"
    report = {"report_id": report_id, "generated": datetime.datetime.now().isoformat(),
              "topic": topic, "patient": patient, "content": content, "disclaimer": DISCLAIMER}
    with open(REPORTS_DIR / f"{report_id}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return jsonify(report)

@app.route("/api/resolve", methods=["POST"])
def resolve_multi_ai():
    data = request.json or {}
    if not rate_limit_check(): return jsonify({"error": "Rate limit exceeded"}), 429
    prompt = sanitise_text_field(data.get("prompt",""), 4000)
    if not prompt: return jsonify({"error": "No prompt provided"}), 400
    pairs_raw = data.get("providers",[])
    if not isinstance(pairs_raw, list) or len(pairs_raw) < 1:
        return jsonify({"error": "No providers specified"}), 400
    if not AI_PROVIDERS_OK: return jsonify({"error": "ai_providers module not available"}), 500
    pairs = []
    for p in pairs_raw[:6]:
        if not isinstance(p, dict): continue
        pid = validate_provider(p.get("provider",""))
        key = sanitise_api_key(p.get("key",""))
        if pid and key: pairs.append((pid, key))
    if not pairs: return jsonify({"error": "No valid provider+key pairs"}), 400
    results = ai_providers.call_multi_ai(pairs, prompt, DEFAULT_SYSTEM, 1500)
    successes = [r for r in results if r.get("success") and r.get("text")]
    synthesis = None
    if len(successes) >= 2:
        synth_parts = [f"=== {r.get('label',r.get('provider','AI'))} ===\n{(r.get('text') or '')[:1200]}"
                       for r in successes]
        synth_prompt = (
            "You are a cardiology research synthesis engine. Multiple AI systems "
            "answered the same question. Question: " + prompt + "\n\n" +
            "\n\n".join(synth_parts) + "\n\n"
            "Synthesise the best, most complete, evidence-based research answer. "
            "Note any disagreements. Lead with the most clinically important finding. "
            "Remind that this is research only — consult a qualified cardiologist."
        )
        synth_key = next((k for pr,k in pairs if pr==successes[0]["provider"]), None)
        if synth_key:
            synth_text, _ = ai_providers.call_ai(
                successes[0]["provider"], synth_key, synth_prompt,
                "You are a cardiology research synthesis assistant.", 2000)
            synthesis = synth_text
    return jsonify({"success": True, "responses": results,
                    "synthesis": synthesis, "disclaimer": DISCLAIMER})

@app.route("/api/providers")
def list_providers():
    if not AI_PROVIDERS_OK: return jsonify({"providers": [], "error": "ai_providers module not available"})
    return jsonify({"providers": [
        {"id":k,"label":v["label"],"default_model":v["default_model"],
         "key_prefix":v["key_prefix"],"get_key_url":v["get_key_url"],
         "server_default_configured":bool(DEFAULT_PROVIDER_KEYS.get(k))}
        for k,v in ai_providers.PROVIDERS.items()], "online": is_online()})

@app.route("/api/status")
def status():
    any_key = bool(API_KEY) or any(DEFAULT_PROVIDER_KEYS.values())
    return jsonify({"server":"running","version":VERSION,"online":is_online(),
                    "mode":"live_ai" if (any_key and is_online()) else "offline_research",
                    "capabilities":{"pdf":FITZ_OK,"images":PIL_OK,
                                    "live_ai":bool(any_key and is_online()),
                                    "offline":True,"multi_provider":AI_PROVIDERS_OK,
                                    "rate_limiting":True,"aes256_frontend":True,
                                    "ambiguity_resolver":True},
                    "knowledge_base":list(KNOWLEDGE.keys()),
                    "providers":list(ai_providers.PROVIDERS.keys()) if AI_PROVIDERS_OK else [],
                    "disclaimer":DISCLAIMER})

# SOFTWARESAFETY: opaque fault management — never leak stack traces or internals to client
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    err_ref = uuid.uuid4().hex[:12]
    log.error(f"[{err_ref}] Internal server error: {e}")
    return jsonify({"error": "Internal server error", "reference": err_ref}), 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    save_knowledge()
    log.info("="*60)
    log.info(f"  CardioCare AI Server v{VERSION} - Port {args.port}")
    log.info(f"  Online: {is_online()}")
    log.info(f"  URL: http://localhost:{args.port}")
    log.info(f"  Providers: {list(ai_providers.PROVIDERS.keys()) if AI_PROVIDERS_OK else 'N/A'}")
    log.info("="*60)
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True, use_reloader=False)
