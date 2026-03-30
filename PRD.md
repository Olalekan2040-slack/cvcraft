Product Requirements Document (PRD): Django-Based Online CV/Resume Builder (SaaS)Version: 1.0
Date: March 27, 2026
Author: Grok (based on analysis of leading platforms like Novoresume, Kickresume, and Resume.io)
Product Name Suggestion: "ResumeForge" or "CVCraft" (customizable)1. Executive SummaryThis PRD defines a full-featured, user-friendly online CV/Resume builder as a SaaS product built entirely with Django (Python backend + modern frontend). It replicates the core experience of top 2026 tools: template selection, guided/AI-assisted content entry, real-time visual preview, drag-and-drop customization, ATS optimization, and professional PDF/DOCX export.Core Value Proposition:
"Build a stunning, ATS-friendly resume in minutes — no design skills needed. Free to start, premium for power users."Monetization: Freemium model (free tier with limits + paid subscriptions via Stripe).
Target Launch: MVP in 2 days for a solo/small team developer.2. Objectives & Success MetricsBusiness Goals:Attract 10k+ monthly active users in first 6 months.
15-20% conversion to paid (typical SaaS benchmark).
High user satisfaction (NPS > 40).

Product Goals:Match or exceed usability of Novoresume/Kickresume/Resume.io.
95%+ of users complete a resume in <15 minutes.
Zero layout-breaking issues (real-time preview + robust PDF).

KPIs:Completion rate, export rate, session time.
ATS pass rate (self-reported + internal checker).
Churn, retention, subscription revenue.

3. Target Audience & User PersonasPrimary: Job seekers (fresh grads, mid-career professionals, career switchers) aged 22-45.
Secondary: Students, freelancers, recruiters (for bulk/ templates).
Personas: Alex (tech professional, wants ATS + AI), Sarah (creative marketer, needs beautiful designs), Jordan (no-experience grad, needs guidance).

4. Key Features4.1 Authentication & OnboardingEmail/password + social (Google, LinkedIn via Django Allauth).
LinkedIn import (OAuth + parse profile data into resume sections).
Guest mode → prompt account creation on first export.
Passwordless magic links (optional).

4.2 Dashboard / My ResumesList of all user resumes (thumbnails + last edited).
Duplicate, delete, rename, share (view-only link).
Folder/tags for organization (future).

4.3 Resume Builder Core (The Heart)Template Gallery (50+ templates at launch):Categorized: ATS-optimized (minimalist, no columns), Professional, Creative, Executive, Student/No-experience.
One-click "Apply template" with live switch (data preserved).

Section-Based Editor:Standard sections: Personal Info (name, title, photo, contact, location, website, LinkedIn), Professional Summary, Work Experience, Education, Skills, Certifications, Projects, Awards, Publications, Volunteer, Custom sections.
Drag-and-drop reordering (Sortable.js + HTMX).
Add/remove/reorder subsections (e.g., multiple jobs).
Rich text editor per field (TipTap or Django CKEditor) with bullet suggestions.

AI Assistance (powered by OpenAI GPT-4o or similar via API):"Generate summary" from job title + experience.
"Improve bullet" / "Rewrite for [role]".
Full section writer.
Content Analyzer (like Novoresume) — real-time scoring for length, keywords, action verbs.
Job-description matcher: Paste JD → suggest keywords/tailor bullets (premium).

Real-Time Preview:Side-by-side or full-screen WYSIWYG preview (HTML/CSS rendered via Tailwind).
Mobile/desktop toggle.

Customization:Colors, fonts (Google Fonts + safe web fonts for ATS), spacing, icons.
Layout variants per template (1-column vs 2-column where ATS-safe).
Profile photo upload (crop + resize, stored in S3/Media).

Cover Letter Builder:Separate but linked tool (same data reuse).
AI generation from resume + JD.

4.4 Export & SharingPDF (primary, using WeasyPrint — see challenges).
DOCX (optional, python-docx).
JSON export/import (for backup).
Shareable public link (view-only HTML/PDF).
Print-optimized version.

4.5 Additional Tools (MVP+)ATS Score Checker (simple keyword + format analysis).
Resume examples gallery.
Basic analytics (views on shared links).

4.6 Account & BillingProfile settings, email preferences.
Subscription management (Stripe).
Usage limits tracking.

Freemium Tiers:Free: 3 resumes, basic templates, 1 PDF export/month, no AI, watermark on PDF.
Pro ($9/mo or $79/year): Unlimited resumes, all templates, unlimited exports, full AI, cover letters, priority support, no watermark.
Team/Enterprise: Future (multi-user, branding).

5. User Flows (High-Level)New User: Visit → Choose template → Guided form fill → AI suggestions → Preview → Export (upgrade prompt).
Returning: Dashboard → Open resume → Edit → Auto-save → Export.
Import: LinkedIn OAuth → Map data → Preview.

All flows emphasize progressive disclosure (simple → advanced).6. Technical Architecture (Django-Centric)Backend: Django 5.x + PostgreSQL (JSONField for flexibility).
Frontend: HTMX + Tailwind CSS + Alpine.js (recommended for speed — no heavy React bundle).
Or Django REST Framework + React (if you prefer full SPA; more maintenance).

Key Packages:Auth: Django Allauth.
Editor/Preview: HTMX for partial updates + Tailwind.
PDF: WeasyPrint (HTML → PDF). Render resume as styled HTML template → WeasyPrint.
AI: OpenAI SDK (async Celery tasks for heavy generations).
Storage: django-storages + S3 for photos/PDFs.
Payments: django-stripe or dj-stripe.
Async: Celery + Redis (for AI, PDF gen, emails).
Testing: pytest + Playwright (E2E).

Deployment: Docker + Render/Heroku/AWS. WeasyPrint works well in containers with proper fonts/deps.Data Model (High-Level):python

User (Django)
Resume
    - user (FK)
    - title
    - template_slug
    - data (JSONField: { "personal": {...}, "experience": [list of dicts], ... })
    - custom_css (JSON or text)
    - is_public
    - created/updated

Template (or static JSON configs)
Subscription (Stripe integration)

JSONField gives ultimate flexibility while keeping queries simple.7. Non-Functional RequirementsResponsive (mobile-first).
Accessibility (WCAG 2.1 AA).
Performance: <2s page loads, instant preview updates.
Security: GDPR-compliant, data encrypted at rest, private-by-default.
SEO: Public landing + blog (for organic traffic).
Scalability: Horizontal (Celery workers).

8. Potential Challenges & Proactive SolutionsHere are the most common pitfalls when building this in Django — and exactly how to solve them:Challenge
Why It Happens
Mitigation (Django-Specific)
Complex drag-and-drop + real-time preview
Pure Django templates feel "old"
Use HTMX + Sortable.js. Preview is a separate <div> updated via POST/HTMX on every change. Auto-save every 10s.
Flexible section structure
Users want custom sections/order
Store everything in one JSONField. Validate schema on save. Admin can still edit raw JSON.
High-quality PDF generation
Resumes need perfect fonts, layout, page breaks
Use WeasyPrint (HTML + Tailwind print styles). Pre-load Google Fonts. Test page-break CSS (break-inside: avoid). Fallback to ReportLab only if pixel-perfect control needed (rarer). Deploy with system fonts (Dockerfile includes fonts-dejavu etc.).
ATS compatibility
Fancy designs break parsers
Default templates use only safe elements (no tables for experience, standard headings). Offer "ATS Mode" toggle that strips colors/images. Built-in checker flags issues.
AI cost & latency
OpenAI calls add up
Cache suggestions per user. Use cheaper models (gpt-4o-mini) for simple tasks. Rate-limit free tier. Run in Celery background tasks.
Deployment of WeasyPrint
System dependencies (Pango, Cairo, GDK)
Use official WeasyPrint Docker image or Render buildpacks. Pre-compile fonts. Test on staging.
Data privacy & compliance
Users store personal info
Explicit consent on signup. Data export/delete endpoints. Anonymize analytics.
Performance with many users
JSONField queries + preview renders
Index JSON keys if needed. Cache rendered HTML previews. Use Redis for sessions.
Feature creep (cover letters, job tracker)
Users expect "everything"
Phase it: MVP = resume + basic cover letter. v2 = full job tracker (separate app).

Bonus Tip: Start with the GeeksforGeeks or existing open-source Django resume tutorials (simple form → PDF) as a proof-of-concept, then layer on the interactive editor.9. RoadmapMVP (4-6 weeks): Auth, 10 templates, basic editor, JSON storage, WeasyPrint PDF, Stripe.
v1 (next 4 weeks): AI integration, full customization, cover letter, ATS checker.
v2: Multi-language, team accounts, analytics dashboard, personal website builder (bonus).

10. Next Steps for You (the Builder)Set up Django project + Tailwind + HTMX boilerplate.
Implement the JSON-based Resume model + basic form editor.
Add one template + WeasyPrint proof-of-concept.
Test with real users early.

This PRD gives you everything needed to spec out sprints, estimate effort, and start coding immediately. The product will feel identical to the best 2026 tools while being 100% under your control and built efficiently with Django.If you want:Detailed ERD diagrams
Sample Django models/code snippets
Wireframes (text-described)
Or a phased development plan


