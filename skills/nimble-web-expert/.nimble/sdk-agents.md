Nimble **Web Search Agents (WSA)** are ready-to-use extraction agents for popular websites like Amazon, Google, LinkedIn, and hundreds more. No CSS selectors or scraping expertise required - just provide the agent name and parameters, and get structured data instantly.

## Quick Start

### Example Request

### Example Response

```
{
  "url": "https://www.amazon.com/dp/B08N5WRWNW",
  "task_id": "b1fa7943-cba5-4ec2-a88c-4d2d6799c794",
  "status": "success",
  "data": {
    "html": "...",
    "parsing": {
      "asin": "B08N5WRWNW",
      "product_title": "Apple AirPods Pro (2nd Generation)",
      "brand": "Apple",
      "web_price": 249.0,
      "list_price": 279.0,
      "average_of_reviews": 4.7,
      "number_of_reviews": 125432,
      "availability": true
    }
  },
  "status_code": 200
}
```

## How it works

## Two types of agents

## Parameters

Supported input parameters:

## Usage

Extract product data from Amazon, Walmart, and other retailers:

Get search results from Google, Amazon, and other platforms:

Find businesses and locations:

Get responses from AI platforms like ChatGPT and Perplexity:

Get location-specific pricing and availability:

Run agent extractions asynchronously for batch processing:

## Agent Gallery

Browse pre-built agents **maintained by Nimble** for popular platforms:

[

## Explore Full Gallery

Browse all agents with interactive documentation and live testing



](https://online.nimbleway.com/pipeline-gallery)

### E-commerce

Agent

Platform

Description

`amazon_pdp`

Amazon

Product details, pricing, reviews

`amazon_serp`

Amazon

Search results with products

`walmart_pdp`

Walmart

Product details and pricing

`walmart_search`

Walmart

Search results

`target_pdp`

Target

Product details

`best_buy_pdp`

Best Buy

Product details

### Search Engines

Agent

Platform

Description

`google_search`

Google

Search results with snippets

`google_maps_search`

Google Maps

Business listings and locations

`google_search_aio`

Google

AI Overview results

### LLM Platforms

Agent

Platform

Description

`chatgpt`

ChatGPT

Prompt responses

`perplexity`

Perplexity

Search + AI responses

`gemini`

Google Gemini

Prompt responses

`grok`

Grok

Prompt responses

Agent

Platform

Description

`tiktok_account`

TikTok

Account profiles and videos

`facebook_page`

Facebook

Page information

`youtube_shorts`

YouTube

Short-form videos

## Create Custom Agents

Can’t find an agent for your target website? Create your own using **Agentic Studio** - no coding required.

### Custom agent example

## Response Fields

Field

Type

Description

`url`

string

The URL that was extracted

`task_id`

string

Unique identifier for the request

`status`

string

`success` or `failed`

`data.html`

string

Raw HTML content

`data.parsing`

object

Structured extracted data

`status_code`

number

HTTP status code from target

## Use cases

What you need

Use

Data from popular sites (Amazon, Google, etc.)

**Public Agents** - [browse gallery](/nimble-sdk/agentic/agent-gallery)

Data from sites not in the gallery

**Custom Agents** - [create in Studio](/nimble-sdk/agentic/studio)

Data from specific URLs (expert users)

[**Extract**](/nimble-sdk/web-tools/extract/quickstart) - full control with CSS selectors

Data from entire website

[**Crawl**](/nimble-sdk/web-tools/crawl)

Search web + extract content from results

[**Search**](/nimble-sdk/web-tools/search)

## Next steps