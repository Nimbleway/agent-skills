# GitHub SEO Checks

Detailed check rules, severity levels, and scoring logic for the seo-github skill.

---

## Scoring Weights

| Category | Weight | Description |
|----------|--------|-------------|
| README Quality | 30% | Content, structure, and completeness of the README |
| Metadata | 20% | Repository description, topics, license, homepage |
| Community Health | 20% | Community files, activity signals, responsiveness |
| Search Visibility | 15% | Presence in Google and GitHub search results |
| AI Discoverability | 15% | Mention/citation in AI-generated answers |

Each category produces a score from 0-100. The overall score is the weighted
average. Checks within each category are weighted by severity.

**Severity weights for check-level scoring:**

| Severity | Points if Pass | Points Deducted if Fail |
|----------|---------------|------------------------|
| Critical | 25 | -25 |
| High | 15 | -15 |
| Medium | 10 | -10 |
| Low | 5 | -5 |

Category score = max(0, min(100, base_score + sum(check_adjustments))). Base
score starts at 50. Each passing check adds points; each failing check deducts.

---

## Category 1: Metadata Checks

| # | Check | Condition | Severity |
|---|-------|-----------|----------|
| 1.1 | Description present | `description` is not null or empty | Critical |
| 1.2 | Description length | 20-200 characters (1-3 sentences ideal) | Medium |
| 1.3 | Description has keywords | Contains at least one domain keyword | Medium |
| 1.4 | Topics present | `topics` array is not empty | High |
| 1.5 | Topic count | 5-15 topics (fewer = undiscoverable, more = spammy) | Medium |
| 1.6 | Topic coverage | Topics include language, domain, AND use-case terms | High |
| 1.7 | Homepage URL set | `homepage` is not null when docs/website exists | Medium |
| 1.8 | License present | `license` field is not null | High |
| 1.9 | OSS-friendly license | MIT, Apache-2.0, BSD-2/3-Clause, ISC, MPL-2.0 | Low |
| 1.10 | Social preview | Custom image set (not GitHub auto-generated) | Low |
| 1.11 | Not archived | `archived` is false | High |
| 1.12 | Primary language matches topics | Main language appears in topics list | Low |

**Recommendations:**

- 1.1: Add a description that explains what the project does in one clear sentence.
  Include the primary use-case and language/framework.
- 1.2: Keep the description between 20-200 characters. Too short is vague; too long
  gets truncated in search results.
- 1.3: Include at least one keyword that users would search for (e.g., "REST API
  client" not just "a client library").
- 1.4/1.5: Add 5-15 topics via Settings > Topics. Include the primary language
  (e.g., `python`), the domain (e.g., `machine-learning`), and use-case terms
  (e.g., `data-pipeline`, `cli-tool`).
- 1.6: Topics should cover three dimensions: language/framework (`typescript`,
  `react`), domain (`web-scraping`, `nlp`), and use-case (`developer-tools`,
  `automation`). This maximizes discoverability across different search intents.
- 1.7: If the project has a documentation site or homepage, set it in the repo
  settings. This links GitHub to external docs and vice versa.
- 1.8/1.9: Add a LICENSE file. MIT and Apache-2.0 are the most adoption-friendly
  for open source. Repos without a license deter contributors and corporate users.
- 1.10: Create a custom social preview image (1280x640px). This is what appears
  when the repo is shared on social media, Slack, or in link previews. Use the
  project logo, name, and a one-line description.

---

## Category 2: README Checks

| # | Check | Condition | Severity |
|---|-------|-----------|----------|
| 2.1 | H1 present | README starts with or contains an H1 heading | Critical |
| 2.2 | H1 matches repo name | H1 text matches or contains the repo name | High |
| 2.3 | Word count adequate | 300-3000 words (< 300 = too thin, > 3000 = bloated) | Medium |
| 2.4 | Code example early | Code block appears within first 500 words | High |
| 2.5 | Installation section | Section headed "Install", "Installation", "Setup", or "Getting Started" | High |
| 2.6 | Usage section | Section headed "Usage", "Quick Start", "Examples", or "Getting Started" | High |
| 2.7 | Badges present | At least one badge image (CI, version, license, downloads) | Medium |
| 2.8 | Multiple badge types | Badges cover 2+ categories (build status, version, license, coverage) | Low |
| 2.9 | Table of contents | TOC present if word count > 500 | Low |
| 2.10 | Contributing info | "Contributing" section or link to CONTRIBUTING.md | Medium |
| 2.11 | License mention | "License" section or mention of license type | Low |
| 2.12 | Documentation links | Links to docs site, wiki, or API reference if they exist | Medium |
| 2.13 | Heading hierarchy | Headings follow H1 > H2 > H3 without skipping levels | Medium |
| 2.14 | No broken links | Sampled links resolve (check 3-5 key links) | Medium |
| 2.15 | Screenshots/demo | Images or GIFs present (for visual/UI projects only) | Medium |
| 2.16 | No stale content | No obviously outdated version numbers, dates, or deprecated badges | Low |

**Recommendations:**

- 2.1/2.2: Start the README with `# {Repo Name}` followed by a one-line description.
  This is the first thing users and search engines see.
- 2.3: Aim for 500-1500 words for most projects. Very short READMEs signal abandoned
  or trivial projects. Very long READMEs need a table of contents and possibly
  should move detail into separate docs.
- 2.4: Developers evaluate repos by code first. Show a minimal usage example within
  the first screenful. A 3-5 line snippet beats a paragraph of description.
- 2.5: Include a clear installation section with copy-pasteable commands
  (`npm install`, `pip install`, `cargo add`, etc.).
- 2.6: Show how to use the project immediately after installation. "Quick Start"
  sections with runnable examples reduce time-to-value.
- 2.7/2.8: Badges signal project health at a glance. Prioritize: CI status (green
  build), latest version/release, license type, test coverage.
- 2.9: For READMEs over 500 words, add a table of contents. GitHub auto-generates
  one in the rendered view, but an explicit TOC in the markdown helps raw readers.
- 2.10: A "Contributing" section or link to CONTRIBUTING.md signals that the project
  welcomes contributions. Even "PRs welcome" is better than nothing.
- 2.12: If the project has a docs site, wiki, or API reference, link to it
  prominently near the top of the README.
- 2.13: Follow proper heading hierarchy (H1 for title, H2 for sections, H3 for
  subsections). Skipping levels (H1 to H3) hurts readability and SEO.
- 2.15: For CLI tools, UI libraries, or visual projects, include a screenshot or
  demo GIF. Visual evidence dramatically increases engagement.

---

## Category 3: Community Health Checks

| # | Check | Condition | Severity |
|---|-------|-----------|----------|
| 3.1 | Code of conduct | CODE_OF_CONDUCT.md or equivalent present | Medium |
| 3.2 | Contributing guide | CONTRIBUTING.md present | Medium |
| 3.3 | Issue templates | .github/ISSUE_TEMPLATE/ directory or config.yml present | Medium |
| 3.4 | PR template | PULL_REQUEST_TEMPLATE.md present | Low |
| 3.5 | Security policy | SECURITY.md present | Medium |
| 3.6 | License file | LICENSE or LICENSE.md present in root | High |
| 3.7 | Recent activity | Last push within 90 days | High |
| 3.8 | Issue responsiveness | Median first response on recent issues < 7 days | Medium |
| 3.9 | Has releases | At least one GitHub Release exists | Medium |
| 3.10 | CHANGELOG present | CHANGELOG.md or equivalent in root | Low |
| 3.11 | Discussions enabled | `has_discussions` is true (for community projects) | Low |
| 3.12 | Wiki or docs | `has_wiki` or `has_pages` is true, or docs link exists | Low |

**Recommendations:**

- 3.1: Add a CODE_OF_CONDUCT.md. GitHub provides templates (Contributor Covenant is
  the most common). This signals a welcoming project.
- 3.2: Add a CONTRIBUTING.md that explains how to set up the dev environment, run
  tests, and submit PRs. Reduces friction for new contributors.
- 3.3: Add issue templates for bug reports and feature requests. Templates ensure
  reporters provide useful information and reduce triage time.
- 3.5: Add a SECURITY.md with instructions for reporting vulnerabilities. GitHub
  surfaces this prominently in the Security tab.
- 3.7: Repos with no activity for 90+ days appear abandoned. If the project is
  stable (not abandoned), add a note in the README and make periodic maintenance
  commits.
- 3.8: Slow issue response drives contributors away. Aim to acknowledge issues
  within 48 hours, even if a fix takes longer.
- 3.9: GitHub Releases make the project installable and show up in search results.
  Tag releases with semantic versioning.

---

## Category 4: Search Visibility Checks

| # | Check | Condition | Severity |
|---|-------|-----------|----------|
| 4.1 | Branded search presence | Repo appears in top 10 for "{repo-name} github" | High |
| 4.2 | Site-scoped search | Repo appears in top 10 for "site:github.com {name}" | High |
| 4.3 | Category search | Repo appears in top 20 for "{keyword} {language} library" | Medium |
| 4.4 | Best-of search | Repo appears in top 20 for "best {category} tool" | Medium |
| 4.5 | Topics match queries | GitHub topics overlap with search queries tested | Medium |

**Scoring:**

- Found in position 1-3: full points
- Found in position 4-10: 70% points
- Found in position 11-20: 40% points
- Not found in top 20: 0 points

**Recommendations:**

- 4.1/4.2: If the repo does not appear for its own name, the description and README
  likely lack the repo name as a keyword. Ensure the repo name appears in the
  description, H1, and first paragraph of the README.
- 4.3/4.4: Category visibility comes from topics, description keywords, README
  content, and external links. Add category-relevant topics and mention the
  category clearly in the README introduction.
- 4.5: Topics are the primary driver of GitHub Explore and GitHub search ranking.
  Align topics with the queries users actually search for.

---

## Category 5: AI Discoverability Checks

| # | Check | Condition | Severity |
|---|-------|-----------|----------|
| 5.1 | Named mention | Repo is mentioned by name in an AI answer | High |
| 5.2 | URL citation | Repo's GitHub or docs URL appears in AI source citations | High |
| 5.3 | Category recommendation | Repo appears in "best {category}" AI answers | Medium |
| 5.4 | Competitor displacement | Competitors appear in AI answers where repo does not | Medium |

**Scoring:**

- Mentioned AND cited: full points
- Mentioned but not cited: 60% points
- Not mentioned, but cited in sources: 40% points
- Not mentioned, competitor mentioned instead: 0 points (flag as gap)
- No AI answer triggered: exclude from scoring (neutral)

**Recommendations:**

- 5.1/5.2: AI models recommend repos they have seen frequently in training data,
  Stack Overflow answers, blog posts, and documentation. Increase mentions by:
  writing blog posts about the project, answering Stack Overflow questions that
  reference it, getting listed in awesome-lists, and publishing on relevant
  aggregators (Hacker News, Reddit, Dev.to).
- 5.3: For "best of" queries, ensure the README clearly states the category the
  project belongs to and its differentiators. AI models extract this positioning
  from README content.
- 5.4: If competitors appear but the repo does not, analyze what content those
  competitors have that the repo lacks (blog posts, tutorials, Stack Overflow
  presence, awesome-list inclusions).

---

## Grade Thresholds

| Grade | Score | Interpretation |
|-------|-------|----------------|
| **A** | 90-100 | Excellent discoverability. The repo follows all best practices. |
| **B** | 75-89 | Good. Minor gaps that are easy to fix. |
| **C** | 60-74 | Fair. Meaningful issues affecting discoverability. |
| **D** | 40-59 | Poor. Significant gaps limiting visibility and adoption. |
| **F** | 0-39 | Critical. The repo is nearly invisible in search and AI. |
