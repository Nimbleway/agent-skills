# Practitioner Extract

Extract practitioner-level data from healthcare practice websites using Nimble web
crawl and extraction APIs.

## What It Does

Given a list of practice URLs (from Definitive Healthcare, a CRM export, or any
source), this skill:

1. **Maps** each practice site to discover provider/team/doctors pages
2. **Extracts** page content as clean markdown
3. **Parses** structured practitioner data using regex + heuristic patterns
4. **Exports** to Google Sheet + JSON + CSV

## Output Schema

Per practitioner:
- Practice name, URL
- Practitioner name, credentials (MD, DO, OD, FACS, etc.)
- Specialty, subspecialty, title
- Office location, phone, email
- Bio URL, appointment URL, patient portal link
- Extraction confidence score

## Requirements

- Nimble CLI (`npm i -g @nimble-way/nimble-cli`) + `NIMBLE_API_KEY`
- Google Sheets credentials (for Sheet output)
- Python 3.11+ with `uv`

## Quick Start

```
extract practitioners from this sheet: [Google Sheet URL]
crawl these ophthalmology practice sites for doctor data
pull providers from these clinic URLs
```

## Works For Any Vertical

Ophthalmology, dental, dermatology, orthopedics, cardiology, primary care, etc.
The extraction patterns adapt based on specialty keywords and credential types.

## Reference Files

| File | Purpose |
|------|---------|
| `references/page-discovery-patterns.md` | URL patterns for provider pages |
| `references/extraction-template.md` | Python pipeline code template |
