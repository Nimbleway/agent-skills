# Nimble Web - Agent Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Agent Skills](https://img.shields.io/badge/Agent-Skills-blue)](https://agentskills.io)
[![Skills CLI](https://img.shields.io/badge/Skills-CLI-orange)](https://www.npmjs.com/package/skills)
[![Version](https://img.shields.io/badge/version-0.1.0-green)](https://github.com/Nimbleway/agent-skills)

Advanced web search skills powered by Nimble Search API. Built on the open-source [Agent Skills](https://agentskills.io) standard for cross-platform agent compatibility.

Features 8 specialized focus modes (general, coding, news, academic, shopping, social, geo, location) with AI-powered answer generation and smart result filtering.

**Quick Install:**
```bash
npx skills add Nimbleway/agent-skills
```

## About Agent Skills

This skill follows the [Agent Skills](https://agentskills.io) open-source standard, making it compatible with multiple AI agent platforms. Install using the [Skills CLI](https://www.npmjs.com/package/skills) - the standard package manager for the Agent Skills ecosystem.

**Agent Skills Benefits:**
- 🔌 **Cross-Platform** - Works with any agent platform that supports Skills
- 📦 **Easy Installation** - Use the Skills CLI package manager
- 📖 **Open Standard** - Community-driven, vendor-neutral specification
- 🔄 **Reusable** - Write once, use across different agent systems
- 🌐 **Growing Ecosystem** - Part of the thriving Agent Skills community

## Features

### 🔍 **8 Specialized Focus Modes**
- **General** - Broad web searches
- **Coding** - Programming resources, documentation, code examples
- **News** - Current events, recent articles, breaking news
- **Academic** - Research papers, scholarly content
- **Shopping** - Product searches, price comparisons
- **Social** - Social media content, community discussions
- **Geo** - Geographic information, regional data
- **Location** - Local business, place-specific queries

### 🤖 **AI-Powered Features**
- **Answer Generation** - Claude-powered synthesis of search results
- **Smart Filtering** - Domain and date-based result filtering
- **Result Optimization** - Customizable result limits and formats

### 📦 **Components**

**1 Skill**
- `nimble-web-search` - Intelligent web search with 8 focus modes

## Installation

### Prerequisites

**Nimble API Key Required** - Get your key at https://www.nimbleway.com/

Set the `NIMBLE_API_KEY` environment variable using your platform's method:

<details>
<summary><strong>Claude Code</strong></summary>

Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "NIMBLE_API_KEY": "your-api-key-here"
  }
}
```
</details>

<details>
<summary><strong>VS Code / GitHub Copilot</strong></summary>

- Add skills to `.github/skills/` in your repository
- Configure API key using GitHub Actions secrets in the copilot environment
- Or set as environment variable in your shell
</details>

<details>
<summary><strong>Shell / Terminal</strong></summary>

```bash
export NIMBLE_API_KEY="your-api-key-here"
```

Or add to your shell profile (~/.bashrc, ~/.zshrc):
```bash
echo 'export NIMBLE_API_KEY="your-api-key-here"' >> ~/.zshrc
```
</details>

<details>
<summary><strong>Any Platform</strong></summary>

The skill checks for the `NIMBLE_API_KEY` environment variable regardless of how you set it. Use your platform's recommended method for configuring environment variables.
</details>

### Install with Skills CLI

Install using the official [Skills CLI](https://www.npmjs.com/package/skills):

```bash
npx skills add Nimbleway/agent-skills
```

That's it! The skill will be installed and ready to use.

### Alternative: Manual Installation

```bash
# Clone the repository
git clone https://github.com/Nimbleway/agent-skills.git

# Configure your API key in ~/.claude/settings.json
# See Prerequisites section above
```

### Platform-Specific Installation

**Claude Code:**
```bash
cc --plugin-dir /path/to/skills
```

**Other Agent Platforms:**
Most Agent Skills-compatible platforms support the standard Skills directory structure. Refer to your platform's documentation for specific installation instructions.

### Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your API key to `.env`:
   ```bash
   NIMBLE_API_KEY=your-api-key-here
   ```

3. (Optional) Customize defaults in `.env`

## Quick Start

The nimble-web-search skill activates automatically when you ask relevant questions:

```
"Search for recent AI developments"
→ Triggers nimble-web-search skill

"Find information about React Server Components"
→ Triggers nimble-web-search skill

"Look up the latest news on quantum computing"
→ Triggers nimble-web-search skill
```

## API Reference

### Search API

```bash
curl -X POST https://nimble-retriever.webit.live/search \
  -H "Authorization: Bearer $NIMBLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search query",
    "focus": "coding",
    "max_results": 10,
    "include_answer": true
  }'
```

## Skills Documentation

### nimble-web-search

**Trigger phrases:** "search for", "find information about", "look up", "research topic"

**Use when:**
- Need to search the web
- Find current information
- Discover URLs
- Research topics

**Documentation:** See `skills/nimble-web-search/SKILL.md`

## Configuration

### API Configuration

Edit `config/api-config.json` to customize:
- API endpoints
- Focus modes
- Parsing formats
- Rate limits
- Defaults

### Environment Variables

Set in `.env`:
- `NIMBLE_API_KEY` - Your API key (required)
- `NIMBLE_BASE_URL` - Custom endpoint (optional)
- `DEBUG` - Enable debug logging (optional)
- `NIMBLE_DEFAULT_*` - Default settings (optional)

## Focus Mode Guide

| Mode | Best For | Example Queries |
|------|----------|-----------------|
| **general** | Broad searches, overviews | "What is quantum computing" |
| **coding** | Programming, technical docs | "React hooks best practices" |
| **news** | Current events, recent news | "AI developments 2026" |
| **academic** | Research papers, studies | "Machine learning papers" |
| **shopping** | Products, comparisons | "Best laptops for programming" |
| **social** | Community, discussions | "Developer opinions on Rust" |
| **geo** | Geographic, regional | "Climate patterns Pacific" |
| **location** | Local business, places | "Coffee shops Seattle" |

See `skills/nimble-web-search/references/focus-modes.md` for detailed guide.

## Best Practices

### Search Strategy

1. **Start with right focus mode** - Match query type (coding, news, academic, etc.)
2. **Begin with 10 results** - Increase if needed for comprehensive coverage
3. **Use answer generation** - Enable AI synthesis for quick insights
4. **Filter domains** - Target authoritative sources with domain filters
5. **Add date filters** - Get recent content for time-sensitive queries
6. **Iterate and refine** - Adjust focus mode and filters based on results

## Troubleshooting

### Authentication Failed

```
Error: 401 Unauthorized
```

**Solution:**
- Check `NIMBLE_API_KEY` is set correctly
- Verify key is active at nimbleway.com
- Ensure key has API access

### Rate Limit Exceeded

```
Error: 429 Too Many Requests
```

**Solution:**
- Add delays between requests
- Reduce request frequency
- Check your plan limits at nimbleway.com
- Consider upgrading API tier

### No Results Found

**Solutions:**
- Try different focus mode
- Broaden search query
- Remove domain filters
- Adjust date filters
- Check for typos

### Timeout Errors

**Solutions:**
- Reduce max_results
- Simplify query
- Increase timeout in config
- Retry after brief delay

## Examples & References

### Examples Directory

- `skills/nimble-web-search/examples/basic-search.md` - Simple search patterns
- `skills/nimble-web-search/examples/deep-research.md` - Multi-step search workflows
- `skills/nimble-web-search/examples/competitive-analysis.md` - Competitive intelligence patterns

### References Directory

- `skills/nimble-web-search/references/focus-modes.md` - Complete focus mode guide (8 modes)
- `skills/nimble-web-search/references/search-strategies.md` - Advanced search patterns and techniques
- `skills/nimble-web-search/references/api-reference.md` - Full API documentation and examples

## Development

### Running Tests

```bash
# Validate API configuration
./skills/nimble-web-search/scripts/validate-query.sh "test query" general
```

## Roadmap

- [ ] Additional focus modes and search capabilities
- [ ] Advanced filtering and result optimization
- [ ] Result caching layer
- [ ] Integration with more Agent Skills platforms
- [ ] Enhanced cross-platform compatibility
- [ ] Custom search templates
- [ ] Community-contributed search patterns

## Support

- **Documentation**: See `skills/` and `references/` directories
- **API Status**: https://status.nimbleway.com
- **Issues**: https://github.com/Nimbleway/agent-skills/issues
- **Support**: support@nimbleway.com
- **Community**: https://community.nimbleway.com

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the [Agent Skills](https://agentskills.io) open-source standard
- Powered by [Nimble Search API](https://www.nimbleway.com/)
- Compatible with multiple Agent Skills platforms

## Links

- **Agent Skills**: https://agentskills.io - Open standard for AI agent skills
- **Skills CLI**: https://www.npmjs.com/package/skills - Official package manager
- **Nimble Search API**: https://www.nimbleway.com/ - Advanced search API
- **GitHub Repository**: https://github.com/Nimbleway/agent-skills - Source code
- **API Documentation**: https://docs.nimbleway.com/nimble-sdk/search-api - API reference

---

**Built with ❤️ for the Agent Skills community**
