# Source map for GTM research

What sellers, SDRs, RevOps and marketers look for on the public web, where it lives, and how fresh it is. Use it to aim a Nimble Search (`include_domains`, `site:`) or pick the page to Extract.

## The account's own pages (start here)

| Page | What it tells you | Where | Freshness |
| - | - | - | - |
| Homepage, about, product pages | What they sell, to whom, in their own words; positioning changes | `<domain>`, `<domain>/about`, `/product`, `/solutions` | Changes with launches and rebrands |
| Newsroom and blog | Funding, launches, partnerships, executive hires, customer wins, events | `<domain>/news`, `/press`, `/blog`, `/newsroom` | Days |
| Leadership or team page | Who holds which role | `<domain>/about`, `/team`, `/leadership` | Often lags real changes by weeks or months |
| Careers page and ATS board | Open roles by function and location (what they are investing in), tools named in job posts (tech stack), new offices | `<domain>/careers`; Greenhouse, Ashby, Lever, Workable, Gem, Workday boards | Days to weeks; closed posts disappear |
| Pricing page | Plans, prices, free tier, packaging changes | `<domain>/pricing`; web.archive.org for earlier versions | Changes without announcement |
| Docs, changelog, release notes | What shipped and when | `docs.<domain>`, `/changelog`, `/releases` | Days |
| Customers page and case studies | Named customers, use cases, vertical focus | `<domain>/customers`, `/case-studies` | Months |
| Integrations and partner directory | Partners and the stack they plug into | `<domain>/integrations`, marketplaces (Salesforce AppExchange, HubSpot, Shopify, AWS Marketplace) | Months |
| Trust, security and status pages | Certifications, subprocessors, incidents | `<domain>/security`, `trust.<domain>`, `status.<domain>` | Weeks |
| Events and webinars | What they are pushing, where they will be | `<domain>/events`, `/webinars` | Weeks |

## Official records

| Area | Sources |
| - | - |
| Public companies | SEC EDGAR (10-K and 10-Q for strategy, risks and segments; 8-K Item 5.02 for executive changes; earnings releases as Ex. 99.1); investor relations pages, earnings call webcasts; foreign regulators (SEDAR+, Companies House, RNS) |
| Company registries | State secretaries of state, Companies House (UK officers and filings), OpenCorporates: legal name, incorporation, officers, new subsidiaries |
| Government buyers | USAspending.gov, SAM.gov, state and city procurement portals: awards, contract vehicles, renewals |
| Layoffs | State WARN notices (60 days' notice, uneven coverage) |
| Legal | CourtListener / RECAP, state court portals |
| Local businesses | State licensing boards (contractors, healthcare, salons), health inspection databases |

## Press and third parties

| Source | What it tells you | Watch for |
| - | - | - |
| Press wires (PR Newswire, Business Wire, GlobeNewswire) | Dated company announcements | The company's own words; still first-party claims |
| Business and tech press (TechCrunch, Bloomberg, Reuters, The Information headlines, trade press) | Funding, M&A, leadership, independent context | Paywalled stories: headline only |
| Investor portfolio pages and announcements | Funding and lead investors | Old rounds still listed as "latest" |
| Aggregators (Crunchbase, PitchBook, Tracxn, CB Insights) | Discovery, rough firmographics | Stale headcount and funding totals |
| Review sites (G2, Capterra, TrustRadius, Trustpilot, Google Maps, Yelp) | Product sentiment, switching reasons, competitors named by reviewers | Small samples, incentivized reviews |
| Employee reviews (Glassdoor, Indeed company pages) | Morale, layoffs, reorganizations | Self-selected and noisy |
| Conference sites | Sponsors, exhibitors, speakers (warm-intro and event targeting) | Last year's lists still indexed |
| Podcasts, webinars, talks | What an executive says they care about, in their words | Date of the talk, not the upload |
| Social (LinkedIn, X, Reddit, YouTube, TikTok) | Executive posts, launches, community sentiment | Login walls; verify claims on a first-party page |
| AI assistants (ChatGPT, Perplexity, Google AI Mode, Gemini) | How a brand and its competitors are described to buyers; which sources get cited | Answers vary by prompt, country and day: sample several prompts |

## Signal decay

| Signal | What it says | Decay |
| - | - | - |
| Funding round | Budget and growth targets; new hires follow | Strongest in the first 90 days |
| New executive (sales, marketing, RevOps, data, security) | New priorities and a vendor review; first 100 days | Weeks to a quarter |
| Hiring push in one function | Investment in that area; tools named in posts | Weeks |
| Product launch or new market | New needs and messaging | Weeks |
| Acquisition (either side) | Stack consolidation, integration projects | A quarter or two |
| Layoffs or reorganization | Budget cuts, but also consolidation projects | Weeks |
| Pricing change | Packaging and monetization pressure | Weeks |
| Review and sentiment shift | Churn risk or competitor weakness | A quarter |

## Query hygiene

- Pair the company name with its domain, and use `-` to exclude a known namesake.
- Use the brand for product and review pages, and the legal name for registries and filings.
- Date-scope every "latest", "new" or "since" question.
- For people, pair name with company and title; confirm on a page that shows the current role.
