import streamlit as st

st.title("AI-Powered Grammar Corrector")

st.write("Improve your English writing with AI")

text = st.text_area("Enter your sentence:")

if st.button("Check Grammar"):
    if text:
        st.success("Your sentence has been submitted for grammar checking.")
    else:
        st.warning("Please enter a sentence.")