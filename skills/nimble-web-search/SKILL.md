---
name: nimble-web-search
description: >
  Use Nimble Search API to perform intelligent web searches with 8 specialized focus modes (general, coding, news, academic, shopping, social, geo, location).
  This skill should be used when you need to search the web, find current information, discover URLs, research topics, or gather up-to-date data.

  Example triggers: "search for React Server Components", "find recent news about AI", "look up academic papers on quantum computing",
  "search for coding examples of async patterns", "find shopping results for laptops", "discover social media posts about climate change"
triggers:
  - search for
  - find information about
  - look up
  - research topic
  - web search
  - discover URLs
  - find recent
  - search the web
  - get latest information
version: 0.1.0
---

# Nimble Web Search

Perform intelligent web searches using Nimble Search API with specialized focus modes and AI-powered result synthesis.

## Prerequisites

**Nimble API Key Required** - Get your key at https://www.nimbleway.com/

### Configuration

Set the `NIMBLE_API_KEY` environment variable using your platform's method:

**Claude Code:**
```json
// ~/.claude/settings.json
{
  "env": {
    "NIMBLE_API_KEY": "your-api-key-here"
  }
}
```

**VS Code/GitHub Copilot:**
- Add to `.github/skills/` directory in your repository
- Or use GitHub Actions secrets for the copilot environment

**Shell/Terminal:**
```bash
export NIMBLE_API_KEY="your-api-key-here"
```

**Any Platform:**
The skill checks for the `NIMBLE_API_KEY` environment variable regardless of how you set it.

### API Key Validation

**IMPORTANT: Before making any search request, verify the API key is configured:**

```bash
# Check if API key is set
if [ -z "$NIMBLE_API_KEY" ]; then
  echo "❌ Error: NIMBLE_API_KEY not configured"
  echo ""
  echo "Get your API key: https://www.nimbleway.com/"
  echo ""
  echo "Configure using your platform's method:"
  echo "- Claude Code: Add to ~/.claude/settings.json"
  echo "- GitHub Copilot: Use GitHub Actions secrets"
  echo "- Shell: export NIMBLE_API_KEY=\"your-key\""
  echo ""
  echo "Do NOT fall back to other search tools - guide the user to configure first."
  exit 1
fi
```

## Overview

Nimble Search provides advanced web search capabilities with 8 specialized focus modes optimized for different types of queries. The API can generate LLM-powered answers, extract deep content, discover relevant URLs, and filter results by domain and date.

## Core Capabilities

### Focus Modes

Choose the appropriate focus mode based on your query type:

1. **general** - Default mode for broad web searches
2. **coding** - Technical documentation, code examples, programming resources
3. **news** - Recent news articles, current events, breaking stories
4. **academic** - Research papers, scholarly articles, academic resources
5. **shopping** - Product searches, e-commerce results, price comparisons
6. **social** - Social media posts, discussions, community content
7. **geo** - Location-based searches, geographic information
8. **location** - Local business searches, place-specific queries

### Search Features

**LLM Answer Generation**
- Request AI-generated answers synthesized from search results
- Powered by Claude for high-quality summaries
- Include citations to source URLs
- Best for: Research questions, topic overviews, comparative analysis

**URL Discovery**
- Extract 1-20 most relevant URLs for a query
- Useful for building reading lists and reference collections
- Returns URLs with titles and descriptions
- Best for: Resource gathering, link building, research preparation

**Deep Content Extraction**
- **Default:** `deep_search=false` for fastest response (titles, descriptions, URLs only)
- **Optional:** `deep_search=true` to extract full page content when needed
- Available formats: markdown, plain_text, simplified_html
- Use deep search only for: Detailed content analysis, archiving, comprehensive text extraction

**Domain Filtering**
- Include specific domains (e.g., github.com, stackoverflow.com)
- Exclude domains to remove unwanted sources
- Combine multiple domains for focused searches
- Best for: Targeted research, brand monitoring, competitive analysis

**Time Filtering**
- **Recommended:** Use `time_range` for simple recency filtering (hour, day, week, month, year)
- **Alternative:** Use `start_date`/`end_date` for precise date ranges (YYYY-MM-DD)
- Note: `time_range` and date filters are mutually exclusive
- Best for: News monitoring, recent developments, temporal analysis

## Usage Patterns

### Basic Search

Use when you need simple web search results:

```
Query: "React Server Components tutorial"
Focus: coding
Max Results: 5
Answer: false (just URLs)
```

### Research with AI Summary

Use when you need synthesized information:

```
Query: "impact of AI on software development 2026"
Focus: general
Max Results: 10
Answer: true (generate LLM answer)
Include Content: true (for deeper analysis)
```

### Domain-Specific Search

Use when targeting specific sources:

```
Query: "async await patterns"
Focus: coding
Domains: ["github.com", "stackoverflow.com", "dev.to"]
Max Results: 8
```

### News Monitoring

Use for current events and breaking news:

```
Query: "latest developments in quantum computing"
Focus: news
Time Range: week (last 7 days)
Max Results: 15
Answer: true (summarize recent developments)
```

### Academic Research

Use for scholarly content:

```
Query: "machine learning interpretability methods"
Focus: academic
Max Results: 20
Deep Content: true (full paper abstracts)
Answer: true (synthesize findings)
```

### Shopping Research

Use for product searches and comparisons:

```
Query: "best mechanical keyboards for programming"
Focus: shopping
Max Results: 10
Answer: true (compare options)
```

## Parallel Search Strategies

### When to Use Parallel Searches

Run multiple searches in parallel when:
- **Comparing perspectives**: Search the same topic across different focus modes
- **Multi-faceted research**: Investigate different aspects of a topic simultaneously
- **Competitive analysis**: Search multiple domains or competitors at once
- **Time-sensitive monitoring**: Track multiple topics or keywords concurrently
- **Cross-validation**: Verify information across different source types

### Implementation Methods

**Method 1: xargs for Controlled Parallelism (Recommended)**
```bash
# Define search queries in a file or array
cat queries.txt | xargs -n1 -P3 -I{} curl -X POST \
  -H "Authorization: Bearer $NIMBLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{}", "focus": "general", "max_results": 10}' \
  https://nimble-retriever.webit.live/search
```

**Method 2: Background Processes for Simple Cases**
```bash
# Start multiple searches concurrently
curl [search1] > result1.json &
curl [search2] > result2.json &
curl [search3] > result3.json &

# Wait for all to complete
wait

# Process results
jq '.results' result*.json
```

**Method 3: Native curl --parallel**
```bash
# For multiple endpoints or URL variations
curl --parallel --parallel-max 5 \
  -d @search1.json https://api/search \
  -d @search2.json https://api/search \
  -d @search3.json https://api/search
```

### Best Practices for Parallel Execution

1. **Rate Limiting**: Limit parallel requests to 3-5 to avoid overwhelming the API
   - Use `xargs -P3` to set maximum concurrent requests
   - Check your API tier limits before increasing parallelism

2. **Error Handling**: Capture and handle failures gracefully
   ```bash
   parallel_search() {
     curl [...] || echo "Failed: $1" >> errors.log
   }
   ```

3. **Result Aggregation**: Combine results after all searches complete
   ```bash
   # Wait for all searches
   wait

   # Merge JSON results
   jq -s 'map(.results) | flatten' result*.json > combined.json
   ```

4. **Progress Tracking**: Monitor completion status
   ```bash
   echo "Running 5 parallel searches..."
   # ... parallel execution ...
   wait
   echo "All searches complete"
   ```

### Example: Multi-Perspective Research

```bash
#!/bin/bash
# Research a topic across multiple focus modes simultaneously

QUERY="artificial intelligence code generation"
OUTPUT_DIR="./search_results"
mkdir -p "$OUTPUT_DIR"

# Run searches in parallel across different focus modes
for focus in "general" "coding" "news" "academic"; do
  (
    curl -X POST \
      -H "Authorization: Bearer $NIMBLE_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"query\": \"$QUERY\", \"focus\": \"$focus\", \"max_results\": 10}" \
      https://nimble-retriever.webit.live/search \
      > "$OUTPUT_DIR/${focus}_results.json"
  ) &
done

# Wait for all searches to complete
wait

# Aggregate and analyze results
jq -s '{
  general: .[0].results,
  coding: .[1].results,
  news: .[2].results,
  academic: .[3].results
}' "$OUTPUT_DIR"/*.json > "$OUTPUT_DIR/combined_analysis.json"

echo "✓ Multi-perspective search complete"
```

### Performance Considerations

- **Optimal Parallelism**: 3-5 concurrent requests balances speed and API limits
- **Memory Usage**: Each parallel request consumes memory; monitor for large result sets
- **Network Bandwidth**: Parallel requests can saturate bandwidth on slow connections
- **API Costs**: More parallel requests = faster API quota consumption

### When NOT to Use Parallel Searches

- Single, focused query with one clear answer
- Sequential research where each search informs the next
- API quota is limited or expensive
- Results need to be processed before next search
- Simple URL collection that doesn't require multiple perspectives

## API Integration

### Required Configuration

**Before making any API request, always validate the API key is configured:**

```bash
# Validate API key is set
if [ -z "$NIMBLE_API_KEY" ]; then
  echo "❌ Nimble API key not configured."
  echo "Get your key at https://www.nimbleway.com/"
  echo ""
  echo "Set NIMBLE_API_KEY environment variable using your platform's method."
  exit 1
fi
```

The skill requires the `NIMBLE_API_KEY` environment variable. See [Prerequisites](#prerequisites) for platform-specific setup instructions.

Get your API key at: https://www.nimbleway.com/

### API Endpoint

```
POST https://nimble-retriever.webit.live/search
```

### Request Format

```json
{
  "query": "search query string",
  "focus": "general|coding|news|academic|shopping|social|geo|location",
  "max_results": 10,
  "include_answer": false,
  "deep_search": false,
  "output_format": "markdown|plain_text|simplified_html",
  "include_domains": ["domain1.com", "domain2.com"],
  "exclude_domains": ["domain3.com"],
  "time_range": "hour|day|week|month|year",
  "start_date": "2026-01-01",
  "end_date": "2026-12-31"
}
```

### Response Format

```json
{
  "results": [
    {
      "url": "https://example.com/page",
      "title": "Page Title",
      "description": "Page description",
      "content": "Full page content (if deep_search=true)",
      "published_date": "2026-01-15"
    }
  ],
  "include_answer": "AI-generated summary (if include_answer=true)",
  "urls": ["url1", "url2", "url3"],
  "total_results": 10
}
```

## Best Practices

### Focus Mode Selection

**Use `coding` for:**
- Programming questions
- Technical documentation
- Code examples and tutorials
- API references
- Framework guides

**Use `news` for:**
- Current events
- Breaking stories
- Recent announcements
- Trending topics
- Time-sensitive information

**Use `academic` for:**
- Research papers
- Scholarly articles
- Scientific studies
- Academic journals
- Citations and references

**Use `shopping` for:**
- Product searches
- Price comparisons
- E-commerce research
- Product reviews
- Buying guides

**Use `social` for:**
- Social media monitoring
- Community discussions
- User-generated content
- Trending hashtags
- Public sentiment

**Use `geo` for:**
- Geographic information
- Regional data
- Maps and locations
- Area-specific queries

**Use `location` for:**
- Local business searches
- Place-specific information
- Nearby services
- Regional recommendations

### Result Limits

- **Quick searches**: 5-10 results for fast overview
- **Comprehensive research**: 15-20 results for depth
- **Answer generation**: 10-15 results for balanced synthesis
- **URL collection**: 20 results for comprehensive resource list

### When to Use LLM Answers

✅ **Use LLM answers when:**
- You need a synthesized overview of a topic
- Comparing multiple sources or approaches
- Summarizing recent developments
- Answering specific questions
- Creating research summaries

❌ **Skip LLM answers when:**
- You just need a list of URLs
- Building a reference collection
- Speed is critical
- You want to analyze sources manually
- Original source text is needed

### Content Extraction

**Use deep content extraction when:**
- Performing detailed analysis
- Archiving content
- Need full text for processing
- Building datasets
- Comprehensive research

**Skip content extraction when:**
- Only need summaries
- Speed is important
- Just collecting URLs
- Previewing options

## Error Handling

### Common Issues

**Authentication Failed**
- Verify NIMBLE_API_KEY is set correctly
- Check API key is active at nimbleway.com
- Ensure key has search API access

**Rate Limiting**
- Reduce max_results
- Add delays between requests
- Check your plan limits
- Consider upgrading API tier

**No Results**
- Try different focus mode
- Broaden search query
- Remove domain filters
- Adjust date filters

**Timeout Errors**
- Reduce max_results
- Disable deep content extraction
- Simplify query
- Try again after brief delay

## Performance Tips

1. **Start Simple**: Begin with basic searches, add features as needed
2. **Choose Right Focus**: Proper focus mode dramatically improves relevance
3. **Optimize Result Count**: More results = longer processing time
4. **Domain Filtering**: Pre-filter sources for faster, more relevant results
5. **Batch Queries**: Group related searches to minimize API calls
6. **Cache Results**: Store results locally when appropriate
7. **Progressive Enhancement**: Start with URLs, add content/answers if needed

## Integration Examples

See the `examples/` directory for detailed integration patterns:
- `basic-search.md` - Simple search implementation
- `deep-research.md` - Multi-step research workflow
- `competitive-analysis.md` - Domain-specific research pattern

See `references/` directory for detailed documentation:
- `focus-modes.md` - Complete focus mode guide
- `search-strategies.md` - Advanced search patterns
- `api-reference.md` - Full API documentation

## Validation

Use the validation script to test your API configuration:

```bash
./scripts/validate-query.sh "test query" general
```

This verifies:
- API key is configured
- Endpoint is accessible
- Response format is correct
- Focus mode is supported

