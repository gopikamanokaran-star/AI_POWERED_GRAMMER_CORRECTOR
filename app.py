import streamlit as st

# Page configuration
st.set_page_config(page_title="AI Grammar Corrector", page_icon="✍️", layout="wide")

# Try importing Groq library
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

groq_api_key = ""
selected_model = ""

if correction_mode == "Real AI Mode (Groq)":
    groq_api_key = st.sidebar.text_input(
        "Enter Groq API Key:", 
        type="password",
        help="Get your free key at https://console.groq.com"
    )
    
    # Dynamically fetch available models directly from Groq API
    if groq_api_key and GROQ_AVAILABLE:
        try:
            client = Groq(api_key=groq_api_key)
            models_data = client.models.list()
            
            # Filter text generation models and exclude guard/whisper models
            available_models = [
                m.id for m in models_data.data 
                if "guard" not in m.id.lower() and "whisper" not in m.id.lower()
            ]
            
            if available_models:
                selected_model = st.sidebar.selectbox("Select Active Groq Model", available_models)
            else:
                st.sidebar.error("No active text models found in your Groq account.")
        except Exception as e:
            st.sidebar.error(f"API Key Error: {e}")

# Main Title Area
st.title("✍️ AI Grammar Corrector & Explainer")
st.write("Correct your grammar, calculate accuracy score, and understand every error!")
st.divider()

# Input Area
user_input = st.text_area("Type or paste your sentence here:", height=120)

if st.button("Check Grammar & Explain", type="primary"):
    if not user_input.strip():
        st.warning("Please enter a sentence first!")
    else:
        with st.spinner("Analyzing grammar, score & explanations..."):
            if correction_mode == "Smart Rules":
                rules = {
                    "he go to school yesterday": {
                        "corrected": "He went to school yesterday.",
                        "error_type": "Past Tense Error",
                        "explanation": "'yesterday' refers to a past event, so the past tense verb 'went' must be used instead of 'go'.",
                        "score": 60
                    },
                    "im learning tomorrow": {
                        "corrected": "I will be learning tomorrow.",
                        "error_type": "Capitalization & Tense Error",
                        "explanation": "'im' should be capitalized to 'I', and 'tomorrow' indicates future action, so 'will be learning' is used.",
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
                    st.info(f"💡 **Explanation:** {res['explanation']}")
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
                    st.info("📌 **Error Type:** Basic Formatting\n\n💡 **Explanation:** Adjusted capitalization and added proper sentence punctuation.")

            else:
                if not GROQ_AVAILABLE:
                    st.error("Groq library missing. Terminal-la 'pip install groq' run pannu.")
                elif not groq_api_key:
                    st.warning("Sidebar-la Groq API Key enter pannunga.")
                elif not selected_model:
                    st.error("Valid model select aagala. Sidebar-la key check pannu da.")
                else:
                    try:
                        client = Groq(api_key=groq_api_key)
                        
                        prompt = f"""You are an expert English grammar corrector and tutor. Analyze the following sentence carefully.

Return your response EXACTLY in this format with these section markers:
SCORE: <a number from 0 to 100 indicating grammatical accuracy>
CORRECTED: <the corrected version of the sentence>
ERROR_TYPE: <type of grammar error, e.g. Tense Error, Subject-Verb Agreement, Spelling, Contraction Error, etc.>
EXPLANATION: <a clear 1-2 line explanation detailing why it was wrong and how to fix it>

Input Sentence: "{user_input}"
"""
                        
                        response = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model=selected_model,
                            temperature=0.2
                        )
                        raw_output = response.choices[0].message.content.strip()
                        
                        # Parsing response
                        score_val = 80
                        corrected_text = user_input
                        error_type = "Grammar Error"
                        explanation = raw_output

                        for line in raw_output.split("\n"):
                            if line.startswith("SCORE:"):
                                try:
                                    score_val = int(''.join(filter(str.isdigit, line.replace("SCORE:", ""))))
                                    score_val = min(max(score_val, 0), 100)
                                except:
                                    pass
                            elif line.startswith("CORRECTED:"):
                                corrected_text = line.replace("CORRECTED:", "").strip()
                            elif line.startswith("ERROR_TYPE:"):
                                error_type = line.replace("ERROR_TYPE:", "").strip()
                            elif line.startswith("EXPLANATION:"):
                                explanation = line.replace("EXPLANATION:", "").strip()

                        # Displaying results
                        st.subheader("📊 Accuracy Analysis")
                        st.metric(label="Grammar Score", value=f"{score_val}%")
                        st.progress(score_val / 100)
                        st.divider()

                        st.success(f"### Corrected Sentence:\n**{corrected_text}**")
                        st.warning(f"📌 **Error Type:** {error_type}")
                        st.info(f"💡 **Explanation:** {explanation}")
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
