# Source map for company investment research

What hedge fund analysts look for on the public web, where it lives, and how fresh it is. Use it to aim a Nimble Search (`include_domains`, `site:`) or pick the page to Extract.

## Regulatory filings (start here)

| Source | What it tells you | Where | Timing |
| - | - | - | - |
| 8-K | Material events. Item 1.01 material agreements (credit facilities, supply deals, mergers); 1.03 bankruptcy; 2.02 earnings (release as Ex. 99.1); 4.01 auditor change; 4.02 non-reliance / restatement; 5.02 officer and director changes; 7.01 Reg FD (decks as Ex. 99); 8.01 other | sec.gov (EDGAR) | Most items within 4 business days |
| 10-K / 10-Q (20-F, 40-F, 6-K for foreign filers) | Segments, risk factors, MD&A, footnotes (debt, leases, contingencies, customer concentration), wording changes from the prior period | sec.gov; XBRL facts at data.sec.gov | 40 to 90 days after period end |
| DEF 14A / PRE 14A / DFAN14A | Pay, board, related-party transactions, shareholder proposals, proxy fights | sec.gov | Ahead of annual and special meetings |
| Schedule 13D / 13G | Activist stakes and intent (13D Item 4); passive stakes | sec.gov | 13D within 5 business days of crossing 5%, amendments within 2 |
| Forms 3 / 4 / 144 | Insider buys and sells, 10b5-1 plans, planned sales | sec.gov | Form 4 within 2 business days |
| 13F | Institutional holdings, crowding | sec.gov | Up to 45 days after quarter-end |
| S-1 / F-1 / S-3 / 424B | IPOs, follow-ons, shelf takedowns, lockups, use of proceeds, dilution | sec.gov | At filing and pricing |
| DEFM14A / S-4 / SC TO / SC 14D9 | Merger terms, background of the merger, fairness opinions, conditions, fees | sec.gov | Weeks after announcement |
| Credit agreements and indentures | Covenants, baskets, maturities, liens | 8-K Ex. 10.x and Ex. 4.x; 10-Q / 10-K exhibits | Often filed with the next periodic report |
| Non-US filings | Annual reports, exchange announcements | SEDAR+ (Canada), Companies House and RNS (UK), HKEXnews, EDINET (Japan), company IR | Varies by market |

EDGAR full-text search takes keywords, exact phrases in quotes, OR, NOT and form and date filters, not natural language.

## Company-published

- **IR site:** earnings releases, decks, investor days, webcasts, events calendar. Decks furnished under 8-K Item 7.01 give a dated, citable copy.
- **Earnings call transcripts:** not filed with the SEC. Look on the IR page, the webcast, or public transcript pages; some are paywalled (headline only).
- **Corporate site:** product, pricing, locations and careers pages often change before a press release. web.archive.org holds earlier versions for before-and-after comparisons.

## Government and regulator databases

| Area | Sources |
| - | - |
| Healthcare | FDA approvals, PDUFA dates (as disclosed by the company), advisory committee calendars, warning letters, 483s, recalls, 510(k); ClinicalTrials.gov (status, enrollment, endpoint and date changes); EMA |
| Government revenue | USAspending.gov, SAM.gov, FPDS, GAO bid protests, state procurement portals |
| Utilities, telecom, energy, transport | FCC, FERC, state public utility commissions, FAA registry, NHTSA, DOT |
| Consumer and product safety | CPSC, NHTSA recalls, CFPB complaints, FDA food inspections |
| Legal | CourtListener / RECAP (free), PACER (paid summaries), state court portals, ITC, bankruptcy claims-agent sites (Kroll, Stretto, Epiq, Verita) for dockets and claims registers |
| Credit stress | State UCC lien filings; state WARN layoff notices (60 days' notice, uneven coverage) |
| Antitrust and deal approvals | FTC / DOJ (HSR, Second Requests), CFIUS, European Commission, UK CMA, SAMR, state attorneys general |
| IP | USPTO, Google Patents, trademark filings |
| Trade | US ocean import records (bills of lading); air, truck and confidential shipments are missing |
| Corporate registries | State secretaries of state, OpenCorporates, Companies House: new subsidiaries, officers, dissolutions |

## Alternative and channel-check data (secondary signals)

| Signal | What it says | Where | Decay |
| - | - | - | - |
| Prices, promotions, stock availability | Margin and demand pressure | Retailer and brand sites; Nimble Extract Templates (Amazon, Walmart, Target, Best Buy, Home Depot, grocery chains...) | Days |
| Job postings | Hiring velocity, mix by function and region, freezes, new locations | Careers pages and ATS boards (Greenhouse, Lever, Ashby, Workday), Indeed, LinkedIn jobs | Weeks |
| Reviews and ratings | Product quality, churn, customer satisfaction | App stores, Amazon, G2, Trustpilot, BBB, Google Maps, Yelp, delivery apps | Weeks to a quarter |
| Store and location data | Openings, closures, footprint | Store locators, Google Maps | Weeks |
| Web, app and search interest | User growth proxies | App store rank pages, public traffic estimates, search trends | Days to weeks |
| Social and news sentiment | Narrative, controversy, launches | News search, YouTube, TikTok, Reddit (via templates where available) | Hours to days |
| Short-seller reports | Allegations built from public records | Short sellers' sites and the company's rebuttal | Event-driven; verify each claim |

Each source decays at its own speed: pricing and social data matter for days, postings for weeks, 13F for a quarter.

## Query hygiene

- Pair the company name with the ticker, and use `-` to exclude a known namesake.
- Use the issuer's legal name for filings and the brand for consumer pages.
- Date-scope every "latest" or "since" question.
- For regulators and courts, search the entity name the agency uses, which may be the operating subsidiary.
