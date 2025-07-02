import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv
import os
import tempfile # For handling temporary files

# Load environment variables from .env file
load_dotenv()

# Constants
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest" # Model supporting File API and large contexts
SESSION_STATE_SUMMARY = 'summary'
SESSION_STATE_CHAT_HISTORY = 'chat_history'
SESSION_STATE_LAST_FILES_KEY = 'last_processed_files_key'

# Function to list available Gemini models (for diagnostics)
def list_available_gemini_models():
    """Lists available Gemini models that support 'generateContent'."""
    try:
        st.write("🔍 Checking available Gemini models...")
        models_info = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models_info.append(f"  - Name: `{m.name}` (Display: {m.display_name})")
        
        if models_info:
            st.info("✅ Available models supporting 'generateContent':\n" + "\n".join(models_info))
        else:
            st.warning("⚠️ No models found that explicitly support 'generateContent'. This might indicate an issue with your API key, project setup, or library version.")
        
        all_models_info = [f"  - Name: `{m.name}` (Display: {m.display_name}, Methods: {m.supported_generation_methods})" for m in genai.list_models()]
        if not all_models_info:
            st.error("🚫 No models returned at all. Please double-check your API key and network connection.")
        else:
            with st.expander("📋 See full list of all detected models"):
                st.markdown("\n".join(all_models_info))

    except Exception as e:
        st.error(f"🔴 Error listing models: {e}")

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("🔴 GEMINI_API_KEY not found. Please set it in your .env file or environment variables.")
    st.stop()

gemini_model_configured = False
try:
    genai.configure(api_key=api_key)
    # Attempt to initialize the primary model to see if it's valid
    genai.GenerativeModel(GEMINI_MODEL_NAME) 
    gemini_model_configured = True
except Exception as e:
    st.error(f"🔴 Error configuring Gemini API or accessing the primary model ('{GEMINI_MODEL_NAME}'): {e}")
    list_available_gemini_models() # Provide diagnostic info
    st.info(f"ℹ️ The application tried to use '{GEMINI_MODEL_NAME}'. If it's not listed above or if errors persist, please check your API key, ensure the model is available in your region, and that your 'google-generativeai' library is up-to-date (`pip install -U google-generativeai`). You might need to update `GEMINI_MODEL_NAME` in the script.")
    st.stop() # Stop if the primary model can't be configured

# Helper to generate a key for uploaded files for change detection
def generate_file_key(pdf_docs_list):
    if not pdf_docs_list:
        return None
    # Sort by file_id to ensure order doesn't affect the key
    return tuple(sorted((doc.name, doc.size, doc.file_id) for doc in pdf_docs_list))

# Cache the Gemini model instance
@st.cache_resource
def get_gemini_model():
    if not gemini_model_configured: # Should not happen if startup checks pass, but as a safeguard
        st.error("🔴 Gemini model was not configured successfully. Please check startup errors.")
        return None
    return genai.GenerativeModel(GEMINI_MODEL_NAME)

# Function to summarize text using Gemini
@st.cache_data(show_spinner=False) # Spinner handled manually
def summarize_with_gemini(_streamlit_uploaded_files, summary_length="concise", output_format="paragraph"):
    """
    Summarizes content from Streamlit UploadedFile objects using Gemini File API.
    _streamlit_uploaded_files is prefixed with _ to indicate it's used for caching key generation
    but the actual file objects are processed fresh.
    """
    try:
        model = get_gemini_model()
        if not model:
            return None # Error already shown by get_gemini_model or startup

        uploaded_gemini_files = []
        temp_file_paths = []

        st.write("⏳ Uploading files to Gemini...")
        for uploaded_file in _streamlit_uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_file_paths.append(tmp.name)
            
            # st.info(f"Uploading {uploaded_file.name} ({uploaded_file.size} bytes) to Gemini File API...")
            gemini_file = genai.upload_file(path=tmp.name, display_name=uploaded_file.name)
            uploaded_gemini_files.append(gemini_file)
            # st.info(f"✅ Uploaded {gemini_file.display_name} as {gemini_file.name}")

        if not uploaded_gemini_files:
            st.error("❌ No files were successfully uploaded to Gemini.")
            return None
        st.success("✅ Files uploaded to Gemini successfully.")

        prompt = f"You are an expert summarizer. Summarize the following document."
        if summary_length == "brief" or summary_length == "concise":
            prompt += " Provide a concise summary (1-2 paragraphs)."
        elif summary_length == "detailed":
            prompt += " Provide a detailed summary (multiple paragraphs, covering key aspects thoroughly)."
        
        if output_format == "bullet_points":
            prompt += " Present the summary as a list of key bullet points."
        else: # paragraph
            prompt += " Present the summary in well-structured paragraphs."

        # Construct content parts: all file objects first, then the text prompt
        content_parts = uploaded_gemini_files + [prompt]
        
        response = model.generate_content(content_parts)
        return response.text
    except Exception as e:
        st.error(f"❌ Gemini API Error (Summarization): {str(e)}")
        return None
    finally:
        # Clean up temporary files
        for path in temp_file_paths:
            if os.path.exists(path):
                os.remove(path)
        # Consider deleting files from Gemini File API if not needed for long, but for Q&A over summary, it's fine.

# Function to handle user questions based on summary
@st.cache_data(show_spinner=False) # Spinner handled manually
def handle_user_question(question, summary, chat_history=None):
    try:
        model = get_gemini_model()
        if not model:
            return None # Error already shown

        
        prompt_parts = [
            "You are a helpful AI assistant. Your task is to answer the user's CURRENT QUESTION based *only* on the provided CONTEXT (a summary of a document).",
            "If the answer cannot be found in the CONTEXT, clearly state that the information is not available in the summary.",
            "Do not use any external knowledge or make assumptions beyond the provided text."
        ]
        prompt_parts.append(f"\nCONTEXT (Document Summary):\n{summary}\n")

        if chat_history:
            prompt_parts.append("PREVIOUS CONVERSATION HISTORY (for reference only):")
            for q_hist, a_hist in chat_history:
                prompt_parts.append(f"User: {q_hist}")
                prompt_parts.append(f"Assistant: {a_hist}")
        
        prompt_parts.append(f"\nCURRENT QUESTION:\n{question}")
        full_prompt = "\n\n".join(prompt_parts)
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ Gemini API Error (Q&A): {str(e)}")
        return None

# Streamlit app
def main():
    st.set_page_config(page_title="Automated Document Summarizer & Q&A", layout="wide")
    st.header("📄 Automated Document Summarizer & Q&A with Gemini")
    st.markdown("Upload PDF documents, get smart summaries, and ask questions directly related to the summarized content!")

    # Initialize session state variables
    for key, default_value in [
        (SESSION_STATE_SUMMARY, None),
        (SESSION_STATE_CHAT_HISTORY, []),
        (SESSION_STATE_LAST_FILES_KEY, None)
    ]:
        if key not in st.session_state:
            st.session_state[key] = default_value

    with st.sidebar:
        st.subheader("⚙️ Controls & Configuration")
        pdf_docs = st.file_uploader("📥 Upload PDF Files", accept_multiple_files=True, type="pdf", key="pdf_uploader")

        st.subheader("Summarization Options")
        summary_length_option = st.radio("Summary Length:", ("Concise", "Detailed"), index=0, key="summary_length")
        summary_format_option = st.radio("Summary Format:", ("Paragraph", "Bullet Points"), index=0, key="summary_format")

        if st.button("✨ Generate Summary", type="primary", use_container_width=True, key="summarize_button"):
            if pdf_docs:
                current_files_key = generate_file_key(pdf_docs)
                
                # Always try to summarize if button is pressed and files are present.
                # Caching of summarize_with_gemini will handle redundancy if files haven't changed.
                # We pass pdf_docs directly now.
                with st.spinner(f"⏳ Preparing and generating {summary_length_option.lower()} summary in {summary_format_option.lower()} format..."):
                    # Pass the actual Streamlit UploadedFile objects
                    # The caching key for summarize_with_gemini will be based on these.
                    # To make caching effective with UploadedFile objects, we might need to pass
                    # a hashable representation like current_files_key or tuple of (name, size, id)
                    # For now, let's pass pdf_docs and rely on @st.cache_data's handling.
                    summary = summarize_with_gemini(
                        pdf_docs, # Pass the list of Streamlit UploadedFile objects
                        summary_length_option.lower(),
                        summary_format_option.lower().replace(" ", "_")
                    )
                    if summary:
                        st.session_state[SESSION_STATE_SUMMARY] = summary
                        st.success("✅ Summary generated successfully!")
                    else:
                        # Error message already shown by summarize_with_gemini
                        st.session_state[SESSION_STATE_SUMMARY] = None
            else:
                st.warning("⚠️ Please upload at least one PDF file.")

        if st.button("🗑️ Clear All & Reset", use_container_width=True, key="clear_button"):
            st.session_state[SESSION_STATE_SUMMARY] = None
            st.session_state[SESSION_STATE_CHAT_HISTORY] = []
            st.session_state[SESSION_STATE_LAST_FILES_KEY] = None
            # Clearing st.session_state.pdf_uploader (if using a key for it) might be needed
            # or simply rely on rerun to reset the uploader widget's visual state.
            st.success("🗑️ All data cleared. Upload new files or change options.")
            st.rerun()

    # Main content area
    if st.session_state[SESSION_STATE_SUMMARY]:
        st.subheader("📝 Document Summary")
        st.markdown(st.session_state[SESSION_STATE_SUMMARY]) # Use markdown for better formatting

        st.download_button(
            label="📥 Download Summary as TXT",
            data=st.session_state[SESSION_STATE_SUMMARY],
            file_name="document_summary.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_summary_button"
        )

        st.subheader("💬 Ask Questions About the Summary")

        # Display chat history
        if st.session_state[SESSION_STATE_CHAT_HISTORY]:
            for i, (q, a) in enumerate(st.session_state[SESSION_STATE_CHAT_HISTORY]):
                st.markdown(f"<div style='text-align: right; margin-bottom: 5px;'><span style='background-color: #D6EAF8; color: #154360; padding: 10px; border-radius: 15px 15px 0 15px;'><b>You:</b> {q}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: left; margin-bottom: 10px;'><span style='background-color: #E9F7EF; color: #145A32; padding: 10px; border-radius: 15px 15px 15px 0;'><b>Gemini:</b> {a}</span></div>", unsafe_allow_html=True)

        user_question = st.chat_input("Type your question here based on the summary...", key="user_question_input")

        if user_question:
            with st.spinner("🤖 Gemini is thinking..."):
                # Pass a limited history to avoid overly long prompts (e.g., last 3 exchanges)
                history_for_prompt = st.session_state[SESSION_STATE_CHAT_HISTORY][-3:]
                
                answer = handle_user_question(user_question, st.session_state[SESSION_STATE_SUMMARY], history_for_prompt)
            
            if answer:
                st.session_state[SESSION_STATE_CHAT_HISTORY].append((user_question, answer))
                st.rerun() # Rerun to display the new message immediately
            else:
                # Error already shown by handle_user_question
                st.warning("⚠️ Could not get an answer. Please try rephrasing or check API status if errors persist.")
    
    # elif st.session_state[SESSION_STATE_PROCESSED_TEXT] and not st.session_state[SESSION_STATE_SUMMARY]: # This condition is no longer relevant
    #     st.info("ℹ️ Text has been extracted from your PDF(s). Click '✨ Generate Summary' in the sidebar to view the summary.")
    
    elif not pdf_docs: # Check if pdf_docs is empty from the uploader
         st.info("👋 Welcome! Please upload PDF documents using the sidebar to get started.")

if __name__ == "__main__":
    main()
