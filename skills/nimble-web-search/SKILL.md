---
name: nimble-web-search
description: >
  Real-time web intelligence powered by Nimble Search API. Perform intelligent web searches with 8 specialized focus modes (general, coding, news, academic, shopping, social, geo, location).
  This skill provides real-time search results when you need to search the web, find current information, discover URLs, research topics, or gather up-to-date data.

  Example triggers: "search for React Server Components", "find recent news about AI", "look up academic papers on quantum computing",
  "search for coding examples of async patterns", "find shopping results for laptops", "discover social media posts about climate change"
triggers:
  - search for
  - find information about
  - look up
  - research topic
  - web search
  - real-time search
  - discover URLs
  - find recent
  - search the web
  - get latest information
  - real-time data
version: 0.1.0
---

# Nimble Web Search

Real-time web intelligence using Nimble Search API with specialized focus modes and AI-powered result synthesis.

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

Nimble Search provides real-time web intelligence with 8 specialized focus modes optimized for different types of queries. Get instant access to current web data with AI-powered answer generation, deep content extraction, URL discovery, and smart filtering by domain and date.

**Recommended Defaults:**
- `focus`: `"general"` - Broad web search (change to specific mode for targeted results)
- `deep_search`: `false` - Fast response with titles/descriptions (set `true` only when full content needed)
- `max_results`: `10` - Balanced speed and coverage

### Quick Start

Use the wrapper script for the simplest experience:

```bash
./scripts/search.sh '{"query": "React hooks"}'
```

The script automatically handles authentication, tracking headers, and output formatting. Focus defaults to "general", add `"focus": "coding"` for technical results.

## Core Capabilities

### Focus Modes

Choose the appropriate focus mode based on your query type:

1. **general** - Default mode for broad web searches
2. **coding** - Real-time access to technical documentation, code examples, programming resources
3. **news** - Real-time news articles, current events, breaking stories
4. **academic** - Research papers, scholarly articles, academic resources
5. **shopping** - Real-time product searches, e-commerce results, price comparisons
6. **social** - Real-time social media posts, discussions, trending community content
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
- **Default (Recommended):** `deep_search=false` - Fastest response, returns titles, descriptions, and URLs
- **Optional:** `deep_search=true` - Slower, extracts full page content
- **Important:** Most use cases work perfectly with `deep_search=false` (the default)
- Available formats when deep_search=true: markdown, plain_text, simplified_html
- Only enable deep search for: Detailed content analysis, archiving, or comprehensive text extraction needs

**Domain Filtering**
- Include specific domains (e.g., github.com, stackoverflow.com)
- Exclude domains to remove unwanted sources
- Combine multiple domains for focused searches
- Best for: Targeted research, brand monitoring, competitive analysis

**Time Filtering**
- **Recommended:** Use `time_range` for real-time recency filtering (hour, day, week, month, year)
- **Alternative:** Use `start_date`/`end_date` for precise date ranges (YYYY-MM-DD)
- Note: `time_range` and date filters are mutually exclusive
- Best for: Real-time news monitoring, recent developments, temporal analysis

## Usage Patterns

All examples below use the `./scripts/search.sh` wrapper for simplicity. For raw API usage, see the [API Integration](#api-integration) section.

### Basic Search

Simplest search with just a query (uses defaults: focus=general, deep_search=false):

```bash
./scripts/search.sh '{"query": "React Server Components tutorial"}'
```

For technical content, specify coding focus:

```bash
./scripts/search.sh '{
  "query": "React Server Components tutorial",
  "focus": "coding"
}'
```

### Research with AI Summary

Get synthesized insights from multiple sources:

```bash
./scripts/search.sh '{
  "query": "impact of AI on software development 2026",
  "include_answer": true
}'
```

### Domain-Specific Search

Target specific authoritative sources:

```bash
./scripts/search.sh '{
  "query": "async await patterns",
  "focus": "coding",
  "include_domains": ["github.com", "stackoverflow.com", "dev.to"],
  "max_results": 8
}'
```

### Real-Time News Monitoring

Track current events and breaking news as they happen:

```bash
./scripts/search.sh '{
  "query": "latest developments in quantum computing",
  "focus": "news",
  "time_range": "week",
  "max_results": 15,
  "include_answer": true
}'
```

### Academic Research

Find and synthesize scholarly content (note: deep_search rarely needed):

```bash
./scripts/search.sh '{
  "query": "machine learning interpretability methods",
  "focus": "academic",
  "max_results": 20,
  "include_answer": true
}'
```

Only add `"deep_search": true` if you need full paper content extracted.

### Real-Time Shopping Research

Compare products and current prices:

```bash
./scripts/search.sh '{
  "query": "best mechanical keyboards for programming",
  "focus": "shopping",
  "max_results": 10,
  "include_answer": true
}'
```

## Parallel Search Strategies

### When to Use Parallel Searches

Run multiple real-time searches in parallel when:
- **Comparing perspectives**: Search the same topic across different focus modes
- **Multi-faceted research**: Investigate different aspects of a topic simultaneously
- **Competitive analysis**: Search multiple domains or competitors at once
- **Real-time monitoring**: Track multiple topics or keywords concurrently
- **Cross-validation**: Verify information across different source types in real-time

### Implementation Methods

**Method 1: Background Processes (Recommended)**

Run multiple searches concurrently using the wrapper script:

```bash
# Start multiple searches in parallel
./scripts/search.sh '{"query": "React", "focus": "coding"}' > react_coding.json &
./scripts/search.sh '{"query": "React", "focus": "news"}' > react_news.json &
./scripts/search.sh '{"query": "React", "focus": "academic"}' > react_academic.json &

# Wait for all to complete
wait

# Combine results
jq -s '.' react_*.json > combined_results.json
```

**Method 2: Loop with xargs (Controlled Parallelism)**

Process multiple queries with rate limiting:

```bash
# Create queries file
cat > queries.txt <<EOF
{"query": "AI frameworks", "focus": "coding"}
{"query": "AI regulation", "focus": "news"}
{"query": "AI research", "focus": "academic"}
EOF

# Run with max 3 parallel processes
cat queries.txt | xargs -n1 -P3 -I{} ./scripts/search.sh '{}'
```

**Method 3: Focus Mode Comparison**

Search the same query across different focus modes:

```bash
QUERY="artificial intelligence trends"

for focus in "general" "coding" "news" "academic"; do
  (
    ./scripts/search.sh "{\"query\": \"$QUERY\", \"focus\": \"$focus\"}" \
      > "${focus}_results.json"
  ) &
done

wait
echo "All searches complete!"
```

### Best Practices for Parallel Execution

1. **Rate Limiting**: Limit parallel requests to 3-5 to avoid overwhelming the API
   - Use `xargs -P3` to set maximum concurrent requests
   - Check your API tier limits before increasing parallelism

2. **Error Handling**: Capture and handle failures gracefully
   ```bash
   ./scripts/search.sh '{"query": "test"}' || echo "Search failed" >> errors.log
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

   for i in {1..5}; do
     ./scripts/search.sh "{\"query\": \"query$i\"}" > "result$i.json" &
   done

   wait
   echo "All searches complete!"
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
    ./scripts/search.sh "{
      \"query\": \"$QUERY\",
      \"focus\": \"$focus\",
      \"max_results\": 10
    }" > "$OUTPUT_DIR/${focus}_results.json"
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

**Note:** For most use cases, use the `./scripts/search.sh` wrapper script shown in [Usage Patterns](#usage-patterns). The raw API examples below are for advanced users who need direct API access or custom integration.

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
  "query": "search query string",  // REQUIRED
  "focus": "general",  // OPTIONAL: default "general" | coding|news|academic|shopping|social|geo|location
  "max_results": 10,  // OPTIONAL: default 10 (range: 1-100)
  "include_answer": false,  // OPTIONAL: default false
  "deep_search": false,  // OPTIONAL: default false (RECOMMENDED: keep false for speed)
  "output_format": "markdown",  // OPTIONAL: default "markdown" | plain_text|simplified_html
  "include_domains": ["domain1.com"],  // OPTIONAL: default [] (no filter)
  "exclude_domains": ["domain3.com"],  // OPTIONAL: default [] (no filter)
  "time_range": "week",  // OPTIONAL: hour|day|week|month|year
  "start_date": "2026-01-01",  // OPTIONAL: Use time_range OR start_date/end_date (not both)
  "end_date": "2026-12-31"  // OPTIONAL
}
```

**Key Defaults:**
- `focus`: `"general"` - Change to specific mode for targeted results
- `deep_search`: `false` - Keep false unless you need full page content
- `max_results`: `10` - Balanced speed and coverage

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
- Real-time current events
- Breaking stories as they happen
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
- Real-time social media monitoring
- Live community discussions
- Current user-generated content
- Trending hashtags and topics
- Real-time public sentiment

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

**Default (Recommended): `deep_search=false`**

The default setting works for 95% of use cases:
- ✅ Fastest response times
- ✅ Returns titles, descriptions, URLs
- ✅ Works perfectly with `include_answer=true`
- ✅ Sufficient for research, comparisons, and URL discovery

**Only use `deep_search=true` when you specifically need:**
- Full page content extraction
- Archiving complete articles
- Processing full text for analysis
- Building comprehensive datasets

**Performance impact:**
- `deep_search=false`: ~1-3 seconds
- `deep_search=true`: ~5-15 seconds (significantly slower)

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

1. **Use Defaults**: Keep `deep_search=false` (default) for 5-10x faster responses
2. **Start Simple**: Begin with just `{"query": "..."}` - defaults work great
3. **Choose Right Focus**: Proper focus mode dramatically improves relevance (default: "general")
4. **Optimize Result Count**: Default of 10 results balances speed and coverage
5. **Domain Filtering**: Pre-filter sources for faster, more relevant results
6. **Avoid Deep Search**: Only enable `deep_search=true` when you truly need full content
7. **Batch Queries**: Group related searches to minimize API calls
8. **Cache Results**: Store results locally when appropriate

## Integration Examples

See the `examples/` directory for detailed integration patterns:
- `basic-search.md` - Simple search implementation
- `deep-research.md` - Multi-step research workflow
- `competitive-analysis.md` - Domain-specific research pattern

See `references/` directory for detailed documentation:
- `focus-modes.md` - Complete focus mode guide
- `search-strategies.md` - Advanced search patterns
- `api-reference.md` - Full API documentation

## Scripts

### search.sh - Main Search Wrapper

The recommended way to use the Nimble Search API:

```bash
./scripts/search.sh '{"query": "your search", "focus": "coding"}'
```

**Features:**
- Automatic authentication with `$NIMBLE_API_KEY`
- Platform detection (claude-code, github-copilot, vscode, cli)
- Request tracking headers for analytics
- JSON validation and error handling
- Formatted output with `jq`

**Usage:**
```bash
# Basic search
./scripts/search.sh '{"query": "React hooks"}'

# With all options
./scripts/search.sh '{
  "query": "AI frameworks",
  "focus": "coding",
  "max_results": 15,
  "include_answer": true,
  "include_domains": ["github.com"]
}'
```

### validate-query.sh - API Configuration Test

Test your API configuration and connectivity:

```bash
./scripts/validate-query.sh "test query" general
```

This verifies:
- API key is configured
- Endpoint is accessible
- Response format is correct
- Focus mode is supported

