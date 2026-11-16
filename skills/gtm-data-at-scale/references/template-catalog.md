# Extract Template catalog snapshot (GTM relevant)

Snapshot of the public Extract Templates that matter for GTM data, taken 2026-11-12 from `GET /v2/extract/templates` (836 templates in total: 94 maintained by Nimble, the rest community-built or unlabeled). The catalog grows every week, so treat this as a starting map and always confirm with `nimble_extract_templates_list` / `GET /v2/extract/templates` and read the live `input_schema` with `nimble_extract_templates_get` before running.

`nimble` = maintained by Nimble (auto-healing, preferred). `community` = built by users; check a sample before relying on it. `-` = no maintainer listed; treat like community.

## Hiring and job postings

What an account is investing in, new offices, tools named in posts, sales-team growth.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `indeed_serp` | nimble | `keyword`, `location` | The Indeed Job Search SERP agent extracts structured job posting data from Indeed's first search result page: job title, employer and... |
| `linkedin_job_search_community_2026_04_18` | community | `query`, `location` | The LinkedIn Job Search agent extracts structured job listings from LinkedIn's public job board by keyword and location. This agent is... |
| `linkedin_job_posting_community_2026_04_18` | community | `job_id` | The LinkedIn Job Posting agent extracts structured data from individual job listings on LinkedIn, including title, company, location,... |
| `dice_com_company_jobs_community_2026_03_23` | community | `company_name` | The Dice Company Job Listings agent extracts active job postings for any company on Dice, including job title, employer name, and... |
| `dice_com_job_search_community_2026_03_23` | community | `query`, `location` | The Dice Tech Job Search agent extracts structured tech job listings from Dice.com by keyword and location. This agent is ideal for... |
| `dice_com_job_posting_details_community_2026_03_23` | community | `job_id` | The Dice Job Posting Details agent extracts structured data from individual Dice.com tech job listings including title, company, posting... |
| `dice_com_skills_based_search_community_2026_03_23` | community | `skill`, `filters` | The Dice Skills-Based Job Search agent extracts tech job listings filtered by skill and employment type from Dice. Ideal for tracking... |
| `ziprecruiter_search_2026_02_23_8rtda7lg` | community | `page`, `query`, `location` | The ZipRecruiter Search Results Page agent extracts structured data from job search results on ziprecruiter.com. This agent is ideal for... |
| `monster_com_company_profile_community_2026_04_24` | community | `company_slug` | The Monster Company Profile agent extracts structured company data from Monster.com company profiles. Ideal for recruiters, job seekers,... |
| `naukri_job_search_results_community_2026_04_26` | community | `query`, `location` | The Naukri Job Search Results agent extracts structured job listings from Naukri.com search pages. This agent is ideal for job market... |
| `doda_job_search_results_community_2026_03_23` | community | `keyword` | The Doda Job Search Results agent extracts structured job listings from doda.jp search result pages. This agent is ideal for job market... |

## People

Finding who holds a role; confirm on a page that shows the current role.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `ti_linkedin_serp_profiles` | - | `url` | Extracts LinkedIn profile results from a Google search results page filtered to linkedin.com/in profiles. Returns name, professional... |

## Software and company reviews

Product sentiment, competitor weaknesses, switching reasons, employee morale.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `g2_product_profile_community_2026_04_01_2026_03_31_7ye3hvvf` | community | `product_slug` | Extracts comprehensive product profiles from G2 software review pages including name, description, and product URL. Ideal for building... |
| `glassdoor_company_reviews_community_2026_04_03_2026_04_03_btr0ffnl` | community | `employer_id` | Extract employee reviews from Glassdoor company pages. |
| `naukri_company_reviews_community_2026_04_26` | community | `company_slug` | The Naukri Company Reviews agent extracts company profile and employee review data from AmbitionBox (powered by Naukri.com). Captures... |
| `shopify_app_store_search` | community | `query` | Extracts app listings from Shopify App Store search results. For each result card on the first page, captures position, app name,... |
| `bbb_org_biz_profile_community_2026_03_16` | community | `biz_slug`, `city_slug`, `state_abbr`, `biz_category` | The BBB Business Profile agent extracts structured data from BBB.org including rating, accreditation, contact info, categories, and... |
| `bbb_org_customer_reviews_community_2026_03_16` | community | `city`, `state`, `category`, `business_slug` | The BBB Customer Reviews agent extracts customer reviews from BBB.org business pages, including reviewer names, ratings, review text,... |

## Local businesses and footprint

SMB and local lead lists, locations, ratings and review volume.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `google_maps_search` | nimble | `query` | The Google Maps Search agent is designed to help you extract real-time location-based data from Google Maps using a search query and... |
| `google_maps_reviews` | nimble | `place_id` | The Google Maps Reviews agent is designed to help you extract user-generated reviews from Google Maps, including ratings, comments,... |
| `bing_maps_local_listings_community_2026_03_17` | community | `query`, `location` | The Bing Local Business Listings agent extracts local business results from Bing search, including name, URL, description, and ranking.... |
| `bbb_org_business_search_community_2026_03_16` | community | `query`, `location` | The BBB Business Search agent extracts structured business listings from the Better Business Bureau directory, including names,... |

## Social media and creators

Executive, brand and creator activity; community sentiment.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `youtube_channel` | nimble | `account_id` | The YouTube Channel agent extracts structured data from a channel’s main page and profile context. It captures channel metadata such as... |
| `youtube_shorts` | nimble | `account_id` | The YouTube Shorts Video agent extracts structured data from YouTube Shorts videos and their surrounding context. It captures video... |
| `tiktok_account` | nimble | `account_id` | This TikTok Account agent extracts structured profile and media records from individual TikTok account page. It captures account... |
| `tiktok_video_page` | nimble | `video_id`, `account_id` | The TikTok Video Page agent extracts structured data from individual TikTok video pages. This agent is ideal for content monitoring,... |
| `instagram_profile_by_account` | nimble | `profile` | The Instagram Profile Template is an agent designed to extract and structure public profile data from Instagram for one or more account... |
| `instagram_post` | nimble | `post_id` | The Instagram Post template extracts structured data from individual Instagram post pages. This agent is ideal for content monitoring,... |
| `facebook_page` | nimble | `facebook_user_url` | The Facebook Profile Page Pipeline extracts structured data from public Facebook profile/pages given a profile URL. This pipeline is... |
| `facebook_page_intro` | nimble | `username` | Retrieves the visible Intro section data from a specified Facebook profile. |
| `facebook_public_page_info_community_2026_03_24` | community | `page_slug` | The Facebook Public Page Info agent extracts structured data from any public Facebook page including name, followers, and handle. Ideal... |
| `reddit_subreddit_posts_community_2026_05_02` | community | `subreddit_name` | The Reddit Subreddit Posts agent extracts top post listings from any public subreddit via Reddit's public JSON API. This agent is ideal... |
| `reddit_post_comments_community_2026_05_02` | community | `post_id`, `subreddit_name` | The Reddit Post Comments agent extracts structured comment data from any Reddit post using the public JSON API. This agent is ideal for... |
| `quora_question_answers_community_2026_04_28` | community | `question_slug` | The Quora Question Details agent extracts structured data from question pages on quora.com. This agent is ideal for knowledge... |
| `medium_search_2026_02_23_8hry2r7o` | community | `query` | The Medium Search agent extracts structured data from Medium's search results pages based on a given keyword. This agent is ideal for... |

## AI answers and AI search visibility

How assistants describe your brand and competitors to buyers, and which pages they cite.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `chatgpt` | nimble | `prompt` | The Agent takes prompts and sends them to GPT to get answers. |
| `perplexity` | nimble | `prompt` | An LLM extractor, converting prompts to Perplexity generated answers, returning the textual results, alongside sources and links. |
| `gemini` | nimble | `prompt` | An LLM extractor, converting prompts to Gemini generated answers, returning both text and HTML, alongside sources and links. |
| `google_ai` | nimble | `keyword` | The agent submits user queries to Google AI Mode and returns answers enriched with associated source links. |
| `reddit_answers` | nimble | `prompt` | The Reddit Answer agent extracts structured answer data from Reddit-based generated responses, including the full markdown answer with... |

## Search engines and news

Share of search, competitor ads, news monitoring across engines.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `google_search` | nimble | `query` | The Google SERP agent is a pre-configured, ready-to-use scraping agent within the Nimble platform, purpose-built for extracting... |
| `bing_web_search_results_community_2026_03_17` | community | `query` | The Bing Web Search agent extracts organic search results from Bing, including titles, URLs, snippets, and ranking positions for any... |
| `bing_news_search_community_2026_03_17` | community | `query` | The Bing News Search agent extracts news articles from Bing News search results, including headlines, publication dates, content... |
| `duckduckgo_news_search_community_2026_03_23` | community | `query` | The DuckDuckGo News Search agent extracts structured news articles from DuckDuckGo's news search results. This agent is ideal for media... |
| `yahoo_news_search_2026_02_23_igwc3sz4` | community | `query` | The Yahoo News Search agent extracts structured data from news search results on news.search.yahoo.com. This agent is ideal for content... |
| `reuters_section_listing_community_2026_05_02` | community | `section` | The Reuters Section Listing agent extracts article listings from Reuters section and subsection pages. Returns headlines, publication... |
| `ti_google_trends_state_interest` | - | `search_term` | Extracts the 'Interest by subregion' table from a Google Trends Explore page, returning each US state's region name, interest score... |

## Merchants, brands and marketplaces

For sellers to ecommerce brands and retailers: catalog size, ranks, prices, store apps.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `amazon_serp` | nimble | `keyword` | The Amazon Search agent extracts structured data from Amazon's search results pages based on a given keyword. This agent is ideal for... |
| `amazon_pdp` | nimble | `asin` | The Amazon Product Detail Page Agent extracts structured data from individual product pages on Amazon. This agent is ideal for tracking... |
| `amazon_best_sellers` | nimble | `category` | The Amazon Best Sellers agent extracts structured data from Amazon's Best Sellers rankings across categories. This agent is ideal for... |
| `walmart_serp` | nimble | `keyword` | The Walmart SERP (Search Results Page) agent extracts product listings from Walmart search result pages. It's ideal for extracting... |
| `walmart_pdp` | nimble | `product_id` | The Walmart PDP (Product Detail Page) agent extracts structured data from individual product pages on Walmart. This agent is ideal for... |
| `target_serp` | nimble | `keyword` | The Target SERP (Search Engine Results Page) agent extracts structured product data from search results on target.com. This agent... |
| `tiktok_shop_pdp` | nimble | `product_url` | TikTok Shop Product page agent extracts structured data from individual product pages on TikTok Shop. This pipeline is ideal for product... |
| `myshopify_com_collection_listing_community_2026_04_24` | community | `store`, `collection_handle` | The Shopify Collection Listing agent extracts product listings from any Shopify store collection via the products.json API. This agent... |
| `myshopify_com_product_search_community_2026_04_24` | community | `query`, `store` | The Shopify Store Product Search agent extracts product search results from any standard Shopify store using the built-in Predictive... |
| `ebay_seller_profile_community_2026_03_23` | community | `username` | The eBay Seller Profile agent extracts structured public profile data from eBay seller pages, including feedback score, positive... |

## Public records

Public-company accounts: filings and insider activity.

| Template | Managed by | Required params | What it returns |
| - | - | - | - |
| `sec_gov_company_filing_details_community_2026_05_08` | community | `form_type`, `cik_number` | Extracts the complete list of SEC filings submitted by a public company, identified by its CIK number or ticker symbol. Returns filing... |
| `sec_gov_insider_trading_data_community_2026_05_08` | community | `cik_number` | Monitor corporate insider buying and selling activity by extracting Form 4 filings from SEC EDGAR. Given a company CIK number, returns... |

No template yet for a site you need (a vertical directory, an association member list, a conference exhibitor list)? Use a Web Search Agent for a one-off, or generate a template when it will be pulled repeatedly (section 4 of `SKILL.md`).
