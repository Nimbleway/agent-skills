#!/usr/bin/env python3
"""Data for this skill's onboarding assets; the renderer is scripts/onboarding_assets.py.

Run after any change to the benchmark numbers or tile copy:
  python3 skills/onboard-your-agent/assets/build.py
The numbers must match references/benchmark.md and the table in ../SKILL.md.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from onboarding_assets import build  # noqa: E402

TITLE = "Deep research task comparison for finance"
CAPTION = "Finance Use-Case Benchmark v2, 40 tasks, November 2026. Higher and further left is better."

# (provider, F1 accuracy + coverage, cost per run in USD). Nimble first = accent.
PROVIDERS = [
    ("Nimble", 0.594, 0.45),
    ("Claude Opus 5.5", 0.583, 0.79),
    ("GPT-6.1 Sol", 0.513, 0.64),
    ("Exa", 0.455, 0.48),
    ("Parallel", 0.418, 0.54),
    ("Firecrawl", 0.388, 0.36),
]

TILES = [
    ("Deep research", "Web Search Agents API",
     "13 hedge fund research agents (deep dive, catalysts, filing changes, red flags, credit, merger arb, channel checks) plus custom agents. Cited answers in about 5 to 15 minutes.",
     "Underwrite Duolingo long on paid subscriber growth."),
    ("Fast search", "Search + Extract APIs",
     "Answers in seconds from filings, IR pages, regulators and news, with dated primary-source citations.",
     "What did NVDA's latest 8-K disclose?"),
    ("Filings, PDFs & media", "Extract file parsing + Media API",
     "Turn 10-K exhibits, decks, credit and merger agreements into markdown; download files and webcasts to disk or S3.",
     "Pull the debt table from this credit agreement."),
    ("Alt data at scale", "Extract Templates + Jobs API",
     "Prices, reviews, jobs and store data from 800+ Extract Templates, run as batches or scheduled jobs into S3 or Databricks.",
     "Track Celsius prices at Walmart and Target daily."),
]

CONFIG = dict(
    TITLE=TITLE, CAPTION=CAPTION, PROVIDERS=PROVIDERS, TILES=TILES,
    X_MAX=0.9, X_STEP=0.15,
    Y_MIN=0.30, Y_MAX=0.65, Y_STEP=0.05,
    Y_LABEL="F1 accuracy + coverage",
    PAGE_TITLE="Nimble for investment research",
    WINDOW_HEIGHT=920,
)

if __name__ == "__main__":
    build(HERE, CONFIG)
