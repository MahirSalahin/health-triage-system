import streamlit as st
import os
import json
import requests
from typing import Optional
from api_client import api

# --- Page Config & Styling ---
st.set_page_config(
    page_title="Health Triage System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a beautiful, professional UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Clean Cards using HTML injection */
    .custom-card {
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(150, 150, 150, 0.2);
        margin-bottom: 24px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .custom-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    
    /* Style Streamlit's native bordered containers to look like custom cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--secondary-background-color) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
        border: 1px solid rgba(150, 150, 150, 0.2) !important;
        margin-bottom: 24px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Responsive Grid for Triage Cards */
    .triage-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
        align-items: start;
    }
    /* If there's an odd number of cards (e.g. Vitals missing), make the final card span the full width */
    .triage-grid > div:nth-child(odd):last-child {
        grid-column: 1 / -1;
    }
    @media (max-width: 768px) {
        .triage-grid {
            grid-template-columns: 1fr;
        }
        .triage-grid > div:nth-child(odd):last-child {
            grid-column: 1; /* Reset span on mobile */
        }
    }
    
    /* Triage Badges */
    .triage-badge {
        display: inline-block;
        padding: 12px 28px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 1.25rem;
        color: #ffffff;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    .triage-GREEN { background: linear-gradient(135deg, #10b981, #059669); }
    .triage-YELLOW { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .triage-RED { background: linear-gradient(135deg, #ef4444, #dc2626); }
    .triage-BLACK { background: linear-gradient(135deg, #1f2937, #111827); }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        border-bottom: 2px solid rgba(150, 150, 150, 0.2);
        padding-bottom: 8px;
    }
    
    /* Data Lists */
    .data-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .data-list li {
        padding: 12px 0;
        border-bottom: 1px solid rgba(150, 150, 150, 0.1);
        display: flex;
        flex-direction: column;
    }
    .data-list li:last-child { border-bottom: none; }
    .item-title { font-weight: 600; font-size: 1.05rem; }
    .item-desc { opacity: 0.8; font-size: 0.95rem; margin-top: 4px; }
    .confidence { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; background: rgba(99, 102, 241, 0.2); color: #818cf8; margin-left: 8px;}
    
    /* Alerts */
    .alert-box {
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        font-weight: 500;
    }
    .alert-danger { background-color: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; color: #fca5a5; }
    .alert-success { background-color: rgba(16, 185, 129, 0.15); border-left: 4px solid #10b981; color: #6ee7b7; }
    
    /* Override Streamlit Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s !important;
    }
    
    /* Hide top padding */
    .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "patient" not in st.session_state:
    st.session_state.patient = {}
if "symptoms_english" not in st.session_state:
    st.session_state.symptoms_english = ""
if "vitals" not in st.session_state:
    st.session_state.vitals = {}
if "medical_entities" not in st.session_state:
    st.session_state.medical_entities = None
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = None
if "triage_result" not in st.session_state:
    st.session_state.triage_result = None
if "intake_stage" not in st.session_state:
    st.session_state.intake_stage = 1

def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1
def reset_app():
    for key in ["step", "patient", "symptoms_english", "vitals", "medical_entities", "extracted_text", "triage_result", "intake_stage"]:
        if key in st.session_state: del st.session_state[key]
    st.rerun()

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #2563eb !important;'>🏥 CHW Triage</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    steps = ["1. Registration", "2. Clinical Intake", "3. Triage Report"]
    for i, name in enumerate(steps, 1):
        color = "#2563eb" if st.session_state.step == i else "#94a3b8"
        weight = "700" if st.session_state.step == i else "500"
        st.markdown(f"<div style='color: {color}; font-weight: {weight}; padding: 8px 0; font-size: 1.1rem;'>{name}</div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    if st.session_state.patient.get("name"):
        st.markdown(f"""
        <div style='padding: 15px; border-radius: 8px; border: 1px solid rgba(150, 150, 150, 0.2);'>
            <div style='font-size: 0.8rem; opacity: 0.7; text-transform: uppercase;'>Current Patient</div>
            <div style='font-weight: 700; font-size: 1.1rem;'>{st.session_state.patient.get('name')}</div>
            <div style='font-size: 0.9rem; opacity: 0.8;'>Age: {st.session_state.patient.get('age')} | Sex: {st.session_state.patient.get('sex').capitalize()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Start New Patient", use_container_width=True):
        reset_app()

# ==========================================
# STEP 1: PATIENT REGISTRATION
# ==========================================
if st.session_state.step == 1:
    st.markdown("<h2>Patient Registration</h2>", unsafe_allow_html=True)
    st.write("Enter the demographic details of the patient.")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", value=st.session_state.patient.get("name", ""))
            phone = st.text_input("Contact Number", value=st.session_state.patient.get("phone", ""))
        with col2:
            age = st.number_input("Age *", min_value=0, max_value=120, value=st.session_state.patient.get("age", 30))
            sex = st.selectbox("Sex *", ["male", "female", "other"], index=["male", "female", "other"].index(st.session_state.patient.get("sex", "male")))
            
    col_left, col_right = st.columns([4, 1])
    with col_right:
        if st.button("Continue ➔", type="primary", use_container_width=True):
            if name.strip() == "":
                st.error("Patient name is required.")
            else:
                st.session_state.patient = {"name": name, "age": age, "sex": sex, "phone": phone if phone else None}
                next_step()
                st.rerun()

# ==========================================
# STEP 2: CLINICAL INTAKE
# ==========================================
elif st.session_state.step == 2:
    st.markdown("<h2>Clinical Intake</h2>", unsafe_allow_html=True)
    # --- Symptoms ---
    with st.container(border=True):
        st.markdown("<div class='section-title'>🗣️ Presenting Symptoms</div>", unsafe_allow_html=True)
        
        tab_text, tab_voice = st.tabs(["Text Input", "Voice Upload"])
        
        with tab_text:
            # Use value instead of key to avoid Streamlit's "modified after instantiation" error
            current_text = st.text_area("Describe symptoms:", value=st.session_state.symptoms_english, height=120)
            st.session_state.symptoms_english = current_text
            col_lang, col_btn = st.columns([1, 1])
            with col_lang:
                lang = st.selectbox("Language", ["auto", "en", "bn"], label_visibility="collapsed")
            with col_btn:
                if st.button("Process & Continue ➔", type="primary", use_container_width=True):
                    with st.spinner("Processing..."):
                        try:
                            if not current_text.strip():
                                st.error("Please enter symptoms before continuing.")
                            else:
                                res = api.text_intake(current_text, lang)
                                # Overwrite the session state with the English translation
                                st.session_state.symptoms_english = res["english_text"]
                                st.session_state.show_text_success = True
                                st.session_state.intake_stage = max(st.session_state.intake_stage, 2)
                                st.rerun()
                        except Exception as e:
                            st.error("An error occurred while connecting to the server. Please try again.")

                # Show success message if translation just finished
                if st.session_state.get("show_text_success"):
                    st.success("Text processed successfully!")
                    st.session_state.show_text_success = False
            
        with tab_voice:
            uploaded_audio = st.file_uploader("Upload Audio (transcribes to symptoms text)", type=["wav", "mp3", "m4a"])
            if uploaded_audio:
                st.audio(uploaded_audio)
                if st.button("Transcribe & Continue ➔", type="primary"):
                    with st.spinner("Transcribing..."):
                        try:
                            res = api.voice_intake(uploaded_audio.read(), mime_type=uploaded_audio.type)
                            st.session_state.symptoms_english = res["english_text"]
                            st.session_state.intake_stage = max(st.session_state.intake_stage, 2)
                            st.rerun()
                        except Exception as e: 
                            st.error("An error occurred while connecting to the server. Please try again.")



    if st.session_state.intake_stage >= 2:
        # --- Complementary Document ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>📄 Complementary Document (Optional)</div>", unsafe_allow_html=True)
            uploaded_doc = st.file_uploader("Upload Medical Document, Prescription, or Lab Report", type=["jpg", "jpeg", "png"])
            if uploaded_doc:
                st.image(uploaded_doc, caption="Uploaded Document", width=350)
                
            if st.session_state.intake_stage == 2:
                st.markdown("<br>", unsafe_allow_html=True)
                col_skip, col_extract = st.columns(2)
                with col_skip:
                    if st.button("Skip Document Upload", use_container_width=True):
                        st.session_state.intake_stage = 3
                        st.rerun()
                with col_extract:
                    if uploaded_doc:
                        if st.button("Extract Data & Continue ➔", type="primary", use_container_width=True):
                            with st.spinner("Extracting data..."):
                                try:
                                    res = api.scan_document(uploaded_doc.read(), mime_type=uploaded_doc.type)
                                    
                                    # Save raw text to DB
                                    if res.get("raw_text"):
                                        st.session_state.extracted_text = res["raw_text"]
                                    
                                    # Save medical entities
                                    if res.get("entities"):
                                        st.session_state.medical_entities = res["entities"]
                                        st.success("Extracted medical entities successfully!")
                                    else:
                                        st.success("Document scanned successfully!")
                                    st.session_state.intake_stage = 3
                                    st.rerun()
                                except Exception as e:
                                    st.error("An error occurred while connecting to the server. Please try again.")
                    else:
                        st.button("Extract Data & Continue ➔", type="primary", disabled=True, use_container_width=True)

    if st.session_state.intake_stage >= 3:
        # --- Vitals ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>🩺 Vital Signs (Optional)</div>", unsafe_allow_html=True)
            vcol1, vcol2, vcol3 = st.columns(3)
            with vcol1:
                sys_bp = st.number_input("Systolic BP", min_value=0, max_value=300, value=st.session_state.vitals.get("systolic_bp"))
                dia_bp = st.number_input("Diastolic BP", min_value=0, max_value=200, value=st.session_state.vitals.get("diastolic_bp"))
            with vcol2:
                hr = st.number_input("Heart Rate", min_value=0, max_value=300, value=st.session_state.vitals.get("heart_rate"))
                temp = st.number_input("Temp (°F)", min_value=70.0, max_value=115.0, value=st.session_state.vitals.get("temperature_f"))
            with vcol3:
                spo2 = st.number_input("SpO2 (%)", min_value=0, max_value=100, value=st.session_state.vitals.get("spo2"))
                glucose = st.number_input("Glucose (mg/dL)", min_value=0, max_value=800, value=st.session_state.vitals.get("blood_glucose_mgdl"))

        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_mid, col_right = st.columns([1, 3, 1])
        with col_left:
            if st.button("🡠 Back", use_container_width=True):
                prev_step()
                st.rerun()
        with col_right:
            if st.button("Confirm & Run AI Triage ➔", type="primary", use_container_width=True):
                # Auto-save vitals on confirm! No need to remember to click save anymore.
                v = {"systolic_bp": sys_bp, "diastolic_bp": dia_bp, "heart_rate": hr, "temperature_f": temp, "spo2": spo2, "blood_glucose_mgdl": glucose}
                st.session_state.vitals = {k: val for k, val in v.items() if val is not None and val > 0}
                next_step()
                st.rerun()

# ==========================================
# STEP 3: TRIAGE & REPORT
# ==========================================
elif st.session_state.step == 3:
    st.markdown("<h2>AI Triage Report</h2>", unsafe_allow_html=True)
    
    if st.session_state.triage_result is None:
        with st.spinner("Analyzing clinical data..."):
            try:
                req_payload = {
                    "patient": st.session_state.patient,
                    "symptoms_english": st.session_state.symptoms_english,
                    "extracted_text": st.session_state.get("extracted_text"),
                    "vitals": st.session_state.vitals if st.session_state.vitals else None,
                    "medical_entities": st.session_state.medical_entities
                }
                st.session_state.triage_result = api.run_triage(req_payload)
            except Exception as e:
                st.error("An error occurred while connecting to the server. Please try again.")
                
    if st.session_state.triage_result:
        res = st.session_state.triage_result
        t = res["triage"]
        sid = res["session_id"]
        score = t["triage_score"]
        
        # Action Bar
        col_pdf, col_bn, col_en = st.columns([2, 1, 1])
        with col_pdf:
            try:
                pdf_bytes = api.download_pdf_report(sid)
                st.download_button(
                    label="📄 Download Official PDF",
                    data=pdf_bytes,
                    file_name=f"Triage_Report.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Could not load PDF: {e}\n\n*(If running locally on Windows without Docker, PDF generation requires GTK3 system libraries to be installed.)*")
                
        with col_bn:
            if st.button("🔊 Bengali Audio", use_container_width=True):
                with st.spinner("Generating audio..."):
                    try:
                        audio_bytes = api.download_audio_summary(sid, "bn")
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Audio failed: {e}")
                        
        with col_en:
            if st.button("🔊 English Audio", use_container_width=True):
                with st.spinner("Generating audio..."):
                    try:
                        audio_bytes = api.download_audio_summary(sid, "en")
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Audio failed: {e}")
        
        # Score & Reasoning HTML Card
        referral_html = ""
        if t.get("referral_needed"):
            referral_html = f"<div class='alert-box alert-danger'>🚨 REFERRAL ({str(t.get('referral_urgency')).upper()}): {t.get('referral_type')}</div>"
        else:
            referral_html = "<div class='alert-box alert-success'>✅ ROUTINE CARE: Can be managed locally/at home.</div>"
            
        st.markdown(f"""
        <div class='custom-card' style='padding-top: 30px; padding-bottom: 30px;'>
            <div style='text-align: center;'>
                <div class='triage-badge triage-{score}'>{score} PRIORITY</div>
            </div>
            <p style='font-size: 1.1rem; line-height: 1.6; margin-bottom: 24px;'>
                {t['triage_reasoning']}
            </p>
            <div>
                {referral_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Details Sections (Linear with Expanders)
        
        # Diagnoses
        if t.get("differential_diagnoses"):
            with st.expander("🩺 Differential Diagnoses", expanded=True):
                diag_items = "".join([f"<li><div class='item-title'>{d['condition']} <span class='confidence'>{d['confidence_percent']}%</span></div><div class='item-desc'>{d['key_indicators']}</div></li>" for d in t["differential_diagnoses"]])
                st.markdown(f"<ul class='data-list'>{diag_items}</ul>", unsafe_allow_html=True)
            
        # First Aid
        if t.get("first_aid_steps"):
            with st.expander("🩹 First Aid / Management", expanded=True):
                fa_items = "".join([f"<li>{step}</li>" for step in t["first_aid_steps"]])
                st.markdown(f"<ul class='data-list' style='list-style-type: decimal; padding-left: 20px;'>{fa_items}</ul>", unsafe_allow_html=True)
            
        # Vitals Anomalies
        if res.get("vitals_analysis") and res["vitals_analysis"].get("anomalies"):
            with st.expander("📈 Vitals Anomalies", expanded=True):
                vit_items = "".join([f"<li><div class='item-title' style='color:#ef4444;'>{a['vital_name'].replace('_', ' ').title()}: {a['value']} {a['unit']}</div><div class='item-desc'>{a['message']}</div></li>" for a in res["vitals_analysis"]["anomalies"]])
                st.markdown(f"<ul class='data-list'>{vit_items}</ul>", unsafe_allow_html=True)
            
        # Red Flags
        if t.get("red_flags"):
            with st.expander("🚨 Red Flags to Monitor", expanded=True):
                rf_items = "".join([f"<li style='color: #be123c; font-weight: 500;'>⚠️ {flag}</li>" for flag in t["red_flags"]])
                st.markdown(f"<div style='background-color: #fff1f2; padding: 15px; border-radius: 8px; border: 1px solid #fecdd3;'><ul class='data-list'>{rf_items}</ul></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_reset = st.columns(2)
    with col_back:
        if st.button("🡠 Back to Intake"):
            prev_step()
            st.rerun()
    with col_reset:
        if st.button("Start New Patient 🔄", type="primary"):
            reset_app()
