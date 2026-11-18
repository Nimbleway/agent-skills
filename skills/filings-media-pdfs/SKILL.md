---
name: filings-media-pdfs
description: Retrieve and parse documents and media for company investment research with Nimble. Use when the task involves a PDF, deck, spreadsheet or media file, such as reading an annual report, 10-K exhibit, investor presentation, earnings release, prospectus, credit agreement, merger agreement, short-seller report, regulator letter, financial supplement (XLSX), or court filing; turning it into markdown; pulling tables out of it; archiving a point-in-time copy; or downloading images, audio or video (webcast replays, product photos) to a file or an S3/GCS bucket. Uses Nimble Extract with file_parsing_options and the Nimble Media API.
metadata:
  author: Nimbleway
  version: 1.10.0
  category: finance-research
---

# Filings, decks, PDFs and media for investment research

Two Nimble capabilities do this work:

| Capability | Endpoint | Returns | Use it to |
| - | - | - | - |
| **Extract + file parsing** | `POST https://sdk.nimbleway.com/v2/extract` with `file_parsing_options` | The document as markdown in `data.markdown` | **Read** a PDF, DOCX, XLSX/XLS/ODS/CSV or PPTX/PPT/ODP: summarize it, quote it, pull tables, diff it against a prior version |
| **Media Download** | `POST https://sdk.nimbleway.com/v2/media` (realtime) or `/v2/media/async` (to your bucket) | The raw file (binary), validated against the MIME types you expect | **Keep** the original file: archive a point-in-time copy, download images, audio or video, or hand a file to another tool |

Rule of thumb: if the next step is reading, parse with Extract. If the next step needs the file itself, download with Media.

Both run through the REST API, the SDKs (`nimble_python`, `@nimble-way/nimble-js`, `nimble-go`) or the `nimble` CLI with `NIMBLE_API_KEY` set. The Nimble MCP server does not expose Media or file-parsing options, so when you only have MCP, use `nimble_extract` for HTML pages and tell the user the CLI or API is needed for parsing documents and downloading media. Never print the API key; let the shell expand `$NIMBLE_API_KEY`.

## 1. Find the right document first

- **Prefer the HTML filing to a PDF.** SEC EDGAR serves 10-Ks, 10-Qs, 8-Ks and proxies as HTML. Extract the HTML filing (plain `nimble_extract` or `/v2/extract` without parsing options) and save parsing for exhibits and documents that only exist as PDFs.
- **Locate PDFs and decks with Search:** `focus: "general"` plus `content_type: ["pdf"]` (or `"presentations"`, `"spreadsheets"`, `"documents"`), `include_domains: [<company IR domain>]`, and a date window. Example query: `"<Company>" investor presentation 2026`.
- **Use the dated copy.** A deck furnished under 8-K Item 7.01 (Ex. 99.x) is the timestamped version of what is on the IR page; cite it when you can.
- **Confirm the entity and the version**: right issuer, right period, latest amendment. File names like `Q3-2026-Earnings-Deck-vF2.pdf` get replaced silently; record the URL and the date you fetched it.
- Common investment documents: annual and sustainability reports, earnings releases and financial supplements (often XLSX), investor day decks, prospectuses (424B), merger agreements and proxies (DEFM14A, S-4 exhibits), credit agreements and indentures (8-K Ex. 10.x and 4.x), rating agency press releases, regulator letters (FDA warning letters, SEC comment letters), court filings and first-day declarations, short-seller reports and company rebuttals, conference presentation slides.

## 2. Parse a document into markdown

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/extract \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "url": "https://investors.example.com/static-files/q3-2026-deck.pdf",
    "formats": ["markdown"],
    "file_parsing_options": {"mode": "light", "max_pages": 80}
  }' | jq -r '.data.markdown' > q3-2026-deck.md
```

Python (plain HTTP, works with any SDK version):

```python
import os, requests
r = requests.post("https://sdk.nimbleway.com/v2/extract",
    headers={"Authorization": f"Bearer {os.environ['NIMBLE_API_KEY']}"},
    json={"url": url, "formats": ["markdown"],
          "file_parsing_options": {"mode": "pro", "max_pages": 150}},
    timeout=300)
r.raise_for_status()
doc = r.json()
markdown, warnings = doc["data"].get("markdown", ""), doc.get("warnings", [])
```

**Choose the mode**

| Mode | Best for | Notes |
| - | - | - |
| `light` (default) | Text-native PDFs with simple layouts: releases, letters, most agreements and prospectuses | Fast and cheapest. No OCR. Tables can come back flat |
| `pro` | Financial tables (income statements, debt schedules, capitalization tables), scanned or image-only PDFs, court filings that are scans | LLM-based parsing with OCR fallback. About $7.50 per 1,000 pages, on top of the base Extract price |

Start with `light` for text. Switch to `pro` when tables come back flattened or pages come back empty. Test one document before a large batch.

**Parameters that matter**

- `formats: ["markdown"]`: returns only the parsed text. Without it, the original file also comes back base64-encoded in `data.html`, which bloats the response.
- `max_pages`: a guard against surprise 600-page filings. A PDF over the limit is rejected before parsing (`400 file exceeds limit`), with no parsing charge. It does not truncate: raise the limit, omit it, or find a shorter document (the exhibit instead of the whole filing). Only PDFs are page-checked.
- Billing is per page parsed, not per document. A parse that fails still returns `200` with a warning and is not billed; check `warnings` and an empty `data.markdown` before trusting the result.
- File type is detected from the content type, URL extension or contents. CSV needs a `.csv` extension or `text/csv` content type.
- `country` routes the fetch through a region when an IR site is geo-restricted.

**What parsing cannot do well:** charts, diagrams and heavily designed slides. For a deck whose numbers live in charts, check the matching earnings release or financial supplement (often XLSX, which parses cleanly) instead of reading values off the chart.

## 3. Work with the parsed text

- **Long filings:** split by headings (`Item 1A. Risk Factors`, `Item 7`, `Note 9 — Debt`) and read only the sections the question needs. Do not paste a whole 10-K into context.
- **Tables:** keep them as markdown tables; carry the units ("in thousands", "in millions") and the period headers with every number you quote.
- **Diffs:** to compare filings (this year's risk factors against last year's), parse both versions in the same mode, align by section heading, and report added, removed and changed sentences with both URLs. The `hf-filing-changes` agent in `company-deep-research` does this end to end.
- **Citations:** cite the document URL, its date, and the section or page heading the value came from. Quote short passages; do not reproduce whole documents.
- **Allegations:** a short report or complaint is a claim, not a fact. Pair each claim with the primary record it relies on.
- **Read the exact words.** Going concern means the filing states substantial doubt exists now, not that auditors "may" express it in future. A merger's outside (end) date and extension terms come from the merger agreement's termination section (8-K Exhibit 2.1), updated by any amendment; cite the section. A debt fair value in the notes is not a market quote.
- **Windows stay windows.** "Expected to close in the second half of 2027" is quoted as written, not converted to a day.

## 4. Download files with Media

**Realtime (raw bytes back in the response):**

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/media \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"url": "https://investors.example.com/q3-2026-deck.pdf",
       "expected_mime_types": ["application/pdf"]}' \
  -D headers.txt --output 2026-11-11_EXMP_q3-2026-deck.pdf
```

The body is the file itself, not JSON. Read the actual type from the `Content-Type` response header. In the SDKs, read the raw response (`nimble.media.with_raw_response.run(...)` in Python, `.asResponse()` in TypeScript). The CLI prints structured output only, so use curl or an SDK for downloads.

**Async (file delivered to your bucket):**

```bash
curl -s -X POST https://sdk.nimbleway.com/v2/media/async \
  -H "Authorization: Bearer $NIMBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/webcast-replay.mp4",
       "expected_mime_types": ["video/mp4"],
       "storage": {"url": "s3://research-archive/exmp/2026-q3/", "type": "s3",
                   "object_name": "exmp_2026q3_webcast_20261111"}}'
```

It returns a `task.id` at once; poll `GET /v2/tasks/{task_id}` until `state` is `success` (or `failed`). The file lands at `storage.url` + `object_name` + its original extension. Bucket permissions must be granted to Nimble first (see the Callbacks & Delivery guide in the Nimble docs). Use async for large files, video, and anything going straight into a data lake.

**Parameters**

- `expected_mime_types`: always set it. The request fails if the server returns something else, which catches the common case of an HTML error or login page served in place of the file. Wildcards work: `["image/*"]`, `["application/pdf"]`, `["audio/*", "video/mp4"]`, `["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]`.
- `country` / `locale`: fetch as if from a region, for geo-restricted IR sites or regional product images.
- `storage.object_name` must be unique. A repeated name overwrites the earlier file. Build names from ticker, document type and date, for example `EXMP_10-K_2026-02-14`.
- Pricing: billed per GB downloaded (about $2.00/GB); failed downloads are not billed.

**Investment uses for Media**

- **Point-in-time archive:** save the exact deck, release or pricing PDF as published, with the fetch date in the name, so the evidence holds up after the company replaces it.
- **Earnings webcast replays and podcasts:** download direct audio or video file links (mp3, mp4) for transcription. Streaming playlists (`.m3u8`) and players behind registration forms are not direct files; record the page URL instead and do not get past registration.
- **Images:** product, packaging and shelf photos from retailer pages, store photos, satellite or site images published by the company, to pair with alt-data tables.
- **Spreadsheets and data supplements:** download the XLSX when you want to load it into pandas yourself rather than read it as markdown.

## 5. Batch work

For tens to hundreds of documents (every 10-K exhibit for a coverage list, every deck from a conference):

1. Build the URL list first (Search, or a Web Search Agent in `dataset_building` mode for "find every investor deck from these 40 companies since 2025").
2. Parse with Extract in parallel at a modest concurrency, set `max_pages`, and write each result to disk named `<ticker>_<doctype>_<date>.md`. Keep a ledger (URL, status, pages, warnings) and retry failures once with `pro`.
3. Archive originals with `/v2/media/async` into the bucket, one unique `object_name` per file.

## 6. Guardrails

- Public documents only. Do not fetch material behind logins, paywalls or registration walls, leaked or "confidential" decks circulating online, or expert-network transcripts: they carry MNPI risk.
- Respect each source's access policy. SEC EDGAR asks for modest request rates (around 10 requests a second at most); keep batch concurrency low there.
- Copyrighted reports (broker research, paid newsletters) are not fair game for redistribution, even when a copy is online.
- Never print or log `NIMBLE_API_KEY`.
