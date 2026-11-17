#!/usr/bin/env python3
"""Data for this skill's onboarding assets; the renderer is scripts/onboarding_assets.py.

Run after any change to the benchmark numbers or tile copy:
  python3 skills/onboard-your-gtm-agent/assets/build.py
The numbers must match references/benchmark.md and the table in ../SKILL.md.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from onboarding_assets import build  # noqa: E402

TITLE = "Deep research task comparison for GTM"
CAPTION = "GTM Use-Case Benchmark v2, 10 tasks, November 2026. Higher and further left is better."

# (provider, combined accuracy + coverage score, cost per run in USD). Nimble first = accent.
# Firecrawl's average is $0.096; it is plotted at $0.10 like the other price-matched APIs.
PROVIDERS = [
    ("Nimble", 0.497, 0.10),
    ("Claude Opus 5.5", 0.520, 0.28),
    ("GPT-6.1 Sol", 0.448, 0.21),
    ("Exa", 0.405, 0.10),
    ("Parallel", 0.357, 0.10),
    ("Firecrawl", 0.316, 0.10),
]

TILES = [
    ("Account research", "Web Search Agents API",
     "12 GTM agents (meeting prep, buying triggers, decision makers, competitive and brand intel, social) plus custom agents. Cited answers in about 2 to 10 minutes.",
     "Prepare me for a meeting with Gong (gong.io)."),
    ("Fast search", "Search + Extract APIs",
     "Answers in seconds from company sites, newsrooms, careers pages and the press, with dated citations.",
     "Did Clay raise a round this year?"),
    ("Lists & CRM enrichment", "Web Search Agents + Search APIs",
     "Build ICP account lists with near-misses, and fill CRM fields (firmographics, funding, leaders, hiring) with sources and conflicts kept.",
     "Find US legal AI companies, Series A to C, hiring AEs."),
    ("GTM data at scale", "Extract Templates + Jobs API",
     "Job postings, reviews, local business lists, social and AI-answer visibility from 800+ Extract Templates, as batches or scheduled jobs.",
     "Track sales hiring at my top 200 accounts weekly."),
    ("People research", "Search + Web Search Agents APIs",
     "Who holds a role, verified as current, in seconds; people who match an ICP, person briefs, buying committees and job-change checks with agents.",
     "Who is Gong's CRO today, and since when?"),
]

CONFIG = dict(
    TITLE=TITLE, CAPTION=CAPTION, PROVIDERS=PROVIDERS, TILES=TILES,
    X_MAX=0.30, X_STEP=0.05,
    Y_MIN=0.28, Y_MAX=0.56, Y_STEP=0.04,
    Y_LABEL="Accuracy + coverage score",
    PAGE_TITLE="Nimble for GTM research",
    WINDOW_HEIGHT=1090,
    SPAN_LAST_ODD_TILE=True,  # five tiles: the last one spans both columns
)

if __name__ == "__main__":
    build(HERE, CONFIG)
