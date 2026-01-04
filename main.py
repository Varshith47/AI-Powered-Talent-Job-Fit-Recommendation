from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from markupsafe import Markup
import os
import PyPDF2
import docx2txt
import google.genai as genai
import google.generativeai as genai
from dotenv import load_dotenv
import re
import json

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'  # Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GeminiApi')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"✓ Gemini API configured successfully")
else:
    print("⚠ Warning: GeminiApi not found in .env file")

# [Keep all your existing functions: extract_text_pdf, extract_text_docs, etc.]
def extract_text_pdf(file_path):
    """
    Robust PDF text extraction:
    - Primary: PyPDF2 per-page extract_text()
    - On page-level failures (e.g., PyPDF2 cmap parsing IndexError), try PyMuPDF (fitz) for that page
    - If PyMuPDF not available or full-file errors occur, gracefully continue and return whatever text could be extracted
    """
    text = ""
    # Attempt with PyPDF2 per page, but handle page-level errors
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ""
                except Exception as e:
                    print(f"⚠ PyPDF2 page {i} extract_text error: {e}")
                    page_text = ""
                    # Try PyMuPDF (fitz) for just this page if available
                    try:
                        import fitz
                        doc = fitz.open(file_path)
                        page_text = doc.load_page(i).get_text("text") or ""
                        doc.close()
                        print(f"✓ PyMuPDF fallback succeeded for page {i}")
                    except Exception as e2:
                        print(f"⚠ PyMuPDF fallback failed for page {i}: {e2}")
                text += page_text + "\n"
        return text
    except Exception as e:
        # If PyPDF2 failed early, try PyMuPDF for whole document
        print(f"⚠ PyPDF2 failed to read PDF: {e}. Trying PyMuPDF for full-document extraction.")
        try:
            import fitz
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text("text") + "\n"
            doc.close()
            return text
        except Exception as e2:
            print(f"❌ PyMuPDF fallback failed: {e2}. Returning partial text (if any).")
            return text

def extract_text_docs(file_path):
    return docx2txt.process(file_path)

def extract_text_txt(file_path):
    with open(file_path,'r',encoding='utf-8') as file:
        return file.read()

def extract_text(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_docs(file_path)
    elif file_path.endswith('.txt'):
        return extract_text_txt(file_path)
    else:
        return ""

def format_markdown_to_html(text):
    """Convert Markdown formatting to HTML for better display"""
    if not text:
        return ""
    
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'^### (.+?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+)\. (.+?)$', r'<li>\2</li>', text, flags=re.MULTILINE)
    text = re.sub(r'((?:<li>.+?</li>\n?)+)', r'<ol>\1</ol>', text, flags=re.DOTALL)
    text = re.sub(r'^[-•] (.+?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'((?:<li>.+?</li>\n?)+)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    text = text.replace('\n', '<br>')
    
    return text

def get_gemini_suggestions(job_description, resumes_dict):
    """Get AI ranking and suggestions from Gemini for all candidates"""
    if not GEMINI_API_KEY:
        print("⚠ Gemini API key not configured")
        return None, None, None
    
    try:
        print("📊 Requesting Gemini AI ranking and analysis...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        ranking_prompt = f"""You are an expert HR recruiter and talent advisor. Analyze ALL candidates and rank them by fit for this role.

**IMPORTANT:** Return a JSON response with the following structure ONLY, no other text:
{{
    "rankings": [
        {{
            "filename": "filename.pdf",
            "rank": 1,
            "match_percentage": 92,
            "key_reason": "Brief reason for this ranking"
        }},
        {{
            "filename": "filename2.pdf",
            "rank": 2,
            "match_percentage": 78,
            "key_reason": "Brief reason"
        }}
    ]
}}

Criteria for ranking:
- Technical skill match (40%)
- Experience level match (30%)
- Cultural fit (15%)
- Education/Certifications (15%)

**Job Description:**
{job_description}

**All Candidates (evaluate ALL of them):**"""
        
        for filename, resume_text in resumes_dict.items():
            ranking_prompt += f"\n\nCandidate: {filename}\n{resume_text[:800]}"
        
        ranking_prompt += "\n\nReturn ONLY valid JSON with rankings of ALL candidates."
        
        response = model.generate_content(ranking_prompt)
        ranking_text = response.text.strip()
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', ranking_text)
            if json_match:
                rankings = json.loads(json_match.group())
                print("✓ AI ranking generated successfully")
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            return None, None, None
        
        sorted_rankings = sorted(rankings.get('rankings', []), key=lambda x: x.get('rank', 999))
        top_3 = sorted_rankings[:3]
        
        top_filenames = [r.get('filename') for r in top_3]
        match_scores = [r.get('match_percentage', 0) / 100.0 for r in top_3]
        match_reasons = [r.get('key_reason', 'N/A') for r in top_3]
        
        analysis_prompt = f"""You are an expert HR recruiter and talent advisor. Based on the job description and the top 3 selected candidates, 
provide comprehensive, professional, and actionable insights.

Format your response with clear sections using markdown. Use **bold** for emphasis.

Structure your response as follows:

## Analysis Overview
Provide a brief executive summary of the top 3 candidates.

## Candidate 1: {top_filenames[0] if len(top_filenames) > 0 else 'Candidate 1'}
**AI Match Score:** {int(match_scores[0] * 100) if len(match_scores) > 0 else 0}%
**Why This Match:** {match_reasons[0] if len(match_reasons) > 0 else 'N/A'}

**Key Strengths:**
- [Strength 1]
- [Strength 2]
- [Strength 3]

**Skill Gaps:**
- [Gap 1]
- [Gap 2]

**Recommended Interview Questions:**
- [Question 1]
- [Question 2]
- [Question 3]

[Repeat for Candidate 2 and 3]

**Job Description:**
{job_description}
return render_template(
    "app.html",
    match_score=87,
    explanation="Strong match in Python, Machine Learning, and NLP. Lacks cloud deployment experience.",
    matched_skills=["Python", "Machine Learning", "NLP", "SQL"],
    missing_skills=["Docker", "AWS"]
)

**Top Candidate Resumes:**"""
        
        for i, filename in enumerate(top_filenames):
            if filename in resumes_dict:
                analysis_prompt += f"\n\nCandidate {i+1}: {filename}\n{resumes_dict[filename][:1200]}"
        
        response = model.generate_content(analysis_prompt)
        detailed_analysis = response.text
        formatted_analysis = format_markdown_to_html(detailed_analysis)
        
        print("✓ Detailed AI analysis generated successfully")
        return top_filenames, match_scores, formatted_analysis
        
    except Exception as e:
        error_msg = f"Error in AI ranking: {str(e)}"
        print(f"❌ {error_msg}")
        return None, None, f"<div style='color: #dc2626;'><strong>AI Analysis Error:</strong> {str(e)}</div>"

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('matchresume'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('matchresume'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'danger')
            return render_template('register.html')
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered!', 'danger')
            return render_template('register.html')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('matchresume'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('matchresume'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def matchresume():
    return render_template("app.html", username=current_user.username)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if request.method == 'POST':
        jd = request.form.get('resumeText')
        resume_files = request.files.getlist('resumeFile')

        if not resume_files or not jd:
            return render_template('app.html', message="Please upload at least one resume and enter a job description", username=current_user.username)
        
        import uuid
        import mimetypes
        from werkzeug.utils import secure_filename

        # Ensure upload folder exists and is writable
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        resume_texts = {}
        for resume_file in resume_files:
            original_filename = resume_file.filename or ''
            safe_name = secure_filename(original_filename)

            # If filename is empty after sanitization, generate a unique name with guessed extension
            if not safe_name:
                ext = ''
                if resume_file.mimetype:
                    guessed = mimetypes.guess_extension(resume_file.mimetype.split(';')[0])
                    ext = guessed or ''
                safe_name = f"{uuid.uuid4().hex}{ext}"

            dest_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)

            try:
                resume_file.save(dest_path)
            except PermissionError as e:
                print(f"❌ PermissionError saving file {dest_path}: {e}")
                return render_template('app.html', message=f"Permission denied when saving file '{safe_name}'. Check upload folder permissions.", username=current_user.username)
            except Exception as e:
                print(f"❌ Error saving file {dest_path}: {e}")
                return render_template('app.html', message=f"Error saving file '{safe_name}': {e}", username=current_user.username)

            text = extract_text(dest_path)
            resume_texts[safe_name] = text
        
        top_r, similarity_scores, suggestions = get_gemini_suggestions(jd, resume_texts)
        
        if top_r is None:
            return render_template('app.html', message="Error in AI analysis. Please try again.", username=current_user.username)
        
        similarity_scores = [round(score * 100, 1) for score in similarity_scores]
        
        print(f"Top matches: {top_r}")
        print(f"AI Match Scores: {similarity_scores}%")
        
        return render_template('app.html', message="Top matching resumes (AI-Ranked):", 
                             top_r=top_r, similarity_scores=similarity_scores, 
                             suggestions=Markup(suggestions), username=current_user.username)

    return render_template('app.html', username=current_user.username)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)