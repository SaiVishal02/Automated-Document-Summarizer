
# 📄 Automated Document Summarizer using Gemini AI

A simple and interactive Streamlit web application that allows users to:
- Upload PDF documents
- Automatically generate concise summaries using **Gemini 1.5 Flash**
- Ask questions about the document and get intelligent answers using **Gemini 1.5 Pro**

---

## 🚀 Features

- 🧠 **Summarize PDFs** instantly using Google Gemini API
- 💬 **Ask Questions** about the summarized content
- 🔒 Secure API key handling via `.env` file
- 🖼️ Minimalistic and clean Streamlit UI

---

## 📸 Demo Preview

> 📌 *Upload a PDF ➡️ Click "Summarize PDF" ➡️ View Summary ➡️ Ask Questions*

![PDF Summarization Screenshot](assets/demo_screenshot.png) *(add your own screenshot)*

---

## 📁 Project Structure

```
automated-document-summarizer/
│
├── app.py                 # Main Streamlit app
├── .env                  # (Not pushed) API key goes here
├── requirements.txt       # Project dependencies
└── README.md              # You're reading this!
```

---

## 🧰 Tech Stack

- **Python 3.8+**
- **Streamlit** – Web framework
- **Google Generative AI SDK** – for Gemini models
- **dotenv** – To manage API key securely

---

## 🔐 API Key Setup

1. Go to: [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Generate your **Gemini API Key**
3. Create a `.env` file in your project root:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

---

## ⚙️ How It Works

### 🔄 Flow Overview

```
[Upload PDF] ➡️ [File Saved Temporarily] ➡️ [Sent to Gemini] ➡️ [Summary Displayed]
                                                       ⬇️
                                               [User Asks Questions]
                                                       ⬇️
                                        [Answers based on summary context]
```

---

## 🧪 How to Run Locally (VS Code or Terminal)

### ✅ Prerequisites

- Python 3.8+
- VS Code or any code editor
- A valid Gemini API key

### 🚀 Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/automated-document-summarizer.git
cd automated-document-summarizer

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Gemini API key
# Create a `.env` file and paste your API key:
# GEMINI_API_KEY=your_key_here

# 5. Run the Streamlit app
streamlit run app.py
```

🔗 Open browser: http://localhost:8501

---

## 📦 `requirements.txt`

```txt
streamlit
google-generativeai
python-dotenv
```

Install with:
```bash
pip install -r requirements.txt
```

---

## ☁️ Optional: Deploy on Streamlit Cloud

1. Push this project to a public GitHub repo
2. Visit: https://streamlit.io/cloud
3. Deploy your GitHub repo
4. Add your **GEMINI_API_KEY** in **Secrets Manager**

---

## ❗ Important Notes

- Don't commit your `.env` file!
- Add `.env` to `.gitignore`:
  ```
  .env
  ```

---

## 📚 Example Usage

- **PDF**: Research papers, reports, essays, or documentation
- **Use Case**: Students, professionals, or developers who want quick insights from long documents

---

## 🤝 Contribution

Feel free to:
- Fork the repo
- Add improvements
- Submit pull requests!

---

## 📄 License

This project is licensed under the **MIT License** – feel free to use and modify.

---

## ✨ Author

Built by [Your Name](https://github.com/yourusername) 🚀
