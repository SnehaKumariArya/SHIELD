# S.H.I.E.L.D. | Secure Campus Intelligence & Cyber Awareness

S.H.I.E.L.D. is a full-stack cybersecurity reporting ecosystem designed for university campuses. It allows students to report incidents anonymously while utilizing AI for triage and privacy-focused metadata scrubbing.

## 🚀 Key Features
- **AI Triage Engine:** Automatically classifies reports into Cyber or Non-Cyber categories using keyword analysis.
- **Privacy Shield:** Programmatically strips EXIF and GPS metadata from image evidence using Python's Pillow library.
- **Secure Authentication:** Real-time SMTP integration for OTP email verification.
- **Investigator Vault:** A live admin dashboard for status management and case purging.
- **Awareness Hub:** An educational center with an integrated AI Chatbot.

## 🛠️ Tech Stack
- **Frontend:** HTML5, Tailwind CSS, JavaScript (ES6+)
- **Backend:** Python, FastAPI, Uvicorn
- **Database:** SQLite3
- **Tools:** SMTP (Gmail API), Pillow (Imaging)

## 📦 Installation
1. Clone the repo: `git clone https://github.com/yourusername/SHIELD-Project.git`
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Run the backend: `python -m uvicorn main:app --reload`
4. Open `app/index.html` in your browser.