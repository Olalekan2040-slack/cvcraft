import json
import os
import re
import copy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.conf import settings
from .models import Resume, ExportLog, DEFAULT_RESUME_DATA, TEMPLATE_CHOICES


# ── Dashboard ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    resumes = Resume.objects.filter(user=request.user)
    free_limit = settings.FREE_RESUME_LIMIT
    is_pro = getattr(request.user, 'subscription',
                     None) and request.user.subscription.is_active
    can_create = is_pro or resumes.count() < free_limit
    return render(request, 'resumes/dashboard.html', {
        'resumes': resumes,
        'free_limit': free_limit,
        'is_pro': is_pro,
        'can_create': can_create,
        'resume_count': resumes.count(),
    })


# ── Create / Duplicate / Delete ─────────────────────────────────────────────

@login_required
def create_resume(request):
    user = request.user
    resumes = Resume.objects.filter(user=user)
    is_pro = getattr(user, 'subscription',
                     None) and user.subscription.is_active
    if not is_pro and resumes.count() >= settings.FREE_RESUME_LIMIT:
        messages.warning(
            request, 'Free plan allows up to 3 resumes. Upgrade to Pro for unlimited.')
        return redirect('resumes:dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', 'My Resume')
        template = request.POST.get('template', 'modern')
        resume = Resume.objects.create(
            user=user,
            title=title,
            template_slug=template,
            data=DEFAULT_RESUME_DATA.copy(),
        )
        return redirect('resumes:builder', pk=resume.pk)

    templates = TEMPLATE_CHOICES
    return render(request, 'resumes/choose_template.html', {'templates': templates})


@login_required
@require_POST
def duplicate_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    user = request.user
    resumes = Resume.objects.filter(user=user)
    is_pro = getattr(user, 'subscription',
                     None) and user.subscription.is_active
    if not is_pro and resumes.count() >= settings.FREE_RESUME_LIMIT:
        messages.warning(request, 'Upgrade to Pro to create more resumes.')
        return redirect('resumes:dashboard')

    new_resume = Resume.objects.create(
        user=user,
        title=f'{resume.title} (Copy)',
        template_slug=resume.template_slug,
        data=resume.data,
        accent_color=resume.accent_color,
        font_family=resume.font_family,
    )
    messages.success(request, 'Resume duplicated successfully.')
    return redirect('resumes:dashboard')


@login_required
@require_POST
def delete_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    resume.delete()
    messages.success(request, 'Resume deleted.')
    return redirect('resumes:dashboard')


@login_required
@require_POST
def rename_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    new_title = request.POST.get('title', '').strip()
    if new_title:
        resume.title = new_title
        resume.save(update_fields=['title'])
    return JsonResponse({'success': True, 'title': resume.title})


# ── Builder ──────────────────────────────────────────────────────────────────

@login_required
def builder(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    resume_data = resume.get_data()
    templates = TEMPLATE_CHOICES
    sections = [
        ('personal', 'Personal', 'user'),
        ('experience', 'Experience', 'briefcase'),
        ('education', 'Education', 'graduation-cap'),
        ('skills', 'Skills', 'star'),
        ('certifications', 'Certs', 'award'),
        ('projects', 'Projects', 'code-2'),
        ('languages', 'Languages', 'globe'),
    ]
    return render(request, 'resumes/builder.html', {
        'resume': resume,
        'resume_data_json': json.dumps(resume_data),
        'templates': templates,
        'sections': sections,
    })


@login_required
@require_POST
def save_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    try:
        payload = json.loads(request.body)
        resume.data = payload.get('data', resume.data)
        resume.title = payload.get('title', resume.title)
        resume.template_slug = payload.get(
            'template_slug', resume.template_slug)
        resume.accent_color = payload.get('accent_color', resume.accent_color)
        resume.font_family = payload.get('font_family', resume.font_family)
        resume.save()
        return JsonResponse({'success': True, 'updated_at': resume.updated_at.strftime('%b %d, %Y %H:%M')})
    except (json.JSONDecodeError, Exception) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ── Preview (partial HTML) ───────────────────────────────────────────────────

@login_required
def preview_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    resume_data = resume.get_data()
    template_name = f'resume_templates/{resume.template_slug}.html'
    return render(request, template_name, {
        'resume': resume,
        'data': resume_data,
        'preview_mode': True,
    })


def public_view(request, token):
    resume = get_object_or_404(Resume, public_token=token, is_public=True)
    resume_data = resume.get_data()
    template_name = f'resume_templates/{resume.template_slug}.html'
    return render(request, template_name, {
        'resume': resume,
        'data': resume_data,
        'preview_mode': False,
        'public_pdf_url': request.build_absolute_uri(f'/r/{token}/pdf/'),
    })


def public_pdf_download(request, token):
    """Download PDF for a public resume — redirects to browser print page."""
    resume = get_object_or_404(Resume, public_token=token, is_public=True)
    from django.urls import reverse
    return redirect(reverse('resume_public_print', kwargs={'token': token}))


def public_print_view(request, token):
    """Print-ready page for a public resume (no login required)."""
    resume = get_object_or_404(Resume, public_token=token, is_public=True)
    from django.template.loader import render_to_string
    template_name = f'resume_templates/{resume.template_slug}.html'
    resume_html = render_to_string(template_name, {
        'resume': resume,
        'data': resume.get_data(),
        'for_pdf': True,
        'preview_mode': False,
    }, request=request)
    name = resume.get_data().get('personal', {}).get('full_name', resume.title)
    public_url = request.build_absolute_uri(resume.get_public_url())
    return render(request, 'resumes/print_page.html', {
        'title': f"{name}'s Resume",
        'resume_html': resume_html,
        'back_url': public_url,
        'auto_print': True,
    })


# ── Toggle Public Link ───────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_public(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    resume.is_public = not resume.is_public
    resume.save(update_fields=['is_public'])
    return JsonResponse({'success': True, 'is_public': resume.is_public,
                         'public_url': request.build_absolute_uri(resume.get_public_url())})


# ── PDF Export ───────────────────────────────────────────────────────────────

@login_required
def export_pdf(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    is_pro = getattr(request.user, 'subscription',
                     None) and request.user.subscription.is_active

    # Check export limits for free users
    if not is_pro:
        from django.utils import timezone
        month_start = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        exports_this_month = ExportLog.objects.filter(
            user=request.user, format='pdf', exported_at__gte=month_start
        ).count()
        if exports_this_month >= settings.FREE_EXPORT_LIMIT:
            messages.warning(
                request, 'Free plan allows 1 PDF export per month. Upgrade to Pro.')
            return redirect('resumes:builder', pk=pk)

    ExportLog.objects.create(user=request.user, resume=resume, format='pdf')
    return redirect('resumes:print_resume', pk=pk)


@login_required
def print_resume(request, pk):
    """Render a print-ready page with auto window.print()."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    from django.template.loader import render_to_string
    template_name = f'resume_templates/{resume.template_slug}.html'
    resume_html = render_to_string(template_name, {
        'resume': resume,
        'data': resume.get_data(),
        'for_pdf': True,
        'preview_mode': False,
    }, request=request)
    back_url = request.build_absolute_uri(f'/dashboard/{resume.pk}/')
    return render(request, 'resumes/print_page.html', {
        'title': resume.title,
        'resume_html': resume_html,
        'back_url': back_url,
        'auto_print': True,
    })


# ── JSON Export / Import ─────────────────────────────────────────────────────

@login_required
def export_json(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    data = {
        'title': resume.title,
        'template_slug': resume.template_slug,
        'accent_color': resume.accent_color,
        'font_family': resume.font_family,
        'data': resume.get_data(),
    }
    ExportLog.objects.create(user=request.user, resume=resume, format='json')
    response = HttpResponse(json.dumps(data, indent=2),
                            content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{resume.title}_backup.json"'
    return response


# ── AI Assist (Gemini) ───────────────────────────────────────────────────────

def _gemini_generate(prompt: str) -> str:
    """Call Gemini 2.0 Flash and return the text response."""
    from google import genai
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError('GEMINI_API_KEY not configured.')
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
    )
    return response.text.strip()


@login_required
@require_POST
def ai_generate(request):
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({'error': 'AI service not configured.'}, status=503)

    try:
        payload = json.loads(request.body)
        action = payload.get('action', 'improve')
        content = payload.get('content', '')
        context = payload.get('context', '')

        prompts = {
            'summary': (
                f"Write a compelling, ATS-friendly professional resume summary (2-3 sentences) "
                f"for someone with this background: {context}. Output only the summary text."
            ),
            'improve': (
                f"Rewrite this resume bullet point to be more impactful, action-oriented, and "
                f"quantifiable where possible. Keep it concise (1-2 lines): {content}"
            ),
            'keywords': (
                f"List 10 powerful ATS resume keywords for this job description. "
                f"Output as a comma-separated list only: {context}"
            ),
        }

        result = _gemini_generate(prompts.get(action, prompts['improve']))
        return JsonResponse({'success': True, 'result': result})

    except Exception as e:
        err = str(e).lower()
        if 'quota' in err or '429' in err or 'exhausted' in err or 'rate' in err:
            return JsonResponse({'error': 'AI quota exceeded. Please try again later or upgrade your Gemini plan.'}, status=429)
        return JsonResponse({'error': str(e)}, status=500)


# ── CV Upload & Parse ─────────────────────────────────────────────────────────

# ── Rule-based Smart CV Parser ───────────────────────────────────────────────

def _parse_cv_smart(text: str) -> dict:
    """
    Parse a raw CV text string into structured resume data using regex + heuristics.
    No external API required.
    """
    data = {
        'personal': {
            'full_name': '', 'job_title': '', 'email': '', 'phone': '',
            'location': '', 'website': '', 'linkedin': '', 'github': '', 'summary': ''
        },
        'experience': [], 'education': [], 'skills': [],
        'certifications': [], 'projects': [], 'languages': [], 'custom_sections': []
    }

    text = re.sub(r'\r\n|\r', '\n', text)
    lines = text.split('\n')
    clean = [l.strip() for l in lines]

    # ── Contact fields (regex, very reliable) ────────────────────────────────
    m = re.search(r'[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}', text)
    if m:
        data['personal']['email'] = m.group()

    m = re.search(r'(?:\+?\d[\d\s\-\(\)\.]{6,}\d)', text)
    if m:
        data['personal']['phone'] = re.sub(r'\s+', ' ', m.group().strip())

    m = re.search(r'linkedin\.com/in/([\w\-]+)', text, re.I)
    if m:
        data['personal']['linkedin'] = 'https://linkedin.com/in/' + m.group(1)

    m = re.search(r'github\.com/([\w\-]+)', text, re.I)
    if m:
        data['personal']['github'] = 'https://github.com/' + m.group(1)

    m = re.search(
        r'https?://(?!(?:www\.)?(?:linkedin|github))[^\s,<>"]+', text, re.I)
    if m:
        data['personal']['website'] = m.group()

    m = re.search(
        r'\b([A-Z][a-zA-Z\s]+,\s*(?:[A-Z]{2}|[A-Z][a-zA-Z]+))\b', text)
    if m:
        data['personal']['location'] = m.group().strip()

    # ── Name: first short non-contact line (Title Case or ALL CAPS) ──────────
    for line in clean[:8]:
        if (len(line) > 2 and len(line) < 60 and '@' not in line
                and not re.search(r'[\d\(\)\+]', line)
                and re.match(r'^[A-Z][a-zA-Z\s\.\-]+$', line)):
            data['personal']['full_name'] = line
            break

    # ── Job title: first plausible title line after the name ─────────────────
    name_found = False
    for line in clean[:12]:
        if line == data['personal']['full_name']:
            name_found = True
            continue
        if name_found and line and '@' not in line and len(line) < 80:
            if not re.search(r'^https?://', line) and not re.search(r'\d{4}', line):
                data['personal']['job_title'] = line
                break

    # ── Section detection ────────────────────────────────────────────────────
    HEADERS = {
        'summary':       r'^(summary|professional\s+summary|profile|objective|about\s+me|career\s+objective)',
        'experience':    r'^(work\s+experience|experience|employment|professional\s+experience|work\s+history|career\s+history)',
        'education':     r'^(education|academic|qualifications?|educational\s+background)',
        'skills':        r'^(skills?|technical\s+skills?|core\s+competencies|key\s+skills?|expertise|technologies)',
        'projects':      r'^(projects?|personal\s+projects?|key\s+projects?|portfolio|side\s+projects?)',
        'certifications': r'^(certifications?|certificates?|licenses?|professional\s+development|courses?|training)',
        'languages':     r'^(languages?|language\s+proficiency)',
    }

    section_starts = {}   # section_name -> line index
    ordered = []          # [(line_idx, section_name), ...]
    for i, line in enumerate(clean):
        for name, pat in HEADERS.items():
            if re.match(pat, line, re.I) and len(line) < 60:
                if name not in section_starts:
                    section_starts[name] = i
                    ordered.append((i, name))
    ordered.sort()

    def section_lines(name):
        if name not in section_starts:
            return []
        start = section_starts[name] + 1
        end = len(clean)
        for idx, n in ordered:
            if idx > section_starts[name]:
                end = idx
                break
        return clean[start:end]

    # ── Summary ───────────────────────────────────────────────────────────────
    sl = section_lines('summary')
    if sl:
        data['personal']['summary'] = ' '.join(l for l in sl if l)

    # ── Skills ────────────────────────────────────────────────────────────────
    sk_id = 1
    for line in section_lines('skills'):
        if not line:
            continue
        for part in re.split(r'[,|•·]', line):
            part = part.strip()
            if 2 < len(part) < 50:
                data['skills'].append(
                    {'id': f'sk{sk_id}', 'name': part, 'level': 'Intermediate'})
                sk_id += 1

    # ── Experience ────────────────────────────────────────────────────────────
    DATE = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*\d{4}|\d{4}'
    DATE_RANGE = re.compile(
        rf'({DATE})\s*[-\u2013\u2014to]+\s*((?:{DATE})|present|current|till\s+date)', re.I
    )
    exp_id = 1
    cur_exp = None
    exp_lines = section_lines('experience')
    for line in exp_lines:
        dr = DATE_RANGE.search(line)
        if dr:
            if cur_exp:
                data['experience'].append(cur_exp)
            end_raw = dr.group(2)
            is_cur = bool(
                re.search(r'present|current|till\s+date', end_raw, re.I))
            cur_exp = {
                'id': f'exp{exp_id}', 'company': '', 'position': '',
                'location': '', 'start_date': dr.group(1),
                'end_date': '' if is_cur else end_raw,
                'current': is_cur, 'bullets': []
            }
            remainder = DATE_RANGE.sub('', line).strip(' |-')
            if remainder:
                parts = re.split(r'\s*[|@]\s*|\s{2,}', remainder, maxsplit=1)
                if len(parts) == 2:
                    cur_exp['position'], cur_exp['company'] = parts[0].strip(
                    ), parts[1].strip()
                else:
                    cur_exp['company'] = remainder
            exp_id += 1
        elif cur_exp is not None:
            stripped = re.sub(
                r'^[•\-\*\u25aa\u25ba\u2192\u2713\u2714\s]+', '', line).strip()
            if not stripped:
                continue
            if not cur_exp['company'] and not re.match(r'^[•\-\*]', line):
                if not cur_exp['position']:
                    cur_exp['position'] = stripped
                elif not cur_exp['company']:
                    cur_exp['company'] = stripped
            else:
                cur_exp['bullets'].append(stripped)
    if cur_exp:
        data['experience'].append(cur_exp)

    # ── Education ─────────────────────────────────────────────────────────────
    edu_id = 1
    cur_edu = None
    for line in section_lines('education'):
        if not line:
            continue
        yr = re.search(r'\d{4}', line)
        if yr and (cur_edu is None or cur_edu.get('institution')):
            if cur_edu:
                data['education'].append(cur_edu)
            cur_edu = {
                'id': f'edu{edu_id}', 'institution': '', 'degree': '',
                'field': '', 'location': '', 'start_date': '', 'end_date': '', 'grade': '', 'bullets': []
            }
            years = re.findall(r'\d{4}', line)
            cur_edu['start_date'] = years[0]
            cur_edu['end_date'] = years[-1] if len(years) > 1 else ''
            remainder = re.sub(
                r'\d{4}(?:\s*[-\u2013\u2014]\s*(?:\d{4}|present))?', '', line).strip(' |-')
            if remainder:
                parts = re.split(r'\s*[,|]\s*|\s{2,}', remainder, maxsplit=1)
                if len(parts) == 2:
                    cur_edu['degree'], cur_edu['institution'] = parts[0].strip(
                    ), parts[1].strip()
                else:
                    cur_edu['institution'] = remainder
            edu_id += 1
        elif cur_edu is not None:
            stripped = re.sub(r'^[•\-\*\s]+', '', line).strip()
            if stripped:
                if not cur_edu['institution']:
                    cur_edu['institution'] = stripped
                else:
                    cur_edu['bullets'].append(stripped)
    if cur_edu:
        data['education'].append(cur_edu)

    # ── Projects ──────────────────────────────────────────────────────────────
    proj_id = 1
    cur_proj = None
    URL_PAT = re.compile(r'https?://\S+', re.I)
    for line in section_lines('projects'):
        if not line:
            continue
        url = URL_PAT.search(line)
        # New project: starts with capital, short, not a bullet
        if re.match(r'^[A-Z\d]', line) and not re.match(r'^[•\-\*]', line) and len(line) < 80:
            if cur_proj:
                data['projects'].append(cur_proj)
            cur_proj = {
                'id': f'proj{proj_id}', 'name': URL_PAT.sub('', line).strip(),
                'technologies': '', 'url': url.group() if url else '',
                'description': '', 'bullets': []
            }
            proj_id += 1
        elif cur_proj:
            stripped = re.sub(r'^[•\-\*\s]+', '', line).strip()
            if not stripped:
                continue
            tm = re.match(
                r'^(?:tech(?:nologies)?|stack|built\s+with|tools?)[:\s]+(.+)', stripped, re.I)
            if tm:
                cur_proj['technologies'] = tm.group(1)
            elif not cur_proj['description']:
                cur_proj['description'] = stripped
            else:
                cur_proj['bullets'].append(stripped)
    if cur_proj:
        data['projects'].append(cur_proj)

    # ── Certifications ────────────────────────────────────────────────────────
    cert_id = 1
    for line in section_lines('certifications'):
        stripped = re.sub(r'^[•\-\*\s]+', '', line).strip()
        if not stripped:
            continue
        yr = re.search(r'\d{4}', stripped)
        name = re.sub(r'\d{4}', '', stripped).strip(' -\u2013|')
        data['certifications'].append({
            'id': f'cert{cert_id}', 'name': name,
            'issuer': '', 'date': yr.group() if yr else '', 'grade': ''
        })
        cert_id += 1

    # ── Languages ─────────────────────────────────────────────────────────────
    LEVELS = ['Native', 'Fluent', 'Advanced',
              'Intermediate', 'Basic', 'Elementary']
    lang_id = 1
    for line in section_lines('languages'):
        for part in re.split(r'[,|•]', line):
            part = part.strip()
            if not part:
                continue
            level = 'Intermediate'
            for lvl in LEVELS:
                if re.search(lvl, part, re.I):
                    level = lvl
                    part = re.sub(lvl, '', part, flags=re.I).strip(' \t-–/:,')
                    break
            if part and len(part) < 40:
                data['languages'].append(
                    {'id': f'lang{lang_id}', 'name': part, 'level': level})
                lang_id += 1

    return data


def _extract_text_from_pdf(file_obj) -> str:
    """Extract all text from an uploaded PDF using pdfplumber."""
    import pdfplumber
    text_parts = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return '\n'.join(text_parts)


def _extract_text_from_docx(file_obj) -> str:
    """Extract all text from an uploaded DOCX file."""
    import docx
    doc = docx.Document(file_obj)
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())


CV_PARSE_PROMPT = """
You are an expert CV parser. Extract all information from the following CV text and return it as valid JSON only — no markdown fences, no extra text, just the raw JSON.

Use this exact structure:
{{
  "personal": {{
    "full_name": "",
    "job_title": "",
    "email": "",
    "phone": "",
    "location": "",
    "website": "",
    "linkedin": "",
    "github": "",
    "summary": ""
  }},
  "experience": [
    {{
      "id": "exp1",
      "company": "",
      "position": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "current": false,
      "bullets": []
    }}
  ],
  "education": [
    {{
      "id": "edu1",
      "institution": "",
      "degree": "",
      "field": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "grade": "",
      "bullets": []
    }}
  ],
  "skills": [
    {{"id": "sk1", "name": "", "level": "Intermediate"}}
  ],
  "certifications": [
    {{"id": "cert1", "name": "", "issuer": "", "date": "", "grade": ""}}
  ],
  "projects": [
    {{
      "id": "proj1",
      "name": "",
      "technologies": "",
      "url": "",
      "description": "",
      "bullets": []
    }}
  ],
  "languages": [
    {{"id": "lang1", "name": "", "level": "Fluent"}}
  ],
  "custom_sections": []
}}

Rules:
- Extract ALL experience entries, education entries, projects, skills, certifications, and languages found.
- For skills, assign level "Expert", "Advanced", "Intermediate", or "Basic" based on context clues (years, proficiency words).
- Keep bullet points as short, clean statements (remove leading •, -, * characters).
- If a field is not found, use an empty string or empty list.
- For "current" field, set true if end_date contains "present", "current", "till date", or similar.
- Generate unique ids like exp1, exp2, edu1, sk1, etc.
- Return ONLY the JSON object. No explanation.

CV TEXT:
{cv_text}
"""


@login_required
def upload_cv(request):
    """
    POST: Accept a PDF or DOCX file, extract text, and use Gemini to parse
    it into structured resume JSON. Returns JSON to be loaded into the builder.
    """
    if request.method == 'GET':
        templates = TEMPLATE_CHOICES
        extracted_fields = [
            'Contact Info', 'Work History', 'Education', 'Skills',
            'Projects', 'Certifications', 'Languages', 'Summary',
        ]
        return render(request, 'resumes/upload_cv.html', {'templates': templates, 'extracted_fields': extracted_fields})

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    uploaded_file = request.FILES.get('cv_file')
    if not uploaded_file:
        return JsonResponse({'error': 'No file uploaded.'}, status=400)

    filename = uploaded_file.name.lower()
    max_size = 5 * 1024 * 1024  # 5 MB
    if uploaded_file.size > max_size:
        return JsonResponse({'error': 'File too large. Maximum size is 5 MB.'}, status=400)

    # Extract text
    try:
        if filename.endswith('.pdf'):
            cv_text = _extract_text_from_pdf(uploaded_file)
        elif filename.endswith('.docx'):
            cv_text = _extract_text_from_docx(uploaded_file)
        elif filename.endswith('.doc'):
            return JsonResponse({'error': 'Legacy .doc files are not supported. Please save as .docx or .pdf.'}, status=400)
        else:
            return JsonResponse({'error': 'Unsupported file type. Upload a PDF or DOCX file.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Could not read file: {str(e)}'}, status=400)

    if not cv_text or len(cv_text.strip()) < 50:
        return JsonResponse({'error': 'Could not extract text from the file. Make sure it is not a scanned image-only PDF.'}, status=400)

    # Cap text length to avoid huge Gemini requests
    cv_text = cv_text[:8000]

    # Call Gemini to parse
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return JsonResponse({'error': 'AI service not configured.'}, status=503)

    try:
        parsed_data = _parse_cv_smart(cv_text)
    except Exception as e:
        return JsonResponse({'error': f'CV parsing failed: {str(e)}'}, status=500)

    # Get chosen template and create resume
    template_slug = request.POST.get('template', 'modern')
    title = parsed_data.get('personal', {}).get(
        'full_name', '') or 'Imported Resume'
    title = f"{title}'s Resume"

    user = request.user
    resumes = Resume.objects.filter(user=user)
    is_pro = getattr(user, 'subscription',
                     None) and user.subscription.is_active
    if not is_pro and resumes.count() >= settings.FREE_RESUME_LIMIT:
        return JsonResponse({'error': 'Free plan allows up to 3 resumes. Upgrade to Pro for unlimited.'}, status=403)

    resume = Resume.objects.create(
        user=user,
        title=title,
        template_slug=template_slug,
        data=parsed_data,
    )

    return JsonResponse({
        'success': True,
        'resume_pk': resume.pk,
        'redirect_url': f'/dashboard/{resume.pk}/',
        'name': title,
    })


# ── ATS Score ────────────────────────────────────────────────────────────────

@login_required
def ats_score(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    data = resume.get_data()
    score, issues, tips = _calculate_ats_score(data, resume.template_slug)
    return JsonResponse({'score': score, 'issues': issues, 'tips': tips})


def _calculate_ats_score(data, template_slug):
    score = 0
    issues = []
    tips = []
    personal = data.get('personal', {})

    if personal.get('full_name'):
        score += 10
    else:
        issues.append('Missing full name')

    if personal.get('email'):
        score += 10
    else:
        issues.append('Missing email')

    if personal.get('phone'):
        score += 5
    if personal.get('location'):
        score += 5

    summary = personal.get('summary', '')
    if len(summary) >= 50:
        score += 15
    elif summary:
        score += 5
        tips.append(
            'Expand your professional summary to 2-3 sentences for better ATS performance.')
    else:
        issues.append('Missing professional summary')

    experience = data.get('experience', [])
    if experience:
        score += 20
        for exp in experience:
            bullets = exp.get('bullets', [])
            if bullets:
                score += 5
                break
        if not any(exp.get('bullets') for exp in experience):
            tips.append('Add bullet points to your work experience entries.')
    else:
        issues.append('No work experience listed')

    education = data.get('education', [])
    if education:
        score += 15
    else:
        issues.append('No education listed')

    skills = data.get('skills', [])
    if len(skills) >= 5:
        score += 15
    elif skills:
        score += 5
        tips.append(
            'Add more skills (aim for 8-12) to improve keyword matching.')
    else:
        issues.append('No skills listed')

    # ATS-safe templates boost score
    ats_safe = ['classic', 'modern', 'clean', 'technical', 'student']
    if template_slug in ats_safe:
        score = min(score + 5, 100)
    else:
        tips.append(
            'Consider using an ATS-optimized template (Classic, Modern, or Clean).')

    return min(score, 100), issues, tips
