"""
Management command to seed Sharafdeen Quadri's resume into the database.
Run: python manage.py seed_sharafdeen
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from resumes.models import Resume


RESUME_DATA = {
    "personal": {
        "full_name": "Sharafdeen Quadri O.",
        "job_title": "Full-Stack Software Engineer",
        "email": "olalekanquadri58@gmail.com",
        "phone": "",
        "location": "Nigeria",
        "website": "Quaddev.com",
        "linkedin": "",
        "github": "github.com/Olalekan2040-slack",
        "summary": (
            "Dynamic Full-Stack Software Engineer with proven expertise in Python, JavaScript, "
            "and modern frameworks for building robust, scalable applications. Passionate about "
            "clean architecture, automation, and data-driven development. Experienced in designing "
            "efficient APIs, managing databases, and deploying production-ready solutions. Combines "
            "strong technical acumen with Agile collaboration and problem solving skills to deliver "
            "impactful digital products that drive business success."
        ),
    },
    "experience": [
        {
            "id": "exp1",
            "company": "N-TECH Info Systems",
            "position": "Web Full-stack Instructor / Tech-hub Manager",
            "location": "Osogbo, Osun State",
            "start_date": "2024",
            "end_date": "Present",
            "current": True,
            "bullets": [
                "Designed, scheduled, and delivered custom training programs for professional and institutional clients.",
                "Supervised students on end-to-end software projects, from coding to deployment, fostering a project-based learning environment.",
                "Managed the tech hub from inception, growing student registration to over 70 active learners across multiple tech disciplines.",
                "Delivered hands-on instruction in Full Stack Web Development using HTML, CSS, JavaScript, Python, Flask, Django, and FastAPI.",
                "Taught core and advanced Python programming, covering object-oriented design, API development, and real-world problem-solving.",
                "Guided students in building and deploying RESTful APIs using FastAPI and Django REST Framework (DRF).",
                "Provided comprehensive training in database design and management with PostgreSQL, MySQL, and SQLite, including ORM implementation in Django.",
                "Organized two cohorts of a Virtual Assistant training class with 44 registered participants in total.",
                "Oversaw scholarships, digital skill programs, and partnership strategies with academic and corporate bodies.",
            ],
        },
        {
            "id": "exp2",
            "company": "ICTinSchool Project",
            "position": "ICT Instructor at Mabest College, Akure",
            "location": "Akure, Ondo State",
            "start_date": "2023",
            "end_date": "Oct 2024",
            "current": False,
            "bullets": [
                "Managed Akure branch operations, overseeing school faculty and AI curriculum delivery.",
                "Trained secondary school students in AI and full-stack development using Python, HTML/CSS, and JavaScript.",
                "Conducted regular training for teaching staff on school management software for digital reporting and scheduling.",
                "Supervised trainers and provided coaching for continuous improvement.",
            ],
        },
        {
            "id": "exp3",
            "company": "Bincom Dev Center",
            "position": "Junior Software Developer (Remote)",
            "location": "Yaba, Lagos State",
            "start_date": "Nov 2023",
            "end_date": "Jan 2025",
            "current": False,
            "bullets": [
                "Member of the Python Team, contributing to numerous projects.",
                "Developed APIs for web projects.",
                "Collaborated with a project manager and front-end developer to deliver project milestones.",
                "Utilized Python for Data Science tasks and developed skills in data analysis and visualization.",
                "Worked collaboratively with teammates using GitLab and Dev server, implementing version control and agile development methodologies.",
            ],
        },
        {
            "id": "exp4",
            "company": "Medmina College",
            "position": "Tutor / IT Support",
            "location": "Ibadan, Oyo State",
            "start_date": "Oct 2019",
            "end_date": "Mar 2023",
            "current": False,
            "bullets": [
                "Taught Literature in English and supported English Language instruction, improving comprehension, critical analysis, and expressive writing skills.",
                "Guided students through literary texts, themes, figures of speech, and examination-focused interpretations.",
                "Actively contributed as a core member of the ICT team, providing technical support across classrooms and staff offices.",
                "Assisted in the delivery of programming and digital skills classes, strengthening students' digital literacy.",
                "Leveraged a Diploma in Software Engineering to integrate technology into teaching and support curriculum enhancement.",
            ],
        },
        {
            "id": "exp5",
            "company": "Dimeji Premier College",
            "position": "Tutor / IT Support",
            "location": "Akure, Ondo State",
            "start_date": "2017",
            "end_date": "Dec 2017",
            "current": False,
            "bullets": [
                "Taught Literature in English, English Language, and Government with emphasis on literary appreciation, grammar, essay writing, and oral communication.",
                "Helped students develop reading confidence, vocabulary, and critical thinking skills through guided discussions.",
                "Prepared students for internal and external examinations using structured lesson plans.",
                "Maintained a supportive classroom environment that encouraged participation and academic discipline.",
            ],
        },
    ],
    "education": [
        {
            "id": "edu1",
            "institution": "AltSchool Africa",
            "degree": "Diploma, Software Engineering",
            "field": "Software Engineering",
            "location": "Lagos, Nigeria",
            "start_date": "",
            "end_date": "September 2023",
            "grade": "Distinction",
            "bullets": [],
        },
        {
            "id": "edu2",
            "institution": "Fountain University",
            "degree": "BSc, Political Science and Public Administration",
            "field": "Political Science and Public Administration",
            "location": "Osogbo, Nigeria",
            "start_date": "",
            "end_date": "September 2016",
            "grade": "Second Class Division",
            "bullets": [],
        },
        {
            "id": "edu3",
            "institution": "Khadob Model College",
            "degree": "O'Level",
            "field": "",
            "location": "Akure, Nigeria",
            "start_date": "",
            "end_date": "2012",
            "grade": "",
            "bullets": [],
        },
    ],
    "skills": [
        {"id": "sk1", "name": "Python", "level": "Expert"},
        {"id": "sk2", "name": "JavaScript", "level": "Advanced"},
        {"id": "sk3", "name": "HTML & CSS", "level": "Expert"},
        {"id": "sk4", "name": "SQL", "level": "Advanced"},
        {"id": "sk5", "name": "Django", "level": "Expert"},
        {"id": "sk6", "name": "FastAPI", "level": "Advanced"},
        {"id": "sk7", "name": "Flask", "level": "Advanced"},
        {"id": "sk8", "name": "React.js", "level": "Intermediate"},
        {"id": "sk9", "name": "PostgreSQL", "level": "Advanced"},
        {"id": "sk10", "name": "MySQL", "level": "Advanced"},
        {"id": "sk11", "name": "SQLite", "level": "Advanced"},
        {"id": "sk12", "name": "Docker", "level": "Intermediate"},
        {"id": "sk13", "name": "AWS EC2", "level": "Intermediate"},
        {"id": "sk14", "name": "Nginx", "level": "Intermediate"},
        {"id": "sk15", "name": "Git & GitLab", "level": "Advanced"},
        {"id": "sk16", "name": "REST API Design", "level": "Expert"},
        {"id": "sk17", "name": "Selenium", "level": "Intermediate"},
        {"id": "sk18", "name": "Data Analysis", "level": "Intermediate"},
        {"id": "sk19", "name": "Agile / Scrum", "level": "Intermediate"},
        {"id": "sk20", "name": "Odoo", "level": "Intermediate"},
    ],
    "certifications": [
        {
            "id": "cert1",
            "name": "Diploma in Software Engineering",
            "issuer": "AltSchool Africa School of Engineering",
            "date": "2023",
            "grade": "Distinction",
        },
        {
            "id": "cert2",
            "name": "Data Science Certification",
            "issuer": "Bincom Academy",
            "date": "2023",
            "grade": "",
        },
        {
            "id": "cert3",
            "name": "Full-Stack Web Development",
            "issuer": "SHE Hacks Africa",
            "date": "2018",
            "grade": "",
        },
        {
            "id": "cert4",
            "name": "Django Full Course",
            "issuer": "Udemy",
            "date": "2023",
            "grade": "",
        },
    ],
    "projects": [
        {
            "id": "proj1",
            "name": "Preptutor – Learning Management System",
            "technologies": "Odoo, Python, XML, JavaScript, PostgreSQL",
            "url": "",
            "description": "Developed an Odoo-based e-learning and assessment platform that streamlines teaching and learning management processes.",
            "bullets": [
                "Customized and extended Odoo modules for course creation, student enrollment, and instructor dashboards.",
                "Built custom Python models and business logic for automated grading, performance tracking, and user management.",
                "Designed interactive front-end views using Odoo's XML templates and JavaScript for enhanced user experience.",
                "Implemented role-based access control and integrated email notifications for course updates and reminders.",
                "Integrated Payment Methods.",
            ],
        },
        {
            "id": "proj2",
            "name": "ExamGenius – AI-Driven Exam Preparation Platform",
            "technologies": "FastAPI, React.js, PostgreSQL",
            "url": "",
            "description": "Full-stack AI-driven exam preparation platform helping Nigerian students master JAMB entrance examinations through intelligent tutoring, adaptive practice, and real-time performance analytics.",
            "bullets": [
                "Architected a FastAPI + PostgreSQL backend with JWT authentication, role-based access control, and a RESTful API serving 30+ endpoints across learning, CBT, analytics, and admin modules.",
                "Integrated DeepSeek V3 AI (via OpenRouter) to power a real-time AI tutor, generate personalized lesson content in English and Pidgin, and deliver context-aware explanations per topic.",
                "Built a full CBT simulation engine with a 26,500+ question bank spanning 18 JAMB subjects and 15 years (2010–2024), complete with timed sessions, instant feedback, and detailed result breakdowns.",
                "Designed a guided learning system with subject syllabuses, subtopic objectives, and post-lesson practice quizzes — guaranteeing a minimum of 20 questions per topic via intelligent fallback mapping.",
                "Implemented adaptive performance analytics tracking accuracy, streaks, strengths/weaknesses, and recommended topics per student.",
                "Deployed on AWS EC2 (Ubuntu) with Nginx reverse proxy, systemd process management, and AWS RDS PostgreSQL — achieving sub-second API response times.",
            ],
        },
        {
            "id": "proj3",
            "name": "Autojobserve – Automated Job Scraping Platform",
            "technologies": "FastAPI, Selenium, OAuth2, Pydocx",
            "url": "https://github.com/Olalekan2040-slack",
            "description": "Backend service for aggregating job postings from multiple job boards into a unified API.",
            "bullets": [
                "Designed and built REST API endpoints using FastAPI for efficient job data retrieval and delivery.",
                "Automated job collection workflows with Selenium, ensuring continuous and up-to-date listings.",
                "Integrated OAuth2 authentication and automated resume scanning via Pydocx for personalized job recommendations.",
            ],
        },
        {
            "id": "proj4",
            "name": "SmartCV – AI-Powered Resume Builder",
            "technologies": "FastAPI, React, PostgreSQL, Tailwind CSS, Docker",
            "url": "",
            "description": "Full-stack AI-powered CV builder that allows users to create professional resumes with intelligent content suggestions, real-time validation, and instant PDF generation.",
            "bullets": [
                "Engineered a FastAPI backend integrated with GPT-based AI for smart resume content recommendations.",
                "Built a React frontend with a sleek dark theme, responsive design, and live CV preview functionality.",
                "Implemented secure authentication, analytics dashboard, and premium subscription features with Stripe integration.",
                "Deployed using Docker, Redis, and Vercel, ensuring scalable performance and smooth user experience.",
            ],
        },
    ],
    "languages": [
        {"id": "lang1", "name": "English", "level": "Fluent"},
        {"id": "lang2", "name": "Yoruba", "level": "Native"},
    ],
    "custom_sections": [],
}


class Command(BaseCommand):
    help = "Seed Sharafdeen Quadri's resume into the database"

    def handle(self, *args, **options):
        # Get or create the user
        user, created = User.objects.get_or_create(
            username="sharafdeen",
            defaults={
                "email": "olalekanquadri58@gmail.com",
                "first_name": "Sharafdeen",
                "last_name": "Quadri",
            },
        )
        if created:
            user.set_password("cvcraft2024!")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created user: sharafdeen"))
        else:
            self.stdout.write("User already exists: sharafdeen")

        # Create or update the resume
        resume, r_created = Resume.objects.update_or_create(
            user=user,
            title="Sharafdeen Quadri — Full-Stack Engineer",
            defaults={
                "template_slug": "technical",
                "data": RESUME_DATA,
                "is_public": True,
                "accent_color": "#C9A84C",
                "font_family": "Inter",
            },
        )

        action = "Created" if r_created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{action} resume (pk={resume.pk})"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Public URL: http://localhost:8000/r/{resume.public_token}/"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Login -> username: sharafdeen  |  password: cvcraft2024!"
        ))
