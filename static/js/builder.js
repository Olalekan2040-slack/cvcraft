// ═══════════════════════════════════════════════════════════
// CVCraft Builder — Alpine.js Component
// ═══════════════════════════════════════════════════════════

function builder() {
    return {
        // State
        data: {},
        resumeTitle: RESUME_TITLE,
        currentTemplate: CURRENT_TEMPLATE,
        accentColor: ACCENT_COLOR,
        fontFamily: FONT_FAMILY,

        // UI state
        activeSection: 'personal',
        saving: false,
        saveStatus: 'All changes saved',
        previewScale: 0.75,

        // ATS
        atsScore: null,
        atsIssues: [],
        atsTips: [],
        atsModal: false,

        // AI
        aiModal: false,
        aiLoading: false,
        aiResult: '',
        aiError: '',
        aiTarget: null,
        newSkill: '',

        // Debounce timers
        _previewTimer: null,
        _saveTimer: null,

        init() {
            // Deep clone resume data
            this.data = JSON.parse(JSON.stringify(RESUME_DATA));

            // Ensure arrays exist
            ['experience', 'education', 'skills', 'certifications', 'projects', 'languages', 'custom_sections'].forEach(key => {
                if (!Array.isArray(this.data[key])) this.data[key] = [];
            });

            if (!this.data.personal) this.data.personal = {};

            // Auto-save every 30 seconds
            setInterval(() => this.autoSave(), 30000);

            // Init sortable for experience
            this.$nextTick(() => {
                this.initSortable();
                lucide.createIcons();
            });
        },

        // ── Preview Management ─────────────────────────────

        debouncedPreview() {
            clearTimeout(this._previewTimer);
            this.saveStatus = 'Unsaved changes...';
            this._previewTimer = setTimeout(() => {
                this.updatePreview();
                this.autoSave();
            }, 800);
        },

        updatePreview() {
            const iframe = document.getElementById('preview-iframe');
            if (!iframe) return;

            // Save current data first, then reload iframe
            this.saveResume(true).then(() => {
                iframe.src = PREVIEW_URL + '?t=' + Date.now();
            });
        },

        // ── Save ───────────────────────────────────────────

        async saveResume(silent = false) {
            if (this.saving) return;
            this.saving = true;

            const payload = {
                title: this.resumeTitle,
                template_slug: this.currentTemplate,
                accent_color: this.accentColor,
                font_family: this.fontFamily,
                data: this.data,
            };

            try {
                const resp = await fetch(SAVE_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN,
                    },
                    body: JSON.stringify(payload),
                });
                const result = await resp.json();
                if (result.success && !silent) {
                    this.saveStatus = `Saved ${result.updated_at}`;
                } else if (!result.success) {
                    this.saveStatus = 'Save failed';
                }
            } catch (e) {
                if (!silent) this.saveStatus = 'Save failed';
            } finally {
                this.saving = false;
            }
        },

        autoSave() {
            clearTimeout(this._saveTimer);
            this._saveTimer = setTimeout(() => this.saveResume(true), 2000);
        },

        // ── Template Switch ────────────────────────────────

        switchTemplate(slug) {
            this.currentTemplate = slug;
            this.updatePreview();
        },

        // ── Section Data Helpers ───────────────────────────

        addExperience() {
            this.data.experience.push({
                position: '', company: '', start_date: '', end_date: 'Present',
                location: '', description: '', bullets: [], _open: true,
            });
            this.$nextTick(() => lucide.createIcons());
        },

        addEducation() {
            this.data.education.push({
                degree: '', institution: '', start_date: '', end_date: '',
                location: '', gpa: '', achievements: '', _open: true,
            });
            this.$nextTick(() => lucide.createIcons());
        },

        addSkill() {
            const name = this.newSkill.trim();
            if (!name) return;
            // Check duplicate
            const exists = this.data.skills.some(s => (s.name || s) === name);
            if (!exists) {
                this.data.skills.push({ name });
                this.debouncedPreview();
            }
            this.newSkill = '';
        },

        addCertification() {
            this.data.certifications.push({ name: '', issuer: '', date: '' });
            this.$nextTick(() => lucide.createIcons());
        },

        addProject() {
            this.data.projects.push({
                name: '', tech_stack: '', url: '', description: '', _open: true,
            });
            this.$nextTick(() => lucide.createIcons());
        },

        addLanguage() {
            this.data.languages.push({ name: '', level: 'Fluent' });
        },

        addBullet(exp) {
            if (!exp.bullets) exp.bullets = [];
            exp.bullets.push('');
            this.$nextTick(() => lucide.createIcons());
        },

        removeItem(arr, idx) {
            arr.splice(idx, 1);
            this.debouncedPreview();
        },

        // ── ATS Score ──────────────────────────────────────

        async checkATS() {
            try {
                const resp = await fetch(ATS_URL, {
                    headers: { 'X-CSRFToken': CSRF_TOKEN },
                });
                const result = await resp.json();
                this.atsScore = result.score;
                this.atsIssues = result.issues || [];
                this.atsTips = result.tips || [];
                this.atsModal = true;
                this.$nextTick(() => lucide.createIcons());
            } catch (e) {
                console.error('ATS fetch failed', e);
            }
        },

        // ── AI Generation ──────────────────────────────────

        async aiGenerate(action, content, targetIdx) {
            this.aiModal = true;
            this.aiLoading = true;
            this.aiResult = '';
            this.aiError = '';
            this.aiTarget = { action, targetIdx };

            try {
                const resp = await fetch(AI_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN,
                    },
                    body: JSON.stringify({ action, content, context: content }),
                });
                const result = await resp.json();
                if (result.success) {
                    this.aiResult = result.result;
                } else {
                    this.aiError = result.error || 'AI generation failed.';
                }
            } catch (e) {
                this.aiError = 'Unable to connect to AI service.';
            } finally {
                this.aiLoading = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        applyAIResult() {
            if (!this.aiResult || !this.aiTarget) return;
            const { action, targetIdx } = this.aiTarget;

            if (action === 'summary') {
                this.data.personal.summary = this.aiResult;
            } else if (action === 'improve' && targetIdx !== undefined) {
                if (this.data.experience[targetIdx]) {
                    const exp = this.data.experience[targetIdx];
                    // Add as a new bullet
                    if (!exp.bullets) exp.bullets = [];
                    exp.bullets.push(this.aiResult);
                }
            }

            this.aiModal = false;
            this.updatePreview();
            this.$nextTick(() => lucide.createIcons());
        },

        // ── Sortable DnD ───────────────────────────────────

        initSortable() {
            const el = document.getElementById('experience-list');
            if (!el || typeof Sortable === 'undefined') return;
            Sortable.create(el, {
                handle: '.drag-handle',
                animation: 150,
                onEnd: (evt) => {
                    const moved = this.data.experience.splice(evt.oldIndex, 1)[0];
                    this.data.experience.splice(evt.newIndex, 0, moved);
                    this.debouncedPreview();
                },
            });
        },
    };
}
