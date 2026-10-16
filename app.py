import streamlit as st
import re

# Page Configuration
st.set_page_config(page_title="AI Grammar Corrector & Explainer", page_icon="✍️", layout="wide")

# Check availability of Groq library
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Sidebar Configuration
st.sidebar.title("⚙️ Settings")
correction_mode = st.sidebar.selectbox(
    "Choose Correction Mode",
    ["Smart Rules", "Real AI Mode (Groq)"]
)

# Explanation Language Option (English / Thanglish)
expl_lang = st.sidebar.selectbox(
    "Explanation Language",
    ["English", "Thanglish (Tamil-English)"]
)

groq_api_key = ""
selected_model = ""

if correction_mode == "Real AI Mode (Groq)":
    groq_api_key = st.sidebar.text_input(
        "Enter Groq API Key:", 
        type="password",
        help="Get your free key at https://console.groq.com"
    )
    
    if groq_api_key and GROQ_AVAILABLE:
        try:
            client = Groq(api_key=groq_api_key)
            models_data = client.models.list()
            # Strict Filtering: Prefer high-performance Llama models to avoid parsing & rate limit issues
            available_models = [
                m.id for m in models_data.data 
                if "llama" in m.id.lower() 
                and "guard" not in m.id.lower() 
                and "vision" not in m.id.lower()
            ]
            if not available_models:
                available_models = [
                    m.id for m in models_data.data 
                    if ("mixtral" in m.id.lower() or "gemma" in m.id.lower())
                    and "guard" not in m.id.lower()
                ]

            if available_models:
                selected_model = st.sidebar.selectbox("Select Active Groq Model", available_models)
            else:
                st.sidebar.error("No valid Llama/Gemma models found in your Groq account.")
        except Exception as e:
            st.sidebar.error(f"API Key Error: {e}")

# Main Interface Title & Description
st.title("✍️ AI Grammar Corrector & Explainer")
st.write("Correct your grammar, calculate accuracy scores, and understand every linguistic error in real-time!")
st.divider()

# User Input Text Area
user_input = st.text_area("Type or paste your sentence here:", height=120)

if st.button("Check Grammar & Explain", type="primary"):
    if not user_input.strip():
        st.warning("Please enter a sentence first!")
    else:
        with st.spinner("Analyzing grammar, accuracy score & explanations..."):
            if correction_mode == "Smart Rules":
                rules = {
                    "he go to school yesterday": {
                        "corrected": "He went to school yesterday.",
                        "error_type": "Past Tense Error",
                        "explanation": "'yesterday' indicates past time; use past tense verb 'went' instead of 'go'." if expl_lang == "English" else "'-la 'yesterday' irukkuradhaala past tense verb 'went' dhaan use pannanum.",
                        "score": 60
                    },
                    "im learning yesterday": {
                        "corrected": "I was learning yesterday.",
                        "error_type": "Tense & Capitalization Error",
                        "explanation": "'im' should be capitalized and corrected to 'I was' to match 'yesterday'." if expl_lang == "English" else "'im'-a 'I was' nu maathanum, yenna 'yesterday' vandhu past time-a kaattudhu.",
                        "score": 50
                    }
                }
                cleaned = user_input.strip().lower()
                
                if cleaned in rules:
                    res = rules[cleaned]
                    score = res['score']
                    st.subheader("📊 Accuracy Analysis")
                    st.metric(label="Grammar Accuracy Score", value=f"{score}%")
                    st.progress(score / 100)
                    st.divider()
                    
                    st.success(f"### Corrected Sentence:\n{res['corrected']}")
                    st.warning(f"📌 **Error Type:** {res['error_type']}")
                    st.info(f"💡 **Explanation ({expl_lang}):** {res['explanation']}")
                else:
                    corrected = user_input.strip().capitalize()
                    if not corrected.endswith(('.', '?', '!')):
                        corrected += '.'
                    
                    score = 90 if corrected != user_input else 100
                    st.subheader("📊 Accuracy Analysis")
                    st.metric(label="Grammar Accuracy Score", value=f"{score}%")
                    st.progress(score / 100)
                    st.divider()
                    
                    st.success(f"### Corrected Sentence:\n{corrected}")
                    st.info(f"📌 **Error Type:** Basic Formatting\n\n💡 **Explanation ({expl_lang}):** " + 
                            ("Adjusted initial capitalization and added proper sentence punctuation." if expl_lang == "English" else "First letter capital panni, proper ending punctuation add pannirukken."))

            else:
                if not GROQ_AVAILABLE:
                    st.error("Groq library missing. Install via 'pip install groq'.")
                elif not groq_api_key:
                    st.warning("Please enter your Groq API Key in the sidebar settings.")
                elif not selected_model:
                    st.error("No valid model selected. Please check your API key and connection.")
                else:
                    try:
                        client = Groq(api_key=groq_api_key)
                        
                        # Strict Language Instruction
                        if expl_lang == "Thanglish (Tamil-English)":
                            lang_inst = "Write the EXPLANATION strictly in friendly Thanglish (Tamil words typed in English, e.g., 'Indha sentence-la verb tense thappu irukku, adhanaala change pannirukkom'). Do NOT use standard English for explanation."
                        else:
                            lang_inst = "Write the EXPLANATION in clear, professional English."

                        system_message = f"""You are an expert AI English Grammar Corrector and Language Tutor. 
Your primary job is to thoroughly fix ALL grammar, tense, spelling, capitalization, and punctuation errors. 

Rules:
1. Always fix the sentence properly.
2. {lang_inst}
3. Output format must be strictly plain text following these line keys:

SCORE: <0 to 100 integer>
CORRECTED: <fully grammatically corrected sentence>
ERROR_TYPE: <category of error>
EXPLANATION: <detailed 1-2 line explanation>"""

                        prompt = f'Analyze and correct this sentence: "{user_input}"'

                        response = client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": prompt}
                            ],
                            model=selected_model,
                            temperature=0.2,
                            max_tokens=350
                        )
                        raw_output = response.choices[0].message.content.strip()
                        
                        # Fallback parsing regex
                        score_val = 70
                        corrected_text = user_input
                        error_type = "Grammar Error"
                        explanation = "Grammar corrections were made to improve sentence structure and clarity."

                        for line in raw_output.split("\n"):
                            line_clean = line.strip()
                            if line_clean.upper().startswith("SCORE:"):
                                num = re.findall(r'\d+', line_clean)
                                if num:
                                    score_val = min(max(int(num[0]), 0), 100)
                            elif line_clean.upper().startswith("CORRECTED:"):
                                corrected_text = re.sub(r'^CORRECTED:\s*', '', line_clean, flags=re.I)
                            elif line_clean.upper().startswith("ERROR_TYPE:"):
                                error_type = re.sub(r'^ERROR_TYPE:\s*', '', line_clean, flags=re.I)
                            elif line_clean.upper().startswith("EXPLANATION:"):
                                explanation = re.sub(r'^EXPLANATION:\s*', '', line_clean, flags=re.I)

                        # If explanation was still empty, use raw output fallback
                        if not explanation or explanation == raw_output:
                            explanation = raw_output

                        # Rendering Results
                        st.subheader("📊 Accuracy Analysis")
                        st.metric(label="Grammar Score", value=f"{score_val}%")
                        st.progress(score_val / 100)
                        st.divider()

                        st.success(f"### Corrected Sentence:\n**{corrected_text}**")
                        st.warning(f"📌 **Error Type:** {error_type}")
                        st.info(f"💡 **Explanation ({expl_lang}):** {explanation}")
                        
                    except Exception as e:
                        st.error(f"API Execution Error: {e}")
