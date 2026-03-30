"""
Seed trial@gmail.com with Sharafdeen's resume data across all 10 CV templates.
Run: python manage.py seed_trial
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from resumes.models import Resume, TEMPLATE_CHOICES

RESUME_DATA = {
    "personal": {
        "full_name": "Sharafdeen Quadri O.",
        "job_title": "Full-Stack Software Engineer",
        "email": "olalekanquadri58@gmail.com",
        "phone": "+234 000 000 0000",
        "location": "Nigeria",
        "website": "https://quaddev.com",
        "linkedin": "",
        "github": "https://github.com/Olalekan2040-slack",
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
            "position": "ICT Instructor — Mabest College, Akure",
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
                "Worked collaboratively using GitLab and Dev server, implementing version control and agile methodologies.",
            ],
        },
        {
            "id": "exp4",
            "company": "Medmina College",
            "position": "Tutor / IT Support",
            "location": "Ibadan, Oyo State",
            "start_date": "Oct 2019",
            "end_date": "March 2023",
            "current": False,
            "bullets": [
                "Taught Literature in English and supported English Language instruction, improving student comprehension and critical analysis.",
                "Actively contributed as a core member of the ICT team, providing technical support across classrooms and staff offices.",
                "Assisted in the delivery of programming and digital skills classes, strengthening students' digital literacy.",
                "Leveraged a diploma in Software Engineering to integrate technology into teaching and curriculum enhancement.",
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
                "Taught Literature in English, English Language, and Government with emphasis on literary appreciation and grammar.",
                "Prepared students for internal and external examinations using structured lesson plans.",
                "Maintained a supportive classroom environment that encouraged participation and academic discipline.",
            ],
        },
    ],
    "education": [
        {
            "id": "edu1",
            "institution": "AltSchool Africa",
            "degree": "Diploma",
            "field": "Software Engineering",
            "location": "Lagos, Nigeria",
            "start_date": "2023",
            "end_date": "2023",
            "grade": "Distinction",
            "bullets": [],
        },
        {
            "id": "edu2",
            "institution": "Fountain University",
            "degree": "BSc (Second Class Division)",
            "field": "Political Science and Public Administration",
            "location": "Osogbo, Nigeria",
            "start_date": "2016",
            "end_date": "2016",
            "grade": "Second Class",
            "bullets": [],
        },
        {
            "id": "edu3",
            "institution": "Khadob Model College",
            "degree": "O'Level",
            "field": "",
            "location": "Akure, Nigeria",
            "start_date": "2012",
            "end_date": "2012",
            "grade": "",
            "bullets": [],
        },
    ],
    "skills": [
        {"id": "sk1",  "name": "Python",               "level": "Expert"},
        {"id": "sk2",  "name": "JavaScript",            "level": "Advanced"},
        {"id": "sk3",  "name": "Django",                "level": "Expert"},
        {"id": "sk4",  "name": "FastAPI",               "level": "Expert"},
        {"id": "sk5",  "name": "Flask",                 "level": "Advanced"},
        {"id": "sk6",  "name": "React.js",              "level": "Intermediate"},
        {"id": "sk7",  "name": "HTML & CSS",            "level": "Expert"},
        {"id": "sk8",  "name": "SQL / PostgreSQL",      "level": "Advanced"},
        {"id": "sk9",  "name": "REST API Design",       "level": "Expert"},
        {"id": "sk10", "name": "Docker",                "level": "Intermediate"},
        {"id": "sk11", "name": "Git / GitLab / GitHub", "level": "Advanced"},
        {"id": "sk12", "name": "Selenium / Automation", "level": "Intermediate"},
        {"id": "sk13", "name": "Data Analysis",         "level": "Intermediate"},
        {"id": "sk14", "name": "Agile / Scrum",         "level": "Advanced"},
        {"id": "sk15", "name": "Linux / Ubuntu",        "level": "Intermediate"},
        {"id": "sk16", "name": "AWS EC2 / RDS",         "level": "Intermediate"},
        {"id": "sk17", "name": "Nginx",                 "level": "Intermediate"},
        {"id": "sk18", "name": "Tailwind CSS",          "level": "Advanced"},
        {"id": "sk19", "name": "Odoo",                  "level": "Intermediate"},
        {"id": "sk20", "name": "JWT / OAuth2",          "level": "Advanced"},
    ],
    "certifications": [
        {
            "id": "cert1",
            "name": "Diploma in Software Engineering (Distinction)",
            "issuer": "AltSchool Africa",
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
            "name": "Full-stack Web Development",
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
                "Implemented role-based access control and integrated email notifications. Integrated Payment Methods.",
            ],
        },
        {
            "id": "proj2",
            "name": "ExamGenius – AI-Driven Exam Prep Platform",
            "technologies": "FastAPI, React.js, PostgreSQL, DeepSeek V3 AI",
            "url": "",
            "description": "Full-stack AI-driven platform helping Nigerian students master JAMB entrance examinations through intelligent tutoring and adaptive practice.",
            "bullets": [
                "Architected a FastAPI + PostgreSQL backend with JWT auth, role-based access control, and 30+ RESTful endpoints.",
                "Integrated DeepSeek V3 AI for a real-time tutor generating personalized lesson content in English and Pidgin.",
                "Built a full CBT engine with 26,500+ question bank spanning 18 JAMB subjects and 15 years (2010–2024).",
                "Deployed on AWS EC2 with Nginx, systemd, and AWS RDS — achieving sub-second API response times.",
            ],
        },
        {
            "id": "proj3",
            "name": "Autojobserve – Automated Job Scraping Platform",
            "technologies": "FastAPI, Selenium, OAuth2, Pydocx",
            "url": "https://github.com/Olalekan2040-slack",
            "description": "Backend service aggregating job postings from multiple job boards into a unified API with automated resume scanning.",
            "bullets": [
                "Designed and built REST API endpoints using FastAPI for efficient job data retrieval and delivery.",
                "Automated job collection workflows with Selenium, ensuring continuous and up-to-date listings.",
                "Integrated OAuth2 authentication and automated resume scanning via Pydocx for personalized job recommendations.",
            ],
        },
        {
            "id": "proj4",
            "name": "SmartCV – AI-Powered Resume Builder",
            "technologies": "FastAPI, React, PostgreSQL, Tailwind CSS, Docker, Stripe",
            "url": "",
            "description": "Full-stack AI-powered CV builder allowing users to create professional resumes with intelligent content suggestions and instant PDF generation.",
            "bullets": [
                "Engineered a FastAPI backend integrated with GPT-based AI for smart resume content recommendations.",
                "Built a React frontend with dark theme, responsive design, and live CV preview.",
                "Implemented secure authentication, analytics dashboard, and premium subscription features with Stripe.",
                "Deployed using Docker, Redis, and Vercel, ensuring scalable performance.",
            ],
        },
    ],
    "languages": [
        {"id": "lang1", "name": "English",  "level": "Fluent"},
        {"id": "lang2", "name": "Yoruba",   "level": "Native"},
    ],
    "custom_sections": [],
}

TEMPLATE_SLUGS = [slug for slug, _ in TEMPLATE_CHOICES]


class Command(BaseCommand):
    help = 'Seed trial@gmail.com with Sharafdeen resume data across all 10 templates'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(email='trial@gmail.com')
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'User trial@gmail.com not found. Create the account first via the signup page.'
            ))
            return

        # Delete existing seeded resumes for this user to allow re-run
        deleted, _ = Resume.objects.filter(user=user).delete()
        if deleted:
            self.stdout.write(f'  Removed {deleted} existing resume(s) for trial@gmail.com')

        for slug, label in TEMPLATE_CHOICES:
            resume = Resume.objects.create(
                user=user,
                title=f'Sharafdeen Quadri — {label}',
                template_slug=slug,
                data=RESUME_DATA,
                is_public=True,
            )
            self.stdout.write(self.style.SUCCESS(
                f'  ✓  [{slug:12s}]  pk={resume.pk}  /dashboard/{resume.pk}/print/'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {len(TEMPLATE_SLUGS)} resumes created for trial@gmail.com.'
        ))
        self.stdout.write('Open each print URL above in your browser to preview.')
