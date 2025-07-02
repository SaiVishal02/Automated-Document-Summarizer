import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import pathlib
import tempfile

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client with the API key
client = genai.Client(api_key=API_KEY)

# Upload and summarize PDF using Gemini's File API
def summarize_with_uploaded_file(file_path):
    try:
        uploaded_file = client.files.upload(file=file_path)
        response = client.models.generate_content(
            model="models/gemini-1.5-flash-latest",
            contents=[uploaded_file, "Summarize this document"]
        )
        return response.text
    except Exception as e:
        return f"❌ Error during summarization: {str(e)}"

# Q&A based on summarized content
def handle_user_question(question, summary):
    try:
        model = client.models.get("models/gemini-1.5-pro-latest")
        response = model.generate_content(
            contents=[{"role": "user", "parts": [f"Context:\n{summary}\n\nQuestion:\n{question}"]}]
        )
        return response.text
    except Exception as e:
        return f"❌ Error during Q&A: {str(e)}"

# Streamlit web app
def main():
    st.set_page_config(page_title="Automated Document Summarizer")
    st.title("📄 Automated Document Summarizer using Gemini AI")

    # File uploader
    pdf_file = st.file_uploader("📥 Upload a PDF file", type="pdf")

    if st.button("Summarize PDF"):
        if pdf_file:
            with st.spinner("Summarizing... Please wait."):
                # Save PDF to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(pdf_file.read())
                    tmp_path = pathlib.Path(tmp_file.name)

                summary = summarize_with_uploaded_file(tmp_path)
                st.session_state["summary"] = summary
                st.success("✅ Summary generated successfully!")
        else:
            st.warning("⚠️ Please upload a PDF file before summarizing.")

    # Display summary if available
    if "summary" in st.session_state:
        st.subheader("📝 PDF Summary")
        st.write(st.session_state["summary"])

        # Question input
        user_question = st.text_input("❓ Ask a question about the document:")
        if user_question:
            with st.spinner("Thinking..."):
                response = handle_user_question(user_question, st.session_state["summary"])
                st.subheader("💬 Gemini's Answer")
                st.write(response)

# Run the app
if __name__ == "__main__":
    main()
