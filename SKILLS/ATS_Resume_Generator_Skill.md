---
name: ats-resume
description: >
  Generate ATS-optimized, tailored Word document resumes — one per job description — by strategically
  weaving JD keywords into the summary, competencies, and experience bullets while keeping all content
  truthful to the candidate's actual experience. Use this skill whenever the user: uploads a resume
  and one or more job descriptions and wants tailored versions; asks to "tailor my resume for this
  job", "create an ATS-friendly resume", "customize my resume for each JD", or "optimize my resume
  for ATS"; shares a job tracker spreadsheet alongside their resume; mentions applying to multiple
  jobs and needing targeted resumes; or asks to match their profile to a job posting. Trigger even
  if the user doesn't say "ATS" — intent phrases like "help me apply", "prepare my resume for this
  role", or "make my resume fit this JD" are enough.
---

# ATS Resume Generator

Generate tailored, ATS-optimized Word document resumes — one per job description — by framing the candidate's real experience using the exact language each JD uses. ATS systems rank resumes by keyword match; the goal is strategic alignment, never fabrication.

## Core Principle

**Frame real experience in the JD's language.** A candidate who "tested APIs" becomes a "REST API Testing specialist" when the JD uses that phrase. Competencies get reordered, summaries get rewritten, bullets get restructured — but every claim stays truthful to the candidate's actual work.

---

## Step 1 — Extract the Resume

**From .docx uploads:**
```bash
pip install python-docx --break-system-packages -q
python3 - << 'EOF'
from docx import Document
doc = Document('path/to/resume.docx')
for p in doc.paragraphs:
    if p.text.strip():
        print(repr(p.style.name), '|', p.text)
EOF
```

Or quick plain-text dump: `pandoc -t plain resume.docx`

Capture everything: name, contact, summary, all competency lines, every job (title, company, dates, all bullets), achievements, education, certifications.

---

## Step 2 — Extract Job Descriptions

**Pasted text:** read directly from conversation context.

**From .xlsx job tracker:**
```bash
pip install openpyxl --break-system-packages -q
python3 - << 'EOF'
import openpyxl
wb = openpyxl.load_workbook('jobs.xlsx')
ws = wb.active
for i, row in enumerate(ws.iter_rows(values_only=True)):
    print(f"Row {i+1}:", row)
EOF
```

For each JD, extract:
- Company name + role title (use these for the output filename)
- Required tools/technologies (these are ATS keywords — use exact spelling)
- Key responsibilities (mirror this verb/noun language in experience bullets)
- Experience level (Senior / Lead / Specialist etc.)
- Domain context (FinTech, AI/ML, Healthcare, etc.)

---

## Step 3 — Tailor Each Resume

Modify only these four sections per JD — everything else (dates, companies, metrics) stays identical:

### Professional Summary ← highest ATS impact
- Open with the exact job title from the JD (or very close)
- Include 3–5 JD-specific keywords in the first 2 sentences
- Reference the domain if specified (FinTech, AI/ML, etc.)
- Keep to 3–4 sentences; make every word earn its place

### Core Competencies
- Reorder categories so JD-matching skills lead
- Use the JD's exact phrasing (if JD says "Playwright" not "Playwright.js", use "Playwright")
- Rename category labels to mirror JD section headings when natural
- Include tools the candidate genuinely has, even if light exposure

### Professional Experience
- Lead each role's bullets with responsibilities that match the JD
- Replace generic verbs with JD-specific language where truthful
- Keep all existing metrics (%, numbers, scale) — never invent new ones
- Add domain context that connects the candidate's work to the JD's world

### Job Title on Resume
- Mirror seniority of the target role if the experience genuinely supports it
- E.g., if candidate has 4+ years and is applying for "Senior QA Engineer", upgrade title

### Never change
- Company names, employment dates, education institution/dates
- Specific quantified achievements — only real numbers
- Skills the candidate doesn't actually have

---

## Step 4 — Generate Word Documents

The `docx` npm package is preinstalled. Always use this NODE_PATH:
```bash
NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules node your_script.js
```

### ATS-Safe Formatting Rules
- **No tables for layout** — ATS parsers often skip table content entirely
- **No text boxes or headers/footers** for important content
- **Simple fonts**: Calibri or Arial (10–11pt body, 13–14pt name)
- **Standard section names**: "Professional Summary", "Core Competencies", "Professional Experience", "Education", "Certifications" — ATS systems pattern-match these headings
- **No graphics, logos, or photos**
- **Margins**: 0.5–0.75 inch (720–1080 twips in docx-js)

### ATS-Optimal Section Order
1. Name + Contact (single line, centered)
2. Professional Summary
3. Core Competencies / Skills
4. Professional Experience (reverse chronological)
5. Key Achievements (optional — powerful for differentiating candidates)
6. Education
7. Certifications

### docx-js Structure Template
```javascript
'use strict';
const { Document, Paragraph, TextRun, Packer, AlignmentType, BorderStyle } = require('docx');
const fs = require('fs');

const FONT = 'Calibri';

// Colored underlined section headers (ATS still reads these)
function sectionHeader(title) {
  return new Paragraph({
    spacing: { before: 180, after: 60 },
    border: { bottom: { color: '1F3864', space: 1, style: BorderStyle.SINGLE, size: 8 } },
    children: [new TextRun({ text: title, bold: true, size: 24, font: FONT, color: '1F3864' })]
  });
}

function bullet(text) {
  return new Paragraph({
    indent: { left: 360 },
    spacing: { after: 40 },
    children: [
      new TextRun({ text: '•  ', size: 20, font: FONT }),
      new TextRun({ text, size: 20, font: FONT })
    ]
  });
}

// Build document
const doc = new Document({
  sections: [{
    properties: { page: { margin: { top: 720, bottom: 720, left: 1008, right: 1008 } } },
    children: [ /* paragraphs here */ ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/path/to/outputs/Resume_01_Company_Role.docx', buf);
  console.log('Done');
});
```

Key gotchas (from docx library):
- Never use `\n` — use separate `Paragraph` elements
- `pageBreakBefore: true` on first paragraph creates a clean page break
- Don't use `ShadingType.SOLID` (renders black) — use `ShadingType.CLEAR`

---

## Step 5 — File Naming

Name output files clearly so the user can identify them at a glance:
```
Resume_01_QuikHire_QA_Engineer.docx
Resume_02_SpintaDigital_Software_Testing_Specialist.docx
```

For a single resume: `Hanmant_Hudekar_Resume_CompanyName.docx`

---

## Step 6 — Verify Output

After generating, spot-check the first and last resume visually:
```bash
python3 /path/to/skills/docx/scripts/office/soffice.py --headless --convert-to pdf output.docx
pdftoppm -jpeg -r 100 output.pdf page && ls page-*.jpg
# Then Read the page images to confirm clean formatting
```

---

## ATS Keyword Strategy

### Keyword Placement Priority (highest to lowest weight)
1. Job title / headline
2. First paragraph of summary
3. Skills/Competencies section headings and values
4. Job titles in experience section
5. First bullet under each role

### Keyword Density
- Each major JD keyword: appear 2–3 times across the resume
- Pattern: once in summary → once in skills → once in experience
- If it reads awkwardly, one appearance is fine — don't stuff

### What to Extract from JDs
Prioritize in order:
1. Named tools and technologies (Selenium, Playwright, Docker, JMeter…)
2. Methodologies (Agile, CI/CD, SAFe, TDD…)
3. Domain terms (FinTech, RAG, microservices, agentic AI…)
4. Testing types explicitly listed (UAT, regression, performance, API…)
5. Soft skills only if they appear multiple times in the JD

---

## Clarifying Questions

Ask these upfront if not already clear from context:

1. **Single or batch?** — One tailored resume, or multiple (one per JD)?
2. **JD source** — Pasted text, uploaded file, or spreadsheet tracker?
3. **Output preference** — Separate files per JD, or all in one document?
4. **Seniority adjustment?** — Should job titles be upgraded to match target role level?
5. **Sections to include/exclude?** — e.g., skip certifications, add objective statement?

---

## Common Pitfalls

- **Over-tailoring unfamiliar skills**: If a candidate lacks a required skill, omit it rather than claiming "familiarity" — ATS may weight it, but the human reviewer will catch the bluff
- **Replacing strong original bullets**: Tailoring refines, it doesn't replace — preserve compelling quantified achievements even if they don't match the JD perfectly
- **Visual-only formatting**: Tables, columns, and text boxes look great but ATS parsers skip them — always use single-column linear layout for ATS submissions
- **Losing specificity in the summary**: Generic summaries ("experienced professional with X years…") score poorly — the summary must name the role, domain, and 2–3 specific skills from the JD
- **Identical competencies across all resumes**: The competencies section is the easiest win — always reorder and relabel it per JD, even if the underlying skills are the same

---

## References

- See the `docx` skill for advanced Word document formatting patterns
- ATS keyword density research: aim for 2–3% of total words for top skills
- Standard ATS-readable fonts: Calibri, Arial, Garamond, Times New Roman, Helvetica
