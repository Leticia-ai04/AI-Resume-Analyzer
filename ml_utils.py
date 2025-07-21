import docx2txt
import re
import os
from textstat import flesch_reading_ease
from fpdf import FPDF
import uuid

# Simple grammar check function (basic heuristic)
def grammar_check(text):
    issues = []
    sentences = text.split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if not sentence[0].isupper():
            issues.append(f"Sentence doesn't start with capital: {sentence}")
        if sentence[-1] not in ['.', '!', '?']:
            issues.append(f"Sentence missing proper punctuation: {sentence}")
    return issues

# Extract text from uploaded file (supports .txt, .pdf, .docx)
def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    elif ext == '.docx':
        text = docx2txt.process(file_path)
    elif ext == '.pdf':
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("Please install pdfplumber for PDF text extraction: pip install pdfplumber")
        with pdfplumber.open(file_path) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
            text = '\n'.join(pages)
    else:
        raise ValueError("Unsupported file type.")
    return text

# Analyze resume text and return dictionary of results
def analyze_resume(text, job_description=None):
    # Word count
    word_count = len(text.split())

    # Readability score
    readability = round(flesch_reading_ease(text), 2)

    # Grammar issues (list)
    grammar_issues = grammar_check(text)
    grammar_issues_count = len(grammar_issues)

    # Detect skills (example list - extend as needed)
    skills_db = ['python', 'java', 'sql', 'machine learning', 'docker', 'aws', 'git', 'linux',
                 'c++', 'javascript', 'tensorflow', 'html', 'css', 'react', 'nodejs', 'flask', 'django']
    text_lower = text.lower()
    detected_skills = [skill for skill in skills_db if skill in text_lower]

    # Experience summary (simple heuristic)
    experience = "Experience section not found."
    match_exp = re.search(r'(experience|work history|professional experience)(.*?)(education|skills|$)', text_lower, re.DOTALL)
    if match_exp:
        experience = match_exp.group(2).strip().capitalize()

    # Education summary (simple heuristic)
    education = "Education section not found."
    match_edu = re.search(r'(education)(.*?)(experience|skills|$)', text_lower, re.DOTALL)
    if match_edu:
        education = match_edu.group(2).strip().capitalize()

    # Keyword match score (if job description provided)
    keyword_match_score = 0.0
    matched_keywords = []
    if job_description:
        jd_words = set(re.findall(r'\w+', job_description.lower()))
        resume_words = set(re.findall(r'\w+', text_lower))
        matched = jd_words.intersection(resume_words)
        matched_keywords = list(matched)
        if jd_words:
            keyword_match_score = round(len(matched) / len(jd_words) * 100, 2)

    # Predicted role (dummy example)
    predicted_role = "Data Scientist" if 'machine learning' in text_lower or 'data' in text_lower else "General Professional"

    # Resume scoring (simple heuristic)
    score = 80
    if readability < 50:
        score -= 10
    if grammar_issues_count > 5:
        score -= 10
    if len(detected_skills) < 3:
        score -= 10
    if keyword_match_score < 30:
        score -= 10
    resume_score = max(0, score)

    # ATS Compatibility (dummy logic)
    ats_compatible = True if len(detected_skills) > 0 else False

    # Career recommendation (dummy text)
    career_recommendation = f"Consider applying for more {predicted_role} positions. Enhance skills in " \
                            f"{', '.join(detected_skills[:3])}."

    # Interview questions (dummy examples)
    interview_questions = [
        "Explain supervised vs unsupervised learning.",
        "Describe a machine learning project you worked on.",
        "How do you handle missing data?"
    ]

    return {
        "word_count": word_count,
        "readability": readability,
        "grammar_issues_count": grammar_issues_count,
        "grammar_issues": grammar_issues,
        "detected_skills": detected_skills,
        "experience_summary": experience,
        "education_summary": education,
        "keyword_match_score": keyword_match_score,
        "matched_keywords": matched_keywords,
        "predicted_role": predicted_role,
        "resume_score": resume_score,
        "ats_compatible": ats_compatible,
        "career_recommendation": career_recommendation,
        "interview_questions": interview_questions
    }

# Generate PDF report of the analysis results
def generate_pdf_report(analysis, save_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(212, 175, 55)  # Gold color

    pdf.cell(0, 10, "Resume Analysis Report", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(255, 255, 255)  # White text

    pdf.cell(0, 10, f"Word Count: {analysis['word_count']}", ln=True)
    pdf.cell(0, 10, f"Readability Score: {analysis['readability']}", ln=True)
    pdf.cell(0, 10, f"Grammar Issues: {analysis['grammar_issues_count']}", ln=True)

    pdf.cell(0, 10, "Detected Skills:", ln=True)
    pdf.multi_cell(0, 10, ", ".join(analysis['detected_skills']) if analysis['detected_skills'] else "None")

    pdf.cell(0, 10, "Experience Summary:", ln=True)
    pdf.multi_cell(0, 10, analysis['experience_summary'])

    pdf.cell(0, 10, "Education Highlights:", ln=True)
    pdf.multi_cell(0, 10, analysis['education_summary'])

    pdf.cell(0, 10, f"Keyword Match Score: {analysis['keyword_match_score']}%", ln=True)
    pdf.cell(0, 10, f"Matched Keywords: {', '.join(analysis['matched_keywords']) if analysis['matched_keywords'] else 'None'}", ln=True)

    pdf.cell(0, 10, f"Predicted Role: {analysis['predicted_role']}", ln=True)
    pdf.cell(0, 10, f"Resume Score: {analysis['resume_score']}/100", ln=True)
    pdf.cell(0, 10, f"ATS Compatibility: {'✅ Compatible' if analysis['ats_compatible'] else '❌ Not Compatible'}", ln=True)

    pdf.cell(0, 10, "Career Recommendation:", ln=True)
    pdf.multi_cell(0, 10, analysis['career_recommendation'])

    pdf.cell(0, 10, "Interview Questions to Prepare:", ln=True)
    for q in analysis['interview_questions']:
        pdf.cell(0, 10, f"- {q}", ln=True)

    pdf.output(save_path)

# Initialize database or other setup if needed
def init_db():
    # You can add your database initialization code here if needed
    pass
