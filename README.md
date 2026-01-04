🚀 AI-Powered Talent–Job Fit Recommendation & Recruitment Optimization Tool
 To run this project : https://78p98pk9-5000.inc1.devtunnels.ms/
 https://ominous-robot-p4w5g4455xw265xj-5000.app.github.dev/
📌 Overview

The AI-Powered Talent–Job Fit Recommendation & Recruitment Optimization Tool is a web-based application that automates resume screening and job matching using Artificial Intelligence and Natural Language Processing (NLP).

The system analyzes resumes and job descriptions, performs semantic matching using Google Gemini (LLM), and provides an explainable match score, skill analysis, and a modern result dashboard to assist recruiters in decision-making.

🎯 Objectives

Automate resume screening

Reduce human bias in recruitment

Match candidates to job roles using AI

Provide explainable and transparent AI results

Improve recruitment efficiency

🧠 AI Used

Google Gemini (Large Language Model)

Used for:

Resume understanding

Skill extraction

Semantic job–candidate matching

Explainable AI output

🛠️ Technologies Used
Backend

Python 3.x

Flask

Frontend

HTML5

CSS3

Jinja2 Templates

Database

SQLite

AI & NLP

Google Gemini API

Tools

Git & GitHub

VS Code

🏗️ System Architecture
User
 ↓
Web Interface (HTML/CSS)
 ↓
Flask Backend
 ↓
Gemini AI (LLM)
 ↓
Match Score + Explanation
 ↓
Result Dashboard
 ↓
SQLite Database

✨ Features
🔐 Authentication

User registration & login

Secure password hashing

Session-based authentication

📄 Resume Upload

Accepts PDF resumes only

File validation & secure storage

🧠 AI Resume–Job Matching

Skill extraction

Experience relevance analysis

Semantic matching (not keyword-based)

📊 Result Dashboard

Match percentage progress bar

Skill analysis (matched & missing skills)

Explainable AI output

Clean and modern UI

📈 Candidate Ranking (Optional)

Rank multiple resumes by match score

📁 Project Structure
AI-Powered-Talent-Job-Fit-Recommendation/
│
├── main.py
├── ai_engine.py
├── pdf_parser.py
├── auth.py
├── requirements.txt
├── .gitignore
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── app.html
│
├── uploads/
├── instance/
│   └── users.db

▶️ How to Run the Project
1️⃣ Clone the Repository
git clone https://github.com/<your-username>/AI-Powered-Talent-Job-Fit-Recommendation.git
cd AI-Powered-Talent-Job-Fit-Recommendation

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Set Environment Variables

Create a .env file:

GEMINI_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key

4️⃣ Run the Application
python main.py

5️⃣ Open in Browser
http://127.0.0.1:5000

⚠️ Limitations

AI accuracy depends on resume quality

Internet connection required for AI API

Text-based analysis only

🔮 Future Enhancements

Admin / recruiter dashboard

Feedback-based learning

Hybrid AI models (LLM + ML)

Cloud deployment

Role-based access control

🎓 Academic Use

This project is suitable for:

Final Year / Capstone Projects

AI & NLP Demonstrations

Recruitment Automation Systems

🏆 Conclusion

The project demonstrates how Large Language Models and explainable AI can be effectively applied to automate recruitment processes. It provides a scalable, transparent, and efficient solution for resume–job matching.

👨‍💻 Author

Varshith Reddy Nimma

📜 License


This project is for educational purposes only.

