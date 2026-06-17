# crewai-nimble

Nimble web search tools for [CrewAI](https://crewai.com) agents.

## Installation

```bash
pip install crewai-nimble
```

Set your API key:

```bash
export NIMBLE_API_KEY="your-key"
```

Get a key at [app.nimbleway.com](https://app.nimbleway.com).

## Tools

### `NimbleSearchTool`

Real-time web search with 8 focus modes and 3 depth levels.

```python
from crewai_nimble import NimbleSearchTool

tool = NimbleSearchTool()
```

**search_depth** controls content richness vs. speed:

| Value | Content | Best for |
|-------|---------|----------|
| `lite` | Title, URL, snippet | URL discovery, high-volume pipelines |
| `fast` _(default)_ | Cached rich content | AI agents, RAG, chatbots |
| `deep` | Full real-time page | Research, due diligence |

**focus** targets specific source types:

| Value | Sources | Best for |
|-------|---------|----------|
| `general` _(default)_ | Broad web | Overviews, general questions |
| `coding` | GitHub, Stack Overflow, docs | Code and technical queries |
| `news` | News outlets | Current events — pair with `time_range` |
| `academic` | Journals, papers | Research and citations |
| `shopping` | E-commerce | Products, prices, reviews |
| `social` | LinkedIn, X, YouTube | People research, opinions |
| `geo` | Maps, regional data | Geographic queries |
| `location` | Local directories | Restaurants, shops, services |

## Usage

```python
from crewai import Agent, Task, Crew
from crewai_nimble import NimbleSearchTool

search = NimbleSearchTool()

researcher = Agent(
    role="Research Analyst",
    goal="Find accurate, up-to-date information on any topic",
    backstory="Expert at web research and synthesizing information",
    tools=[search],
)

task = Task(
    description="Research the latest developments in quantum computing",
    expected_output="A summary of recent breakthroughs with sources",
    agent=researcher,
)

crew = Crew(agents=[researcher], tasks=[task])
crew.kickoff()
```

### Advanced parameters

```python
# News search — last week only
search._run(
    query="AI regulation EU",
    focus="news",
    search_depth="fast",
    time_range="week",
)

# Deep research with domain filter
search._run(
    query="transformer attention mechanisms",
    focus="academic",
    search_depth="deep",
    include_domains=["arxiv.org", "semanticscholar.org"],
    max_results=5,
)

# People research
search._run(
    query="Sam Altman OpenAI CEO",
    focus="social",
    search_depth="fast",
    max_subagents=3,
)
```

### Async support

```python
result = await search._arun(query="latest AI news", focus="news", time_range="day")
```

## Requirements

- Python 3.10+
- `NIMBLE_API_KEY` environment variable
