"""
seed_nigerian_sources.py
Populates Nigerian job sources and 7 category-specific cover letter templates
based on Sharafdeen Quadri's actual CV and experience.

Usage:
    python seed_nigerian_sources.py
"""
from app.utils.auth import hash_password
from app.services.scraper import NIGERIAN_SOURCES
from app.models.user import User
from app.models.email import EmailTemplate
from app.models.job import JobSource
from app.database import SessionLocal
from dotenv import load_dotenv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()


db = SessionLocal()

# ── Cover Letter Templates ─────────────────────────────────────────────────
TEMPLATES = [
    # ── 1. Backend Developer ──────────────────────────────────────────────
    {
        "name": "Backend Developer Cover Letter",
        "category": "backend_developer",
        "subject": "Application for {{job_title}} at {{company}}",
        "variables": ["job_title", "company", "location", "applicant_name", "applicant_email", "applicant_github", "applicant_website"],
        "html_body": """<div style="font-family:Georgia,serif;max-width:680px;margin:auto;color:#1a1a1a;line-height:1.7">
<p>Dear Hiring Manager,</p>

<p>I am writing to express my strong interest in the <strong>{{job_title}}</strong> position at
<strong>{{company}}</strong> ({{location}}).</p>

<p>As a Full-Stack Software Engineer with deep specialisation in Python backend development,
I have delivered production-grade systems for real users. At <strong>N-TECH Info Systems Ltd</strong>,
I led end-to-end software development, from RESTful API design to cloud deployment, while also
mentoring over 70 active learners in FastAPI and Django.</p>

<p>My most relevant backend project is <strong>ExamGenius</strong> — a FastAPI + PostgreSQL platform
serving Nigerian students with JWT authentication, 30+ REST API endpoints, DeepSeek AI integration,
and a 26,500-question CBT engine. I deployed it on <strong>AWS EC2</strong> with Nginx, achieving
sub-second response times through query optimisation and connection pooling.</p>

<p><strong>Backend skills directly applicable to this role:</strong></p>
<ul>
  <li>FastAPI &amp; Django REST Framework — production API design</li>
  <li>PostgreSQL, MySQL, SQLite — schema design, ORM (SQLAlchemy, Django ORM), complex queries</li>
  <li>JWT, OAuth2, role-based access control</li>
  <li>Docker, Nginx, AWS EC2, Render — deployment &amp; infrastructure</li>
  <li>Git, GitLab, Agile methodology (Bincom Dev Center experience)</li>
</ul>

<p>I also built <strong>Autojobserve</strong> (a Selenium-based job scraping platform with OAuth2)
and <strong>SmartCV</strong> (a FastAPI + React AI resume builder with Stripe integration),
demonstrating my ability to integrate complex third-party services into robust APIs.</p>

<p>My CV is attached. I would welcome the opportunity to discuss how I can contribute to
your engineering team at {{company}}.</p>

<p>Best regards,<br/>
<strong>{{applicant_name}}</strong><br/>
{{applicant_email}}<br/>
{{applicant_github}} | {{applicant_website}}</p>
<hr style="border:none;border-top:1px solid #ddd;margin-top:24px"/>
<small style="color:#888"><em>To unsubscribe, reply with "Unsubscribe" in the subject line.</em></small>
</div>""",
        "text_body": """Dear Hiring Manager,

I am writing to express my strong interest in the {{job_title}} position at {{company}} ({{location}}).

As a Full-Stack Software Engineer specialising in Python backend development, I have delivered production-grade systems at N-TECH Info Systems Ltd, including ExamGenius — a FastAPI + PostgreSQL platform with JWT auth, 30+ REST endpoints, AI integration, and AWS EC2 deployment with sub-second response times.

Key backend skills: FastAPI, Django REST Framework, PostgreSQL, JWT/OAuth2, Docker, Nginx, AWS EC2.

I also built Autojobserve (Selenium + OAuth2 job scraping platform) and SmartCV (FastAPI + React AI resume builder with Stripe).

My CV is attached. I'd welcome a conversation about contributing to {{company}}.

Best regards,
{{applicant_name}}
{{applicant_email}} | {{applicant_github}} | {{applicant_website}}

---
To unsubscribe, reply with "Unsubscribe" in the subject line.""",
    },

    # ── 2. Full-Stack Developer ───────────────────────────────────────────
    {
        "name": "Full-Stack Developer Cover Letter",
        "category": "full_stack_developer",
        "subject": "Application for {{job_title}} at {{company}}",
        "variables": ["job_title", "company", "location", "applicant_name", "applicant_email", "applicant_github", "applicant_website"],
        "html_body": """<div style="font-family:Georgia,serif;max-width:680px;margin:auto;color:#1a1a1a;line-height:1.7">
<p>Dear Hiring Manager,</p>

<p>I am excited to apply for the <strong>{{job_title}}</strong> role at
<strong>{{company}}</strong> ({{location}}).</p>

<p>I am a <strong>Dynamic Full-Stack Software Engineer</strong> with proven expertise in Python,
JavaScript, and modern frameworks for building robust, scalable applications. I combine strong
backend API design with polished React frontends — a combination I have applied across multiple
live products.</p>

<p>Highlights of my full-stack experience:</p>
<ul>
  <li><strong>ExamGenius</strong> — FastAPI backend + React frontend; AI-driven JAMB exam prep
      platform deployed on AWS EC2 with 30+ endpoints and real-time analytics</li>
  <li><strong>SmartCV</strong> — FastAPI + React AI resume builder with live preview, dark theme,
      Stripe payments, Docker deployment, and PDF generation</li>
  <li><strong>Preptutor</strong> — Odoo-based LMS with custom Python models, XML templates, and
      JavaScript front-end views for course management and automated grading</li>
</ul>

<p><strong>Full-stack skills:</strong></p>
<ul>
  <li><strong>Backend:</strong> Python, FastAPI, Django, Flask, PostgreSQL, SQLAlchemy, JWT</li>
  <li><strong>Frontend:</strong> React.js, JavaScript (ES6+), HTML5, CSS3, Tailwind CSS</li>
  <li><strong>DevOps:</strong> Docker, AWS EC2, Render, Nginx, Git/GitLab</li>
  <li><strong>Integrations:</strong> OpenRouter AI (DeepSeek), Stripe, OAuth2, email services</li>
</ul>

<p>At N-TECH Info Systems Ltd I grew a tech hub from zero to over 70 active learners, teaching
full-stack development end-to-end — which means I write clean, documented, mentorship-ready code.</p>

<p>My CV is attached for your review. I look forward to contributing to {{company}}.</p>

<p>Best regards,<br/>
<strong>{{applicant_name}}</strong><br/>
{{applicant_email}}<br/>
{{applicant_github}} | {{applicant_website}}</p>
<hr style="border:none;border-top:1px solid #ddd;margin-top:24px"/>
<small style="color:#888"><em>To unsubscribe, reply with "Unsubscribe" in the subject line.</em></small>
</div>""",
        "text_body": """Dear Hiring Manager,

I am applying for the {{job_title}} role at {{company}} ({{location}}).

I am a Full-Stack Software Engineer with expertise in Python (FastAPI/Django) + React/JavaScript. Key projects include ExamGenius (FastAPI + React, AWS EC2), SmartCV (AI resume builder with Stripe), and Preptutor (Odoo LMS with custom Python modules).

Skills: FastAPI, Django, React, PostgreSQL, Docker, AWS, Tailwind CSS, JWT, Stripe, OpenRouter AI.

My CV is attached. I'd welcome a discussion about this role.

Best regards,
{{applicant_name}}
{{applicant_email}} | {{applicant_github}} | {{applicant_website}}

---
To unsubscribe, reply with "Unsubscribe" in the subject line.""",
    },

    # ── 3. Software Engineer (General) ────────────────────────────────────
    {
        "name": "Software Engineer Cover Letter",
        "category": "software_engineer",
        "subject": "Application for {{job_title}} at {{company}}",
        "variables": ["job_title", "company", "location", "applicant_name", "applicant_email", "applicant_github", "applicant_website"],
        "html_body": """<div style="font-family:Georgia,serif;max-width:680px;margin:auto;color:#1a1a1a;line-height:1.7">
<p>Dear Hiring Manager,</p>

<p>I am writing to apply for the <strong>{{job_title}}</strong> position at
<strong>{{company}}</strong> ({{location}}).</p>

<p>I am a <strong>Full-Stack Software Engineer</strong> with a Diploma in Software Engineering
(Distinction, AltSchool Africa School of Engineering) and hands-on experience building and deploying production
applications. My work spans API development, AI integration, e-learning platforms, and automation
systems — all delivered to real users in production environments.</p>

<p><strong>Career highlights:</strong></p>
<ul>
  <li>Architected and deployed <strong>ExamGenius</strong> on AWS EC2 — a high-traffic AI exam
      platform serving Nigerian students (FastAPI, PostgreSQL, JWT, DeepSeek AI)</li>
  <li>Built <strong>Preptutor</strong>, an Odoo-based LMS with custom Python business logic,
      automating grading and role-based access control for institutional clients</li>
  <li>Contributed to multiple Python team projects at <strong>Bincom Dev Center</strong>,
      practising GitLab-based Agile development</li>
  <li>Managed a tech hub from inception to 70+ active students at
      <strong>N-TECH Info Systems Ltd</strong>, Osogbo</li>
</ul>

<p><strong>Core engineering skills:</strong> Python · JavaScript · FastAPI · Django · React ·
PostgreSQL · Docker · AWS EC2 · REST APIs · Git · Agile</p>

<p>I take pride in clean architecture, clear documentation, and delivering products that work
reliably in production. My CV is attached.</p>

<p>I would be delighted to discuss how my experience aligns with {{company}}'s engineering goals.</p>

<p>Best regards,<br/>
<strong>{{applicant_name}}</strong><br/>
{{applicant_email}}<br/>
{{applicant_github}} | {{applicant_website}}</p>
<hr style="border:none;border-top:1px solid #ddd;margin-top:24px"/>
<small style="color:#888"><em>To unsubscribe, reply with "Unsubscribe" in the subject line.</em></small>
</div>""",
        "text_body": """Dear Hiring Manager,

I am applying for the {{job_title}} position at {{company}} ({{location}}).

I am a Full-Stack Software Engineer with a Diploma in Software Engineering (Distinction, AltSchool Africa School of Engineering) and production experience across FastAPI, Django, React, PostgreSQL, and AWS EC2. I have shipped ExamGenius (AI exam platform, AWS), Preptutor (Odoo LMS), SmartCV (AI resume builder), and more.

My CV is attached. I look forward to discussing this opportunity.

Best regards,
{{applicant_name}}
{{applicant_email}} | {{applicant_github}} | {{applicant_website}}

---
To unsubscribe, reply with "Unsubscribe" in the subject line.""",
    },

    # ── 4. Tech / ICT Teacher ─────────────────────────────────────────────
    {
        "name": "Tech Teacher Cover Letter",
        "category": "tech_teacher",
        "subject": "Application for {{job_title}} at {{company}}",
        "variables": ["job_title", "company", "location", "applicant_name", "applicant_email", "applicant_github", "applicant_website"],
        "html_body": """<div style="font-family:Georgia,serif;max-width:680px;margin:auto;color:#1a1a1a;line-height:1.7">
<p>Dear Principal / HR Manager,</p>

<p>I am applying for the <strong>{{job_title}}</strong> position at
<strong>{{company}}</strong> ({{location}}).</p>

<p>With over <strong>5 years of combined classroom teaching and technology instruction</strong>
in Nigerian secondary schools and tertiary institutions, I bring both the technical depth of a
professional software engineer and the pedagogical skills of an experienced educator.</p>

<p><strong>Teaching experience directly relevant to this role:</strong></p>
<ul>
  <li><strong>ICT Instructor — Mabest College, Akure (ICTinSchool Project, 2023–2024):</strong>
      Trained secondary school students in AI, full-stack web development, Python, HTML/CSS,
      and JavaScript. Managed Akure branch operations and AI curriculum delivery.</li>
  <li><strong>IT Support &amp; Programming Instructor — Medmina College, Ibadan (2019–2023):</strong>
      Delivered programming and digital skills classes alongside core subject teaching.
      Leveraged a Software Engineering diploma to integrate technology into the curriculum.</li>
  <li><strong>Web Full-Stack Instructor — N-TECH Info Systems Ltd (2024–present):</strong>
      Designed and delivered training programmes in Python, Django, FastAPI, React, and
      PostgreSQL to professional and institutional clients; grew student enrolment to
      70+ active learners across multiple disciplines.</li>
</ul>

<p><strong>Subjects I can teach:</strong> Computer Science · ICT · Programming (Python, JavaScript,
HTML/CSS) · Robotics/AI Fundamentals · Web Development · Database Management</p>

<p>I hold a <strong>Diploma in Software Engineering (Distinction)</strong> from AltSchool Africa School of Engineering
and have real industry experience building production software — meaning every concept I teach
is grounded in practical, real-world application.</p>

<p>My CV is attached. I am available for interview at your earliest convenience and would be
honoured to contribute to the digital education of the next generation at {{company}}.</p>

<p>Yours sincerely,<br/>
<strong>{{applicant_name}}</strong><br/>
{{applicant_email}}<br/>
{{applicant_github}} | {{applicant_website}}</p>
<hr style="border:none;border-top:1px solid #ddd;margin-top:24px"/>
<small style="color:#888"><em>To unsubscribe, reply with "Unsubscribe" in the subject line.</em></small>
</div>""",
        "text_body": """Dear Principal / HR Manager,

I am applying for the {{job_title}} position at {{company}} ({{location}}).

I have 5+ years of combined classroom teaching and technology instruction in Nigerian secondary schools and institutions:
- ICT Instructor, Mabest College, Akure (AI, Python, HTML/CSS, JavaScript — ICTinSchool Project)
- IT Support & Programming Instructor, Medmina College, Ibadan (4 years)
- Full-Stack Web Instructor, N-TECH Info Systems Ltd (70+ active learners)

Subjects: Computer Science, ICT, Python, JavaScript, Web Development, AI Fundamentals.
Qualifications: Diploma in Software Engineering (Distinction), AltSchool Africa School of Engineering.

My CV is attached. I look forward to contributing to {{company}}.

Yours sincerely,
{{applicant_name}}
{{applicant_email}} | {{applicant_github}} | {{applicant_website}}

---
To unsubscribe, reply with "Unsubscribe" in the subject line.""",
    },

    # ── 5. Python Developer ───────────────────────────────────────────────
    {
        "name": "Python Developer Cover Letter",
        "category": "python_developer",
        "subject": "Application for {{job_title}} at {{company}}",
        "variables": ["job_title", "company", "location", "applicant_name", "applicant_email", "applicant_github", "applicant_website"],
        "html_body": """<div style="font-family:Georgia,serif;max-width:680px;margin:auto;color:#1a1a1a;line-height:1.7">
<p>Dear Hiring Manager,</p>

<p>I am writing to apply for the <strong>{{job_title}}</strong> role at
<strong>{{company}}</strong> ({{location}}).</p>

<p>Python is my primary language, and I have used it professionally across web development,
automation, API engineering, data science, and AI integration over the past several years.
Here is a snapshot of what I have built with Python:</p>

<ul>
  <li><strong>ExamGenius:</strong> FastAPI + PostgreSQL backend with DeepSeek AI integration,
      JWT security, 30+ endpoints, deployed on AWS EC2</li>
  <li><strong>Autojobserve:</strong> Automated job scraping with Selenium + FastAPI backend,
      OAuth2 authentication, and automated resume scanning via Pydocx</li>
  <li><strong>Preptutor:</strong> Odoo (Python/XML) LMS with custom models, automated grading,
      and payment integration</li>
  <li><strong>JobRadar:</strong> FastAPI-based job scraper and email outreach automation
      (personal productivity tool)</li>
</ul>

<p><strong>Python ecosystem proficiency:</strong></p>
<ul>
  <li>Web frameworks: FastAPI, Django, Flask</li>
  <li>Data: Pandas, NumPy (Bincom Academy Data Science certification)</li>
  <li>Automation: Selenium, httpx, BeautifulSoup, APScheduler</li>
  <li>ORM: SQLAlchemy, Django ORM, Alembic</li>
  <li>Testing, CI/CD: pytest, GitLab pipelines</li>
</ul>

<p>My CV is attached. I would be happy to walk you through any of these projects and discuss
how my Python expertise can benefit {{company}}.</p>

<p>Best regards,<br/>
<strong>{{applicant_name}}</strong><br/>
{{applicant_email}}<br/>
{{applicant_github}} | {{applicant_website}}</p>
<hr style="border:none;border-top:1px solid #ddd;margin-top:24px"/>
<small style="color:#888"><em>To unsubscribe, reply with "Unsubscribe" in the subject line.</em></small>
</div>""",
        "text_body": """Dear Hiring Manager,

I am applying for the {{job_title}} role at {{company}} ({{location}}).

Python is my primary language. Key projects: ExamGenius (FastAPI + DeepSeek AI, AWS EC2), Autojobserve (Selenium automation + OAuth2), Preptutor (Odoo/Python LMS), JobRadar (scraping + SMTP automation).

Skills: FastAPI, Django, Flask, Selenium, SQLAlchemy, Pandas, pytest, Docker, AWS.
Certification: Bincom Academy Data Science (2023).

CV attached. Happy to discuss further.

Best regards,
{{applicant_name}}
{{applicant_email}} | {{applicant_github}} | {{applicant_website}}

---
To unsubscribe, reply with "Unsubscribe" in the subject line.""",
    },

    # ── 6. Data Analyst ───────────────────────────────────────────────────
    {
        "name": "Data Analyst Cover Letter",
        "category": "data_analyst",
        "subject": "Application for {{job_title}} at {{company}}",
        "variables": ["job_title", "company", "location", "applicant_name", "applicant_email", "applicant_github", "applicant_website"],
        "html_body": """<div style="font-family:Georgia,serif;max-width:680px;margin:auto;color:#1a1a1a;line-height:1.7">
<p>Dear Hiring Manager,</p>

<p>I am writing to apply for the <strong>{{job_title}}</strong> role at
<strong>{{company}}</strong> ({{location}}).</p>

<p>My interest in data-driven decision-making is backed by practical experience:
I hold a <strong>Bincom Academy Data Science Certification (2023)</strong> and have applied
data analysis skills professionally at <strong>Bincom Dev Center</strong> (Lagos), where I used
Python for Data Science tasks and developed competencies in data analysis and visualisation as
part of a cross-functional engineering team.</p>

<p><strong>Relevant data skills:</strong></p>
<ul>
  <li>Python (Pandas, NumPy) for data manipulation and analysis</li>
  <li>PostgreSQL and SQL — complex queries, aggregations, window functions</li>
  <li>Data visualisation — charts, dashboards, performance analytics reporting</li>
  <li>Built adaptive <strong>performance analytics</strong> in ExamGenius: tracking accuracy,
      streaks, subject strengths/weaknesses, and recommended topics using batched SQL queries</li>
  <li>Experience building admin dashboards and analytics-facing APIs in FastAPI</li>
</ul>

<p>My software engineering background means I can go beyond analysis — I can build the
data pipelines, APIs, and dashboards needed to put insights into action.</p>

<p>My CV is attached. I look forward to the opportunity to discuss how I can add value to
the data team at {{company}}.</p>

<p>Best regards,<br/>
<strong>{{applicant_name}}</strong><br/>
{{applicant_email}}<br/>
{{applicant_github}} | {{applicant_website}}</p>
<hr style="border:none;border-top:1px solid #ddd;margin-top:24px"/>
<small style="color:#888"><em>To unsubscribe, reply with "Unsubscribe" in the subject line.</em></small>
</div>""",
        "text_body": """Dear Hiring Manager,

I am applying for the {{job_title}} role at {{company}} ({{location}}).

I hold a Bincom Academy Data Science Certification (2023) and used Python for data analysis at Bincom Dev Center, Lagos. In ExamGenius, I built performance analytics tracking student accuracy, strengths, and weaknesses with batched SQL queries.

Skills: Python (Pandas, NumPy), PostgreSQL (complex queries, aggregations), data visualisation, FastAPI analytics dashboards.

CV attached. I look forward to discussing this opportunity.

Best regards,
{{applicant_name}}
{{applicant_email}} | {{applicant_github}} | {{applicant_website}}

---
To unsubscribe, reply with "Unsubscribe" in the subject line.""",
    },

    # ── 7. Odoo Developer ────────────────────────────────────────────────
    {
        "name": "Odoo Developer Cover Letter",
        "category": "odoo_developer",
        "subject": "Application for {{job_title}} at {{company}}",
        "variables": ["job_title", "company", "location", "applicant_name", "applicant_email", "applicant_github", "applicant_website"],
        "html_body": """<div style="font-family:Georgia,serif;max-width:680px;margin:auto;color:#1a1a1a;line-height:1.7">
<p>Dear Hiring Manager,</p>

<p>I am writing to express my interest in the <strong>{{job_title}}</strong> position at
<strong>{{company}}</strong> ({{location}}).</p>

<p>I have hands-on Odoo development experience through <strong>Preptutor</strong>, an
Odoo-based e-learning and assessment platform I built for N-TECH Info Systems Ltd.
This project gave me deep exposure to the full Odoo development stack:</p>

<ul>
  <li>Customised and extended <strong>Odoo modules</strong> for course creation,
      student enrolment, and instructor dashboards</li>
  <li>Built <strong>custom Python models</strong> and business logic for automated grading,
      performance tracking, and user management</li>
  <li>Designed interactive front-end views using <strong>Odoo XML templates and JavaScript</strong>
      for an enhanced user experience</li>
  <li>Implemented <strong>role-based access control</strong> and integrated
      <strong>email notifications</strong> for course updates and reminders</li>
  <li>Integrated <strong>payment methods</strong> within the Odoo framework</li>
</ul>

<p>Beyond Odoo, I bring strong Python and PostgreSQL fundamentals — essential for complex
module customisation and ORM work.</p>

<p>My CV and a live demo of Preptutor are available for your review. I would welcome a
technical discussion about how I can contribute to {{company}}'s Odoo projects.</p>

<p>Best regards,<br/>
<strong>{{applicant_name}}</strong><br/>
{{applicant_email}}<br/>
{{applicant_github}} | {{applicant_website}}</p>
<hr style="border:none;border-top:1px solid #ddd;margin-top:24px"/>
<small style="color:#888"><em>To unsubscribe, reply with "Unsubscribe" in the subject line.</em></small>
</div>""",
        "text_body": """Dear Hiring Manager,

I am applying for the {{job_title}} role at {{company}} ({{location}}).

I have Odoo development experience from building Preptutor (N-TECH Info Systems): custom Python models, Odoo XML views, JavaScript frontend, role-based access control, automated grading, and payment integration. Full Python/PostgreSQL background for complex ORM customisation.

CV attached. I welcome a technical discussion.

Best regards,
{{applicant_name}}
{{applicant_email}} | {{applicant_github}} | {{applicant_website}}

---
To unsubscribe, reply with "Unsubscribe" in the subject line.""",
    },

    # ── 8. General / Fallback ────────────────────────────────────────────
    {
        "name": "General Tech Cover Letter",
        "category": "general",
        "subject": "Application for {{job_title}} at {{company}}",
        "variables": ["job_title", "company", "location", "applicant_name", "applicant_email", "applicant_github", "applicant_website"],
        "html_body": """<div style="font-family:Georgia,serif;max-width:680px;margin:auto;color:#1a1a1a;line-height:1.7">
<p>Dear Hiring Manager,</p>

<p>I am writing to express my keen interest in the <strong>{{job_title}}</strong> position
at <strong>{{company}}</strong> ({{location}}).</p>

<p>I am <strong>Sharafdeen Quadri O.</strong>, a Dynamic Full-Stack Software Engineer and
technology educator based in Nigeria, with expertise in Python, JavaScript, and modern
frameworks for building scalable, production-ready applications.</p>

<p><strong>Why I am a strong candidate:</strong></p>
<ul>
  <li>Built and deployed multiple live products: ExamGenius (AI exam platform, AWS EC2),
      SmartCV (AI resume builder), Preptutor (Odoo LMS), Autojobserve (job scraping automation)</li>
  <li>Full-stack proficiency: FastAPI · Django · React · PostgreSQL · Docker · AWS</li>
  <li>5+ years of tech instruction experience in Nigerian secondary schools and institutions</li>
  <li>AltSchool Africa School of Engineering Diploma in Software Engineering (Distinction) + Bincom Data Science Cert</li>
  <li>Managed N-TECH Info Systems tech hub, growing active learners to 70+</li>
</ul>

<p>I am passionate about clean architecture, automation, and data-driven development. I am
confident I can make a meaningful contribution at {{company}}.</p>

<p>My CV is attached for your review. I look forward to hearing from you.</p>

<p>Best regards,<br/>
<strong>{{applicant_name}}</strong><br/>
{{applicant_email}}<br/>
{{applicant_github}} | {{applicant_website}}</p>
<hr style="border:none;border-top:1px solid #ddd;margin-top:24px"/>
<small style="color:#888"><em>To unsubscribe, reply with "Unsubscribe" in the subject line.</em></small>
</div>""",
        "text_body": """Dear Hiring Manager,

I am applying for the {{job_title}} position at {{company}} ({{location}}).

I am Sharafdeen Quadri O., a Full-Stack Software Engineer and tech educator based in Nigeria. I have built and deployed ExamGenius (AI platform, AWS EC2), SmartCV (AI resume builder), Preptutor (Odoo LMS), and Autojobserve (job scraping automation). 5+ years of tech teaching experience in Nigerian schools.

Skills: Python, FastAPI, Django, React, PostgreSQL, Docker, AWS EC2.
Qualifications: AltSchool Africa School of Engineering Diploma in Software Engineering (Distinction).

CV attached. Looking forward to hearing from you.

Best regards,
{{applicant_name}}
{{applicant_email}} | {{applicant_github}} | {{applicant_website}}

---
To unsubscribe, reply with "Unsubscribe" in the subject line.""",
    },
]


# ─── Seed ─────────────────────────────────────────────────────────────────────
try:
    # ── Job Sources ──────────────────────────────────────────────────────────
    print("\n── Job Sources ──────────────────────────────────────────────────────")
    for src in NIGERIAN_SOURCES:
        existing = db.query(JobSource).filter(
            JobSource.url == src["url"]).first()
        if not existing:
            db.add(JobSource(
                name=src["name"],
                url=src["url"],
                scraper_type=src.get("scraper_type", "bs4"),
                keywords=src.get("keywords", []),
                selectors=src.get("selectors"),
                is_active=True,
            ))
            print(
                f"  + Added source: {src['name']} [{src.get('scraper_type', 'bs4')}]")
        else:
            # Update scraper_type and selectors to the latest values
            changed = False
            if existing.scraper_type != src.get("scraper_type", "bs4"):
                existing.scraper_type = src.get("scraper_type", "bs4")
                changed = True
            if existing.selectors != src.get("selectors"):
                existing.selectors = src.get("selectors")
                changed = True
            if changed:
                print(
                    f"  ↑ Updated: {src['name']} → scraper_type={existing.scraper_type}")
            else:
                print(f"  ~ Exists:  {src['name']} [{existing.scraper_type}]")
    # Remove dead sources no longer in NIGERIAN_SOURCES
    live_urls = {s["url"] for s in NIGERIAN_SOURCES}
    dead_sources = db.query(JobSource).filter(
        ~JobSource.url.in_(live_urls)).all()
    for ds in dead_sources:
        ds.is_active = False
        print(f"  ✗ Deactivated dead source: {ds.name}")

    # ── Cover Letter Templates ──────────────────────────────────────────────
    print("\n── Cover Letter Templates ───────────────────────────────────────────")
    for t in TEMPLATES:
        existing = db.query(EmailTemplate).filter(
            EmailTemplate.category == t["category"]).first()
        if not existing:
            db.add(EmailTemplate(
                name=t["name"],
                category=t["category"],
                subject=t["subject"],
                html_body=t["html_body"],
                text_body=t["text_body"],
                variables=t["variables"],
                is_active=True,
                version=1,
            ))
            print(f"  + Added [{t['category']}] → {t['name']}")
        else:
            changed = False
            for field in ["name", "subject", "html_body", "text_body", "variables"]:
                if getattr(existing, field) != t[field]:
                    setattr(existing, field, t[field])
                    changed = True
            if not existing.is_active:
                existing.is_active = True
                changed = True
            if changed:
                existing.version = (existing.version or 1) + 1
                print(f"  ↑ Updated [{t['category']}] → {t['name']}")
            else:
                print(f"  ~ Exists  [{t['category']}] → {t['name']}")

    # ── Default Admin User ──────────────────────────────────────────────────
    print("\n── Admin User ───────────────────────────────────────────────────────")
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(
            username="admin",
            hashed_password=hash_password("jobradar2026"),
            is_active=True,
        ))
        print("  + Admin created: admin / jobradar2026")
    else:
        print("  ~ Admin already exists")

    db.commit()
    print("\n✓ Seed complete. Categories seeded:")
    for t in TEMPLATES:
        print(f"    {t['category']:<25} → {t['name']}")
    print("\n  Login at http://localhost:8000/ui  →  admin / jobradar2026")

finally:
    db.close()
