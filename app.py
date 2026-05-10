import streamlit as st
from groq import Groq
import json
import re
import pdfplumber

st.set_page_config(
    page_title="AI Resume Job-Fit Scorer",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .stApp { background: #0f0f0f; color: #e8e8e0; }
  section[data-testid="stSidebar"] { display: none; }
  .main .block-container { max-width: 1100px; padding: 2.5rem 2rem; }
  h1 { font-family: 'DM Mono', monospace !important; font-size: 1.6rem !important;
       letter-spacing: -0.02em; color: #e8e8e0 !important; }
  .sub { font-size: 0.85rem; color: #666; margin-top: -0.5rem; margin-bottom: 2rem;
         font-family: 'DM Mono', monospace; }
  textarea { background: #1a1a1a !important; border: 1px solid #2a2a2a !important;
             color: #e8e8e0 !important; font-family: 'DM Mono', monospace !important;
             font-size: 0.8rem !important; border-radius: 6px !important; }
  textarea:focus { border-color: #c8f05a !important; box-shadow: none !important; }
  label { color: #999 !important; font-size: 0.75rem !important;
          font-family: 'DM Mono', monospace !important; letter-spacing: 0.08em; }
  .stButton > button { background: #c8f05a; color: #0f0f0f; border: none;
                       font-family: 'DM Mono', monospace; font-weight: 500;
                       font-size: 0.8rem; letter-spacing: 0.05em;
                       padding: 0.6rem 1.8rem; border-radius: 4px;
                       transition: all 0.15s; width: 100%; }
  .stButton > button:hover { background: #d9ff70; transform: translateY(-1px); }
  .score-ring { text-align: center; padding: 1.5rem 0; }
  .score-num { font-family: 'DM Mono', monospace; font-size: 4rem; font-weight: 500; line-height: 1; }
  .score-label { font-size: 0.7rem; letter-spacing: 0.12em; color: #666;
                 font-family: 'DM Mono', monospace; margin-top: 0.4rem; }
  .verdict-box { background: #1a1a1a; border-left: 3px solid #c8f05a;
                 border-radius: 0 6px 6px 0; padding: 0.9rem 1.1rem;
                 margin: 1rem 0; font-size: 0.85rem; color: #e8e8e0; line-height: 1.6; }
  .section-head { font-family: 'DM Mono', monospace; font-size: 0.65rem;
                  letter-spacing: 0.14em; color: #555; margin: 1.5rem 0 0.7rem;
                  border-bottom: 1px solid #1f1f1f; padding-bottom: 0.4rem; }
  .gap-item { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 5px;
              padding: 0.6rem 0.9rem; margin-bottom: 0.5rem;
              font-size: 0.82rem; color: #e8e8e0; line-height: 1.5; }
  .gap-item::before { content: "↳ "; color: #c8f05a; font-family: 'DM Mono', monospace; }
  .strength-item { background: #141f0a; border: 1px solid #1e3010; border-radius: 5px;
                   padding: 0.6rem 0.9rem; margin-bottom: 0.5rem;
                   font-size: 0.82rem; color: #a8d870; line-height: 1.5; }
  .strength-item::before { content: "✓ "; font-family: 'DM Mono', monospace; }
  .bullet-before { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 5px;
                   padding: 0.7rem 0.9rem; margin-bottom: 0.4rem;
                   font-size: 0.8rem; color: #666; font-family: 'DM Mono', monospace; line-height: 1.5; }
  .bullet-after { background: #141f0a; border: 1px solid #2a2a2a; border-radius: 5px;
                  padding: 0.7rem 0.9rem; margin-bottom: 1rem;
                  font-size: 0.8rem; color: #a8d870; font-family: 'DM Mono', monospace; line-height: 1.5; }
  .arrow-label { font-size: 0.65rem; color: #555; font-family: 'DM Mono', monospace;
                 letter-spacing: 0.1em; margin: 0.25rem 0 0.2rem; }
  .result-card { background: #141414; border: 1px solid #222; border-radius: 10px;
                 padding: 1.5rem; height: 100%; }
  .upload-box { background: #1a1a1a; border: 1px dashed #2a2a2a; border-radius: 6px;
                padding: 1rem; margin-top: 0.5rem; text-align: center; }
  .pdf-success { background: #141f0a; border: 1px solid #1e3010; border-radius: 5px;
                 padding: 0.6rem 0.9rem; font-size: 0.82rem; color: #a8d870;
                 margin-top: 0.5rem; font-family: 'DM Mono', monospace; }
  div[data-testid="stMarkdownContainer"] p { font-size: 0.85rem; color: #999; line-height: 1.7; }
  .stTextArea { margin-bottom: 0.5rem; }
  .stTabs [data-baseweb="tab-list"] { background: #1a1a1a; border-radius: 6px; padding: 4px; gap: 4px; }
  .stTabs [data-baseweb="tab"] { background: transparent; color: #666; border-radius: 4px;
                                  font-family: 'DM Mono', monospace; font-size: 0.75rem; }
  .stTabs [aria-selected="true"] { background: #c8f05a !important; color: #0f0f0f !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# AI Resume Job-Fit Scorer")
st.markdown('<p class="sub">// paste a job description + upload your resume PDF or paste text → get a fit score, gap analysis & rewritten bullets</p>', unsafe_allow_html=True)


def extract_text_from_pdf(pdf_file) -> str:
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()


def analyze_resume(job_desc: str, resume: str) -> dict:
    client = Groq(api_key=st.session_state.api_key)

    prompt = f"""You are a senior talent acquisition expert and career coach.

Analyze how well the resume matches the job description. Return ONLY valid JSON — no markdown fences, no extra text.

JSON format:
{{
  "fit_score": <integer 0-100>,
  "verdict": "<2-3 sentence overall assessment>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "gaps": ["<gap 1>", "<gap 2>", "<gap 3>", "<gap 4>"],
  "rewritten_bullets": [
    {{"original": "<original bullet>", "improved": "<improved bullet tailored to JD>"}},
    {{"original": "<original bullet>", "improved": "<improved bullet tailored to JD>"}},
    {{"original": "<original bullet>", "improved": "<improved bullet tailored to JD>"}}
  ],
  "keywords_missing": ["<keyword>", "<keyword>", "<keyword>", "<keyword>", "<keyword>"]
}}

Rules:
- fit_score: be honest, not generous. 60+ = decent fit, 80+ = strong fit.
- gaps: specific skills, experience, or qualifications clearly required but absent.
- rewritten_bullets: pick the 3 weakest bullets from the resume and rewrite them to align with the JD language and keywords. Make them quantified and impactful.
- keywords_missing: ATS keywords in the JD not found in the resume.

JOB DESCRIPTION:
{job_desc}

RESUME:
{resume}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.3
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


def score_color(score: int) -> str:
    if score >= 80:
        return "#c8f05a"
    elif score >= 60:
        return "#f0c85a"
    else:
        return "#f05a5a"


if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.expander("⚙  API key", expanded=not st.session_state.api_key):
    key_input = st.text_input(
        "Groq API key",
        type="password",
        value=st.session_state.api_key,
        placeholder="gsk_...",
        help="Get yours free at console.groq.com"
    )
    if key_input:
        st.session_state.api_key = key_input

col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown('<div class="section-head">JOB DESCRIPTION</div>', unsafe_allow_html=True)
    job_desc = st.text_area(
        "job_desc",
        height=280,
        placeholder="Paste the full job description here...",
        label_visibility="collapsed"
    )

with col2:
    st.markdown('<div class="section-head">YOUR RESUME</div>', unsafe_allow_html=True)
    resume_tab1, resume_tab2 = st.tabs(["📄 Upload PDF", "✏️ Paste Text"])

    resume_text = ""

    with resume_tab1:
        uploaded_pdf = st.file_uploader(
            "Upload your resume PDF",
            type=["pdf"],
            label_visibility="collapsed"
        )
        if uploaded_pdf:
            try:
                resume_text = extract_text_from_pdf(uploaded_pdf)
                st.markdown(f'<div class="pdf-success">✓ PDF loaded — {len(resume_text)} characters extracted from {uploaded_pdf.name}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not read PDF: {str(e)}")

    with resume_tab2:
        pasted_text = st.text_area(
            "resume_text",
            height=220,
            placeholder="Paste your resume text here...",
            label_visibility="collapsed"
        )
        if pasted_text:
            resume_text = pasted_text

btn_col = st.columns([1, 2, 1])[1]
with btn_col:
    analyze_btn = st.button("ANALYZE FIT →")

if analyze_btn:
    if not st.session_state.api_key:
        st.error("Add your Groq API key above first.")
    elif not job_desc.strip():
        st.warning("Paste a job description to continue.")
    elif not resume_text.strip():
        st.warning("Upload a PDF or paste your resume text to continue.")
    else:
        with st.spinner("Analyzing fit..."):
            try:
                result = analyze_resume(job_desc, resume_text)
                score = result["fit_score"]
                color = score_color(score)

                st.markdown("---")

                r1, r2 = st.columns([1, 2], gap="medium")

                with r1:
                    st.markdown(f"""
                    <div class="result-card score-ring">
                      <div class="score-num" style="color:{color}">{score}</div>
                      <div class="score-label">FIT SCORE / 100</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="section-head">MISSING KEYWORDS</div>', unsafe_allow_html=True)
                    kw_html = " ".join(
                        f'<span style="display:inline-block;background:#1a1a1a;border:1px solid #2a2a2a;'
                        f'border-radius:3px;padding:3px 8px;font-size:0.72rem;color:#f05a5a;'
                        f'font-family:\'DM Mono\',monospace;margin:2px;">{kw}</span>'
                        for kw in result.get("keywords_missing", [])
                    )
                    st.markdown(kw_html, unsafe_allow_html=True)

                with r2:
                    st.markdown(f'<div class="verdict-box">{result["verdict"]}</div>', unsafe_allow_html=True)

                    s_col, g_col = st.columns(2, gap="small")

                    with s_col:
                        st.markdown('<div class="section-head">STRENGTHS</div>', unsafe_allow_html=True)
                        for s in result.get("strengths", []):
                            st.markdown(f'<div class="strength-item">{s}</div>', unsafe_allow_html=True)

                    with g_col:
                        st.markdown('<div class="section-head">GAPS TO ADDRESS</div>', unsafe_allow_html=True)
                        for g in result.get("gaps", []):
                            st.markdown(f'<div class="gap-item">{g}</div>', unsafe_allow_html=True)

                st.markdown('<div class="section-head" style="margin-top:2rem">REWRITTEN BULLETS</div>', unsafe_allow_html=True)
                st.markdown('<p style="font-size:0.78rem;color:#555;margin-bottom:1rem;">3 of your weakest bullets rewritten to match the job description language and keywords.</p>', unsafe_allow_html=True)

                b_cols = st.columns(3, gap="medium")
                for i, bullet in enumerate(result.get("rewritten_bullets", [])[:3]):
                    with b_cols[i]:
                        st.markdown(f'<div class="arrow-label">BEFORE</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="bullet-before">{bullet["original"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="arrow-label">↓ AFTER</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="bullet-after">{bullet["improved"]}</div>', unsafe_allow_html=True)

            except json.JSONDecodeError:
                st.error("Could not parse the AI response. Try again.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("""
<div style="margin-top:3rem;padding-top:1rem;border-top:1px solid #1f1f1f;
     font-family:'DM Mono',monospace;font-size:0.7rem;color:#333;text-align:center;">
  built with Groq API · streamlit · python &nbsp;·&nbsp; your resume is never stored
</div>
""", unsafe_allow_html=True)
