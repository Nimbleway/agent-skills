from __future__ import annotations

import importlib.metadata
import json
import os
from typing import Any, Literal, Optional, Type

from crewai.tools import BaseTool, EnvVar
from pydantic import BaseModel, Field

try:
    from nimble_python import AsyncNimble, Nimble
except ImportError:
    Nimble = None  # type: ignore[assignment,misc]
    AsyncNimble = None  # type: ignore[assignment,misc]

try:
    _VERSION = importlib.metadata.version("crewai-nimble")
except importlib.metadata.PackageNotFoundError:
    _VERSION = "0.0.0"

_TRACKING_HEADERS = {
    "X-Client-Source": "crewai-tools",
    "X-Client-Tool": "NimbleSearchTool",
    "X-Client-Version": _VERSION,
}


class NimbleSearchInput(BaseModel):
    query: str = Field(description="Search query")
    search_depth: Literal["lite", "fast", "deep"] = Field(
        default="fast",
        description=(
            "Content depth: lite=metadata only (fastest, for URL discovery), "
            "fast=cached rich content (recommended for AI agents), "
            "deep=real-time full content (slowest, for research)"
        ),
    )
    focus: str = Field(
        default="general",
        description=(
            "Focus mode: general, coding, news, academic, shopping, social, geo, location. "
            "Also accepts an array of explicit agent names e.g. ['amazon_serp', 'walmart_serp']."
        ),
    )
    max_results: int = Field(default=10, ge=1, le=100, description="Number of results (1–100)")
    include_answer: bool = Field(
        default=False,
        description="Generate an AI-synthesized answer from results (premium feature)",
    )
    output_format: Literal["plain_text", "markdown", "simplified_html"] = Field(
        default="markdown",
        description="Output format for result content",
    )
    include_domains: Optional[list[str]] = Field(
        default=None,
        description="Restrict results to these domains (max 50)",
    )
    exclude_domains: Optional[list[str]] = Field(
        default=None,
        description="Exclude these domains from results (max 50)",
    )
    time_range: Optional[Literal["hour", "day", "week", "month", "year"]] = Field(
        default=None,
        description="Filter by recency. Cannot combine with start_date/end_date.",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start of date range, YYYY-MM-DD. Cannot combine with time_range.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End of date range, YYYY-MM-DD. Cannot combine with time_range.",
    )
    country: Optional[str] = Field(
        default=None,
        description="ISO Alpha-2 country code for geo-targeted results (e.g. 'US')",
    )
    locale: Optional[str] = Field(
        default=None,
        description="Language code for results (e.g. 'en', 'fr', 'de')",
    )
    max_subagents: Optional[int] = Field(
        default=None,
        description="Parallel subagents for shopping/social/geo/location focus modes (1–5)",
    )


class NimbleSearchTool(BaseTool):
    name: str = "Nimble Web Search"
    description: str = (
        "Search the web for real-time information using Nimble's search API.\n\n"
        "Choose the right search_depth:\n"
        "- lite: Metadata only (title, URL, snippet). Fastest. Best for URL discovery,\n"
        "  quick filtering, high-volume pipelines.\n"
        "- fast (default): Cached rich content. Best for AI agents, RAG, chatbots —\n"
        "  quality content without scrape latency.\n"
        "- deep: Full real-time page content. Slowest. Best for research, due diligence,\n"
        "  tasks requiring complete source material.\n\n"
        "Choose the right focus:\n"
        "- general (default): Broad web search\n"
        "- coding: GitHub, Stack Overflow, official docs\n"
        "- news: Current events — combine with time_range for recency\n"
        "- academic: Research papers and journals\n"
        "- shopping: E-commerce, product comparisons\n"
        "- social: LinkedIn, X, YouTube — best for people research\n"
        "- geo: Geographic/regional data\n"
        "- location: Local businesses and places"
    )
    args_schema: Type[BaseModel] = NimbleSearchInput
    env_vars: list[EnvVar] = [
        EnvVar(
            name="NIMBLE_API_KEY",
            description="Nimble API key — get yours at app.nimbleway.com",
            required=True,
        )
    ]
    max_content_chars: int = 10_000

    def _get_client(self) -> Any:
        if Nimble is None:
            raise ImportError(
                "`nimble_python` not installed. Run: pip install nimble-python"
            )
        return Nimble(
            api_key=os.environ["NIMBLE_API_KEY"],
            extra_headers=_TRACKING_HEADERS,
        )

    def _build_kwargs(self, args: NimbleSearchInput) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "query": args.query,
            "search_depth": args.search_depth,
            "focus": args.focus,
            "max_results": args.max_results,
            "include_answer": args.include_answer,
            "output_format": args.output_format,
        }
        for field in (
            "include_domains",
            "exclude_domains",
            "time_range",
            "start_date",
            "end_date",
            "country",
            "locale",
            "max_subagents",
        ):
            val = getattr(args, field)
            if val is not None:
                kwargs[field] = val
        return kwargs

    def _format_results(self, resp: Any, search_depth: str) -> str:
        results = []
        for r in resp.results:
            entry: dict[str, Any] = {
                "title": r.title,
                "url": r.url,
                "description": r.description,
            }
            if search_depth in ("fast", "deep"):
                content = getattr(r, "content", None) or ""
                if content:
                    if len(content) > self.max_content_chars:
                        content = content[: self.max_content_chars] + "... [truncated]"
                    entry["content"] = content
            results.append(entry)

        output: dict[str, Any] = {
            "total_results": resp.total_results,
            "results": results,
        }
        if getattr(resp, "answer", None):
            output["answer"] = resp.answer
        return json.dumps(output, ensure_ascii=False, indent=2)

    def _run(self, **kwargs: Any) -> str:
        args = NimbleSearchInput(**kwargs)
        client = self._get_client()
        resp = client.search(**self._build_kwargs(args))
        return self._format_results(resp, args.search_depth)

    async def _arun(self, **kwargs: Any) -> str:
        if AsyncNimble is None:
            raise ImportError(
                "`nimble_python` not installed. Run: pip install nimble-python"
            )
        args = NimbleSearchInput(**kwargs)
        client = AsyncNimble(
            api_key=os.environ["NIMBLE_API_KEY"],
            extra_headers=_TRACKING_HEADERS,
        )
        resp = await client.search(**self._build_kwargs(args))
        return self._format_results(resp, args.search_depth)
