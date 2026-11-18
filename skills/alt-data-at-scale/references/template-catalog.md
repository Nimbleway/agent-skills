# Extract Template catalog snapshot (alt-data relevant)

Snapshot of the public Extract Templates that matter for alternative data, taken 2026-11-11 from `GET /v2/extract/templates` (837 templates in total: 95 maintained by Nimble, the rest community-built). The catalog grows every week, so treat this as a starting map and always confirm with `nimble_extract_templates_list` / `GET /v2/extract/templates` and read the live `input_schema` with `nimble_extract_templates_get` before running.

`nimble` = maintained by Nimble (auto-healing, preferred). `community` = built by users; check a sample before relying on it.

## Ecommerce: prices, products, rankings

| Template | Managed by | What it returns |
| - | - | - |
| `aldi_clp` | nimble | Aldi Browse Products agent extracts structured product listings from Aldi's category pages. This agent is idea |
| `aldi_clp_localized` | nimble | Aldi Browse Products agent extracts structured product listings from Aldi's category pages for the store neare |
| `aldi_pdp` | nimble | Aldi Product Detail Page Agent extracts structured data from individual product pages on Aldi. This agent is i |
| `amazon_best_sellers` | nimble | Amazon Best Sellers agent extracts structured data from Amazon's Best Sellers rankings across categories. This |
| `amazon_jp_best_sellers` | nimble | Amazon Best Sellers agent extracts structured data from Amazon's Best Sellers rankings across categories. This |
| `amazon_jp_pdp` | nimble | Amazon Japan Product Detail Page Agent extracts structured data from individual product pages on Amazon. This  |
| `amazon_pdp` | nimble | Amazon Product Detail Page Agent extracts structured data from individual product pages on Amazon. This agent  |
| `amazon_plp` | nimble | Amazon Browse Products agent extracts structured product listings from Amazon’s category pages. This agent is  |
| `amazon_serp` | nimble | Amazon Search agent extracts structured data from Amazon's search results pages based on a given keyword. This |
| `amazon_uk_best_sellers` | nimble | Amazon UK Best Sellers agent extracts structured data from Amazon.co.uk's Best Sellers rankings across categor |
| `amazon_uk_pdp` | nimble | Amazon Japan Product Detail Page Agent extracts structured data from individual product pages on Amazon. This  |
| `asos_pdp` | nimble | agent accepts an ASOS product id and extracts full product information, including product descriptions, prices |
| `asos_serp` | nimble | agent accepts free text search keywords and produces the search results' ASOS products based on relevance. It  |
| `b_and_h_clp` | nimble | B&H Photo Video category listing page — extracts paginated product listings (name, price, sku, mpn, url, produ |
| `b_and_h_serp` | nimble | B&H SERP (Search Engine Results Page) agent extracts structured product data from the search result pages of b |
| `best_buy_pdp` | nimble | Best Buy PDP (Product Detail Page) agent extracts structured information from Best Buy product pages. Ideal fo |
| `bestbuy_serp` | nimble | agent retrieves structured product listings directly from Best Buy search results. By entering a keyword (e.g. |
| `bookshop_serp` | nimble | Bookshop.org SERP agent extracts structured book listing data from search result pages on bookshop.org. This a |
| `cvs_clp` | nimble | CVS Category Landing Page agent extracts structured product listing data from CVS.com category and search resu |
| `ferguson_plp` | nimble | Ferguson SERP (Search Results Page) agent extracts structured data from Fergusons search results pages based o |
| `footlocker_pdp` | nimble | Foot Locker Canada PDP (Product Detail Page) agent extracts detailed structured data from individual product p |
| `footlocker_serp` | nimble | Foot Locker SERP (Search Results Page) agent extracts structured product listing data from search results page |
| `heb_pdp` | nimble | H-E-B Product Detail Page agent extracts structured grocery product data—including product identity, current a |
| `heb_serp` | nimble | H-E-B Search Results agent extracts structured product data from H-E-B search and category listing pages — inc |
| `hm_pdp` | nimble | H&M Product Detail Page agent extracts structured data from individual product pages on H&M. This agent is ide |
| `hm_serp` | nimble | H&M Search Results Page agent extracts structured product listings from H&M search results. This agent is idea |
| `homedepot_serp` | nimble | Home Depot SERP (Search Results Page) agent extracts structured product listing data from search results pages |
| `iga_clp` | nimble | IGA Browse Products agent extracts structured product listings from IGA's category pages. This agent is ideal  |
| `kroger_serp` | nimble | agent retrieves Kroger product search results and returns key details such as item name, price, and sale infor |
| `lowes_pdp` | nimble | Lowes PDP (Product Detail Page) agent extracts detailed structured data from individual product pages on lowes |
| `lowes_serp` | nimble | Lowes SERP (Search Results Page) agent extracts structured data from Lowes search results pages based on a giv |
| `office_depot_pdp` | nimble | Office Depot Product Detail Page agent extracts structured product information from Office Depot’s individual  |
| `office_depot_serp` | nimble | Office Depot Search Results Page agent extracts product listings from Office Depot’s search result pages. Idea |
| `price_chopper_pdp` | nimble | Extracts Price Chopper (shop.pricechopper.com) product pages: name, brand, size, category, description, ingred |
| `price_chopper_serp` | nimble | Extracts Price Chopper (shop.pricechopper.com) search results by keyword: one row per ranked slot with page ra |
| `sams_club_pdp` | nimble | agent accepts a Sam’s Club product ID as input and retrieves the corresponding product page. It extracts clean |
| `sams_club_plp` | nimble | agent accepts a search query and fetches the corresponding Sam’s Club search results page. It extracts structu |
| `shoprite_pdp` | nimble | Extracts ShopRite (shoprite.com) product pages by URL: name, brand, size, shelf price, regular (was) price, un |
| `shoprite_serp` | nimble | Extracts ShopRite (shoprite.com) search results by keyword: one row per ranked slot (sponsored slots included  |
| `slickdeals_pdp` | nimble | SlickDeals Deal Page agent accepts a Slickdeals deal ID an enhanced set of product data to enrich the deal inf |
| `slickdeals_serp` | nimble | SlickDeals Search Results agent takes a product search query returns a structured list of the deals shown on t |
| `sobeys_clp` | nimble | Sobeys Browse Products agent extracts structured product listings from Sobeys's category pages. This agent is  |
| `staples_pdp` | nimble | Staples PDP (Product Detail Page) agent collects structured data from product detail pages on Staples.com. Thi |
| `staples_serp` | nimble | Staples SERP (Search Results Page) agent extracts structured product listing data from search result and categ |
| `target_serp` | nimble | Target SERP (Search Engine Results Page) agent extracts structured product data from search results on target. |
| `tesco_clp` | nimble | Tesco Browse Products agent extracts structured product listings from Tesco's category pages. This agent is id |
| `tesco_pdp` | nimble | Tesco Product Detail Page Agent extracts structured data from individual product pages on Tesco. This agent is |
| `tractorsupply_pdp` | nimble | Tractor Supply Product Detail Page agent extracts structured product data — including name, pricing, brand, ra |
| `walmart_aldi_pdp_localized` | nimble | Aldi Product Detail Page Agent extracts structured data from individual product pages on Aldi. This agent is i |
| `walmart_ca_pdp` | nimble | Walmart Canada Product Detail Page pipeline extracts structured product data from Walmart.ca using a product’s |
| `walmart_ca_serp` | nimble | Walmart Canada Search Results Page Pipeline extracts product listings from Walmart search result pages. It's i |
| `walmart_canada_pdp` | nimble | Walmart Canada Product Detail Page agent extracts structured product data from Walmart.ca using a product’s ID |
| `walmart_clp` | nimble | Extracts product listings from Walmart browse/category pages (up to 10 pages). Outputs product_id and url for  |
| `walmart_pdp` | nimble | Walmart PDP (Product Detail Page) agent extracts structured data from individual product pages on Walmart. Thi |
| `walmart_serp` | nimble | Walmart SERP (Search Results Page) agent extracts product listings from Walmart search result pages. It's idea |
| `zara_product_detail_template_2026_02_24_4nxjf0z1` | nimble | Zara Product Details Page agent extracts structured data from individual product pages on Zara. This agent is  |
| `zara_search_template_2026_03_05_g4gu8tpl` | nimble | Zara Search Results Page agent extracts structured product listings from Zara search results. This agent is id |
| `zoro_serp` | nimble | Zoro SERP pipeline gives you a clear snapshot of products available on Zoro, including the product’s name, bra |
| `bbb_org_biz_profile_community_2026_03_16` | community | BBB Business Profile agent extracts structured data from BBB.org including rating, accreditation, contact info |
| `bbb_org_business_search_community_2026_03_16` | community | BBB Business Search agent extracts structured business listings from the Better Business Bureau directory, inc |
| `bbb_org_scam_tracker_community_2026_03_16` | community | BBB Scam Tracker agent extracts scam report listings from the Better Business Bureau Scam Tracker by keyword s |
| `bestbuy_com_category_listing_community_2026_03_16_2026_03_16_63o2wlgb` | community | Best Buy Category Listing agent extracts structured product data from Best Buy category pages including names, |
| `bestbuy_com_product_search_community_2026_03_16` | community | Best Buy Product Search agent extracts structured product listings from Best Buy search results including name |
| `chewy_category_listing_community_2026_03_23` | community | Chewy Category Listings agent extracts structured product data from Chewy.com browse category pages. This agen |
| `chewy_product_page_community_2026_03_23` | community | Chewy Product Details agent extracts structured data from Chewy product pages including name, price, brand, ra |
| `chewy_product_search_community_2026_03_23` | community | Chewy Product Search Results agent extracts structured product listings from Chewy search results pages includ |
| `ebay_category_browse_community_2026_03_23` | community | eBay Category Browse agent extracts subcategory cards and featured listings from eBay category browse pages. T |
| `ebay_product_listing_community_2026_03_23` | community | eBay Product Listing agent extracts structured data from eBay item pages including title, price, brand, condit |
| `ebay_search_2026_02_23_pbgj8oft` | community | eBay Search agent extracts structured data from product search results on www.ebay.com. This agent is ideal fo |
| `ebay_search_results_community_2026_03_23` | community | eBay Search Results agent extracts product listings from eBay search pages, including titles, prices, images,  |
| `ebay_seller_profile_community_2026_03_23` | community | eBay Seller Profile agent extracts structured public profile data from eBay seller pages, including feedback s |
| `etsy_product_page_community_2026_03_23` | community | Etsy Product Listing agent extracts structured data from Etsy listing pages including title, price, shop name, |
| `etsy_search_results_community_2026_03_24` | community | Etsy Search Results agent extracts structured product listings from Etsy search pages, including titles, price |
| `etsy_shop_page_community_2026_03_23` | community | Etsy Shop Page agent extracts structured data from public Etsy storefronts including shop name, sales count, r |
| `g2_product_profile_community_2026_04_01_2026_03_31_7ye3hvvf` | community | Extracts comprehensive product profiles from G2 software review pages including name, description, and product |
| `kroger_product_details_community_2026_04_20` | community | Kroger Product Details agent extracts structured product information from Kroger grocery store product pages.  |
| `lowes_com_product_page_community_2026_04_18` | community | Lowe's Product Details agent extracts structured data from Lowe's product pages including name, price, brand,  |
| `lowes_com_product_search_community_2026_04_20` | community | Lowe's Product Search agent extracts structured product listings from Lowe's search results, including names,  |
| `realmadrid_player_profile_community_2026_05_02` | community | Real Madrid Player Profile agent extracts structured data from official player pages on realmadrid.com, includ |
| `shopify_app_store_search` | community | Extracts app listings from Shopify App Store search results. For each result card on the first page, captures  |

## Reviews and ratings

| Template | Managed by | What it returns |
| - | - | - |
| `google_maps_reviews` | nimble | Google Maps Reviews agent is designed to help you extract user-generated reviews from Google Maps, including r |
| `airbnb_listing_reviews_community_2026_03_15` | community | Airbnb Listing Details agent extracts structured data from Airbnb property pages including name, price, descri |
| `ajmadison_product_reviews_community_2026_03_15` | community | AJ Madison Product Detail Page agent extracts structured product data including name, price, brand, rating, SK |
| `aliexpress_product_reviews_community_2026_03_15_v2` | community | AliExpress Product Details agent extracts structured data from AliExpress product pages including name, price, |
| `aliexpress_ru_product_reviews_community_2026_05_11` | community | Extracts product details (name, price, brand, rating, SKU, image, description) from AliExpress Russia (aliexpr |
| `amazon_ae_product_reviews_2026_02_25_u4ad2x0p` | community | Amazon UAE Product Reviews agent extracts structured data from customer review pages on amazon.ae. This agent  |
| `amazon_br_product_reviews_2026_02_25_zedat0lo` | community | Amazon Brazil Review Page agent extracts structured data from product review pages on amazon.com.br. This agen |
| `amazon_ca_product_reviews_2026_02_25_mqjexd0x` | community | Amazon Canada Product Reviews agent extracts structured data from product review pages on amazon.ca. This agen |
| `amazon_fr_product_reviews_2026_02_25_t90l0zzs` | community | Amazon France Product Reviews agent extracts structured data from customer review pages for products on amazon |
| `amazon_india_product_reviews_2026_02_25_rwzmqema` | community | Amazon India Review Page agent extracts structured data from customer review pages on amazon.in. This agent is |
| `amazon_mexico_product_reviews_2026_02_25_g5ez5zjn` | community | Amazon Mexico Product Reviews agent extracts structured data from customer review pages on amazon.com.mx. This |
| `amazon_nl_product_reviews_2026_02_25_hddx9m6q` | community | Amazon Netherlands Product Reviews agent extracts structured data from customer review pages for products on a |
| `amazon_sg_product_reviews_2026_02_25_7fk4js9y` | community | Amazon Singapore Review Page agent extracts structured data from product review pages on amazon.sg. This agent |
| `bbb_org_customer_reviews_community_2026_03_16` | community | BBB Customer Reviews agent extracts customer reviews from BBB.org business pages, including reviewer names, ra |
| `bestbuy_com_product_reviews_community_2026_03_17` | community | Best Buy Product Details agent extracts structured product data including name, price, brand, rating, descript |
| `booking_com_property_reviews_community_2026_03_17` | community | Booking.com Hotel Property Reviews agent extracts verified guest reviews including scores, reviewer details, a |
| `boulanger_product_reviews_community_2026_03_17` | community | Boulanger Product Details agent extracts structured data from Boulanger product pages including name, price, b |
| `carparts_com_product_reviews_community_2026_03_17` | community | CarParts.com Auto Parts Product Details agent extracts structured product data from CarParts.com product pages |
| `doordash_store_reviews_community_2026_03_23` | community | DoorDash Store Reviews agent extracts customer reviews and ratings from DoorDash restaurant pages, including r |
| `douglas_de_product_reviews_community_2026_03_23` | community | Douglas agent extracts structured product data from douglas.de product pages including name, price, brand, and |
| `douglas_de_product_reviews_community_2026_03_23_2026_03_23_8jo18cbf` | community | Douglas agent extracts structured product data from douglas.de product pages including name, price, brand, and |
| `dsw_product_reviews_community_2026_03_16` | community | DSW Product Reviews agent extracts customer reviews from DSW shoe products via BazaarVoice. This agent is idea |
| `etsy_product_reviews_community_2026_03_24_2026_03_23_bqzkfi72` | community | Etsy Product Detail Page agent extracts product and review data from Etsy listings. Ideal for ecommerce resear |
| `flipkart_product_reviews_community_2026_03_24` | community | Flipkart Product Reviews agent extracts structured customer review data from any product page, including star  |
| `glassdoor_company_reviews_community_2026_04_03_2026_04_03_btr0ffnl` | community | Extract employee reviews from Glassdoor company pages. |
| `lowes_com_product_reviews_community_2026_04_18` | community | Lowe's Product Reviews agent extracts structured customer review data from Lowe's product pages. This agent is |
| `manomano_fr_product_reviews_community_2026_04_20` | community | ManoMano FR Product Reviews agent extracts structured customer review data from ManoMano.fr product pages. Thi |
| `naukri_company_reviews_community_2026_04_26` | community | Naukri Company Reviews agent extracts company profile and employee review data from AmbitionBox (powered by Na |
| `newegg_product_reviews_community_2026_04_26` | community | Newegg Product Reviews agent extracts customer reviews and ratings from Newegg product pages. Ideal for sentim |
| `nykaa_product_reviews_community_2026_04_27` | community | Nykaa Product Reviews agent extracts customer reviews from Nykaa product pages, including star ratings, review |
| `rakuten_co_jp_product_reviews_community_2026_05_02` | community | Rakuten Product Reviews agent extracts structured customer review data from Rakuten Ichiba product pages, incl |
| `steampowered_com_game_reviews_community_2026_05_14` | community | Extracts user reviews for a specific game, including review text, recommendation (positive/negative), hours pl |

## Jobs and hiring

| Template | Managed by | What it returns |
| - | - | - |
| `indeed_serp` | nimble | Indeed Job Search SERP agent extracts structured job posting data from Indeed's first search result page: job  |
| `dice_com_company_jobs_community_2026_03_23` | community | Dice Company Job Listings agent extracts active job postings for any company on Dice, including job title, emp |
| `dice_com_job_posting_details_community_2026_03_23` | community | Dice Job Posting Details agent extracts structured data from individual Dice.com tech job listings including t |
| `dice_com_job_search_community_2026_03_23` | community | Dice Tech Job Search agent extracts structured tech job listings from Dice.com by keyword and location. This a |
| `doda_job_detail_page_community_2026_03_23` | community | Doda Job Detail Page agent extracts structured data from doda.jp individual job listings. This agent is ideal  |
| `doda_job_search_results_community_2026_03_23` | community | Doda Job Search Results agent extracts structured job listings from doda.jp search result pages. This agent is |
| `linkedin_job_posting_community_2026_04_18` | community | LinkedIn Job Posting agent extracts structured data from individual job listings on LinkedIn, including title, |
| `linkedin_job_search_community_2026_04_18` | community | LinkedIn Job Search agent extracts structured job listings from LinkedIn's public job board by keyword and loc |
| `loblaw_ca_job_listings_community_2026_04_18` | community | Loblaw Job Listing Details agent extracts structured data from individual job postings on careers.loblaw.ca. T |
| `montana_state_job_listings_community_2026_04_24` | community | Montana State Government Jobs agent extracts structured job listings from Montana's official Taleo careers por |
| `naukri_job_detail_page_community_2026_04_26` | community | Extracts detailed information from individual Naukri.com job postings including job title, company, location,  |
| `naukri_job_search_results_community_2026_04_26` | community | Naukri Job Search Results agent extracts structured job listings from Naukri.com search pages. This agent is i |
| `stlouis_mo_gov_job_postings_community_2026_05_14` | community | Extracts current city government job openings including position title, department, salary range, qualificatio |

## Locations and local businesses

| Template | Managed by | What it returns |
| - | - | - |
| `google_maps_search` | nimble | Google Maps Search agent is designed to help you extract real-time location-based data from Google Maps using  |
| `kroger_store_locator_community_2026_04_20` | community | Kroger Store Locator agent extracts nearby store locations from kroger.com based on a ZIP code or city. Return |
| `lowes_com_store_locator_community_2026_04_18` | community | Lowe's Store Locator agent extracts structured location data from Lowe's store pages. This agent is ideal for  |

## Restaurants and delivery

| Template | Managed by | What it returns |
| - | - | - |
| `doordash_pdp` | nimble | agent accepts a doordash store ID and extracts business data, customer reviews and menu items. |
| `uber_eats_pdp` | nimble | agent accepts an UberEats store ID and extracts business data, customer reviews and menu items. |
| `doordash_cuisine_category_browse_community_2026_03_23` | community | Extracts restaurant listings by cuisine type from DoorDash, including names, ratings, prices, and URLs. Ideal  |
| `doordash_restaurant_menu_community_2026_03_23` | community | DoorDash Restaurant Menu agent extracts structured menu items from any DoorDash store page, including names, p |

## Travel, lodging and ticketing

| Template | Managed by | What it returns |
| - | - | - |
| `stubhub_event_get_page` | nimble | agent retrieves listings from a specific page within a StubHub event.  Each page contains 10 listings. Use the |
| `stubhub_get_url` | nimble | Submit an event ID, and get the full event URL. |
| `ticketmaster_events_extractor` | nimble | Ticketmaster Venue Events Agent extracts structured event data from individual venue pages on Ticketmaster. Gi |
| `ticketmaster_offers_details` | nimble | Ticketmaster Offers Details Page Agent extracts structured data from individual event pages on Ticketmaster. T |
| `viagogo_get_event_page` | nimble | agent retrieves listings from a specific page within a Viagogo event. Each page contains 10 listings. Use the  |
| `viagogo_get_url` | nimble | Submit an event ID, and get the full event URL.   |
| `vividseats_json` | nimble | Vividseats Tickets pipeline extracts structured ticketing data for a specific event using its unique event_id. |
| `airbnb_co_in_experience_details_community_2026_03_15` | community | Extracts structured data from Airbnb India experience pages including name, price, rating, and listing URL. Id |
| `airbnb_co_in_listing_details_community_2026_03_15` | community | Airbnb India Listing Details agent extracts structured data from Airbnb India property listing pages including |
| `airbnb_experience_details_community_2026_03_15` | community | Airbnb Experience Details agent extracts structured data from Airbnb experience pages including title, host, c |
| `airbnb_listing_details_community_2026_03_15` | community | Airbnb Listing Details agent extracts structured data from Airbnb property pages including title, price, descr |
| `airbnb_search_results_community_2026_03_15` | community | Airbnb Search Results agent extracts structured property listings from Airbnb search pages for any destination |
| `booking_com_dest_pricing_community_2026_03_17` | community | Booking.com Destination Pricing agent extracts hotel listings from search results including names, prices, rat |
| `booking_com_property_search_community_2026_03_17` | community | Booking.com Property Search agent extracts hotel and accommodation search results including names, prices, rat |

## Real estate

| Template | Managed by | What it returns |
| - | - | - |
| `zillow_pdp` | nimble | Zillow PDP (Property Details Page) agent collects full, structured property data from Zillow’s PDP using a ZPI |
| `zillow_plp` | nimble | Zillow PLP (Property Listings Page) agent collects real-estate listing assets from Zillow’s PLP based on zipco |
| `zillow_serp_region` | nimble | Fetches a Zillow search results page (SERP) for a given region, identified by its Zillow region ID. Results ca |
| `zillow_zipcode_resolver` | nimble | Zillow Zip Code Resolver agent extracts structured region identity, location hierarchy (city, county, state, c |

## Social media and creators

| Template | Managed by | What it returns |
| - | - | - |
| `facebook_page` | nimble | Facebook Profile Page Pipeline extracts structured data from public Facebook profile/pages given a profile URL |
| `facebook_page_intro` | nimble | Retrieves the visible Intro section data from a specified Facebook profile. |
| `facebook_url_resolver` | nimble | Resolves a Facebook URL into structured identity data, extracting the canonical username and the unique Facebo |
| `instagram_audio_page` | nimble | Instagram Audio Page agent extracts structured data from Instagram Reels sound/audio pages. Returns video-leve |
| `instagram_post` | nimble | Instagram Post template extracts structured data from individual Instagram post pages. This agent is ideal for |
| `instagram_profile_by_account` | nimble | Instagram Profile Template is an agent designed to extract and structure public profile data from Instagram fo |
| `moltbook_post` | nimble | agent extracts the Submolt post thread based on Post ID, including latest comments, and first level responses. |
| `moltbook_submolts` | nimble | agent accepts any value, and extracts the currently available Submolts based on what number of pages to extrac |
| `moltbook_submolts_posts` | nimble | agent extracts current posts from Submolt based on Submolt name and sort type (hot, top or new) |
| `tiktok_account` | nimble | TikTok Account agent extracts structured profile and media records from individual TikTok account page. It cap |
| `tiktok_shop_pdp` | nimble | TikTok Shop Product page agent extracts structured data from individual product pages on TikTok Shop. This pip |
| `tiktok_video_page` | nimble | TikTok Video Page agent extracts structured data from individual TikTok video pages. This agent is ideal for c |
| `youtube_channel` | nimble | YouTube Channel agent extracts structured data from a channel’s main page and profile context. It captures cha |
| `youtube_shorts` | nimble | YouTube Shorts Video agent extracts structured data from YouTube Shorts videos and their surrounding context.  |

## LLM answers and AI search visibility

| Template | Managed by | What it returns |
| - | - | - |
| `chatgpt` | nimble | Agent takes prompts and sends them to GPT to get answers.  |
| `gemini` | nimble | An LLM extractor, converting prompts to Gemini generated answers, returning both text and HTML, alongside sour |
| `google_ai` | nimble | agent submits user queries to Google AI Mode and returns answers enriched with associated source links. |
| `google_sge_new` | nimble | Google Search AIO (SGE) Pipeline Template is an advanced scraping pipeline tailored for capturing results from |
| `perplexity` | nimble | An LLM extractor, converting prompts to Perplexity generated answers, returning the textual results, alongside |
| `reddit_answers` | nimble | Reddit Answer agent extracts structured answer data from Reddit-based generated responses, including the full  |

## Search engines and news

| Template | Managed by | What it returns |
| - | - | - |
| `google_search` | nimble | Google SERP agent is a pre-configured, ready-to-use scraping agent within the Nimble platform, purpose-built f |
| `finance_yahoo_com_financial_news_community_2026_03_24_2026_03_23_0ojd1wyn` | community | Yahoo Finance Stock News agent extracts financial news headlines and summaries for any stock ticker symbol. Th |
| `yahoo_news_search_2026_02_23_igwc3sz4` | community | Yahoo News Search agent extracts structured data from news search results on news.search.yahoo.com. This agent |

## Regulators and public records

| Template | Managed by | What it returns |
| - | - | - |
| `clinicaltrials_gov_condition_browse_community_2026_03_23` | community | ClinicalTrials.gov Condition Browse agent extracts filtered clinical trial listings by disease, phase, and rec |
| `clinicaltrials_gov_study_details_community_2026_03_23` | community | ClinicalTrials.gov Study Details agent extracts structured data from individual clinical trial pages including |
| `clinicaltrials_gov_study_results_community_2026_03_23` | community | ClinicalTrials.gov Study Results agent extracts posted clinical trial results including participant flow, outc |
| `clinicaltrials_gov_study_search_community_2026_03_23` | community | ClinicalTrials.gov Study Search agent extracts structured trial data from search result pages. This agent is i |
| `fda_510k_device_search_community_2026_03_24` | community | FDA 510(k) Device Search agent extracts premarket notification records from the FDA database including device  |
| `fda_drug_label_lookup_community_2026_03_25` | community | FDA Drug Label Lookup agent extracts structured drug label data from the openFDA API, including ingredients, d |
| `fda_food_inspection_results_community_2026_03_25` | community | FDA Food Recall Results agent extracts structured recall data from the openFDA food enforcement API. This agen |
| `fda_recall_alerts_community_2026_03_25` | community | FDA Recall Alerts agent extracts product recall and safety alert listings from the openFDA enforcement API, in |

## Markets and finance pages

| Template | Managed by | What it returns |
| - | - | - |
| `finance_yahoo_com_historical_prices_community_2026_03_25` | community | Yahoo Finance Historical Prices agent extracts daily OHLCV data for any stock ticker symbol. This agent is ide |
| `finance_yahoo_com_stock_search_community_2026_03_24` | community | Yahoo Finance Stock Lookup agent extracts structured quote data for stocks, ETFs, and indices by ticker symbol |
| `yahoo_finance_info_2026_02_23_fl3ij8ps` | community | Yahoo Finance Stock Quote agent extracts structured data from stock quote pages on finance.yahoo.com. This age |
