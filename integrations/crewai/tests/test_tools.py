import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from crewai_nimble.tools import NimbleSearchInput, NimbleSearchTool


def _mock_result(
    title: str = "Result Title",
    url: str = "https://example.com",
    description: str = "A snippet",
    content: str = "Full page content",
) -> MagicMock:
    r = MagicMock()
    r.title = title
    r.url = url
    r.description = description
    r.content = content
    return r


def _mock_response(
    results: list | None = None,
    answer: str | None = None,
    total_results: int = 1,
) -> MagicMock:
    resp = MagicMock()
    resp.results = results if results is not None else [_mock_result()]
    resp.total_results = total_results
    resp.answer = answer
    return resp


# --- Input schema ---


class TestNimbleSearchInput:
    def test_defaults(self):
        inp = NimbleSearchInput(query="test")
        assert inp.search_depth == "fast"
        assert inp.focus == "general"
        assert inp.max_results == 10
        assert inp.include_answer is False
        assert inp.output_format == "markdown"
        assert inp.include_domains is None
        assert inp.time_range is None

    def test_all_optional_fields(self):
        inp = NimbleSearchInput(
            query="python asyncio",
            search_depth="deep",
            focus="coding",
            max_results=5,
            include_answer=True,
            output_format="plain_text",
            include_domains=["docs.python.org"],
            exclude_domains=["w3schools.com"],
            time_range="week",
            country="US",
            locale="en",
            max_subagents=3,
        )
        assert inp.search_depth == "deep"
        assert inp.focus == "coding"
        assert inp.max_results == 5
        assert inp.include_domains == ["docs.python.org"]

    def test_max_results_lower_bound(self):
        with pytest.raises(Exception):
            NimbleSearchInput(query="test", max_results=0)

    def test_max_results_upper_bound(self):
        with pytest.raises(Exception):
            NimbleSearchInput(query="test", max_results=101)

    def test_invalid_search_depth(self):
        with pytest.raises(Exception):
            NimbleSearchInput(query="test", search_depth="standard")

    def test_invalid_time_range(self):
        with pytest.raises(Exception):
            NimbleSearchInput(query="test", time_range="quarter")


# --- Tool ---


class TestNimbleSearchTool:
    def setup_method(self):
        self.tool = NimbleSearchTool()
        os.environ["NIMBLE_API_KEY"] = "test-key"

    def teardown_method(self):
        os.environ.pop("NIMBLE_API_KEY", None)

    def test_name(self):
        assert self.tool.name == "Nimble Web Search"

    def test_description_covers_depth_modes(self):
        assert "lite" in self.tool.description
        assert "fast" in self.tool.description
        assert "deep" in self.tool.description

    def test_description_covers_focus_modes(self):
        for mode in ("general", "coding", "news", "academic", "shopping", "social", "geo", "location"):
            assert mode in self.tool.description

    def test_env_vars(self):
        assert len(self.tool.env_vars) == 1
        assert self.tool.env_vars[0].name == "NIMBLE_API_KEY"
        assert self.tool.env_vars[0].required is True

    @patch("crewai_nimble.tools.Nimble")
    def test_run_returns_json(self, mock_cls):
        mock_cls.return_value.search.return_value = _mock_response()
        result = self.tool._run(query="test query")
        data = json.loads(result)
        assert "results" in data
        assert "total_results" in data

    @patch("crewai_nimble.tools.Nimble")
    def test_run_passes_query(self, mock_cls):
        mock_client = mock_cls.return_value
        mock_client.search.return_value = _mock_response()
        self.tool._run(query="nimble search api")
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["query"] == "nimble search api"

    @patch("crewai_nimble.tools.Nimble")
    def test_fast_depth_includes_content(self, mock_cls):
        mock_cls.return_value.search.return_value = _mock_response()
        result = self.tool._run(query="test", search_depth="fast")
        data = json.loads(result)
        assert "content" in data["results"][0]

    @patch("crewai_nimble.tools.Nimble")
    def test_lite_depth_omits_content(self, mock_cls):
        mock_cls.return_value.search.return_value = _mock_response()
        result = self.tool._run(query="test", search_depth="lite")
        data = json.loads(result)
        assert "content" not in data["results"][0]

    @patch("crewai_nimble.tools.Nimble")
    def test_deep_depth_includes_content(self, mock_cls):
        mock_cls.return_value.search.return_value = _mock_response()
        result = self.tool._run(query="test", search_depth="deep")
        data = json.loads(result)
        assert "content" in data["results"][0]

    @patch("crewai_nimble.tools.Nimble")
    def test_content_truncation(self, mock_cls):
        long_content = "x" * 20_000
        mock_cls.return_value.search.return_value = _mock_response(
            results=[_mock_result(content=long_content)]
        )
        result = self.tool._run(query="test", search_depth="deep")
        data = json.loads(result)
        assert data["results"][0]["content"].endswith("... [truncated]")
        assert len(data["results"][0]["content"]) <= self.tool.max_content_chars + len("... [truncated]")

    @patch("crewai_nimble.tools.Nimble")
    def test_answer_included_when_present(self, mock_cls):
        mock_cls.return_value.search.return_value = _mock_response(answer="The answer is 42")
        result = self.tool._run(query="test", include_answer=True)
        data = json.loads(result)
        assert data["answer"] == "The answer is 42"

    @patch("crewai_nimble.tools.Nimble")
    def test_answer_absent_when_none(self, mock_cls):
        mock_cls.return_value.search.return_value = _mock_response(answer=None)
        result = self.tool._run(query="test")
        data = json.loads(result)
        assert "answer" not in data

    @patch("crewai_nimble.tools.Nimble")
    def test_tracking_headers(self, mock_cls):
        mock_cls.return_value.search.return_value = _mock_response()
        self.tool._run(query="test")
        headers = mock_cls.call_args[1]["extra_headers"]
        assert headers["X-Client-Source"] == "crewai-tools"
        assert headers["X-Client-Tool"] == "NimbleSearchTool"
        assert "X-Client-Version" in headers

    @patch("crewai_nimble.tools.Nimble")
    def test_optional_fields_omitted_when_none(self, mock_cls):
        mock_client = mock_cls.return_value
        mock_client.search.return_value = _mock_response()
        self.tool._run(query="test")
        call_kwargs = mock_client.search.call_args[1]
        for field in ("include_domains", "exclude_domains", "time_range", "country", "locale"):
            assert field not in call_kwargs

    @patch("crewai_nimble.tools.Nimble")
    def test_optional_fields_passed_when_set(self, mock_cls):
        mock_client = mock_cls.return_value
        mock_client.search.return_value = _mock_response()
        self.tool._run(
            query="EU AI Act",
            focus="news",
            time_range="week",
            include_domains=["reuters.com"],
            country="DE",
        )
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["time_range"] == "week"
        assert call_kwargs["include_domains"] == ["reuters.com"]
        assert call_kwargs["country"] == "DE"

    def test_missing_nimble_package(self):
        with patch("crewai_nimble.tools.Nimble", None):
            with pytest.raises(ImportError, match="nimble_python"):
                self.tool._run(query="test")

    @pytest.mark.asyncio
    @patch("crewai_nimble.tools.AsyncNimble")
    async def test_arun_returns_json(self, mock_cls):
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        mock_client.search.return_value = _mock_response()
        result = await self.tool._arun(query="async test")
        data = json.loads(result)
        assert "results" in data

    @pytest.mark.asyncio
    async def test_arun_missing_nimble_package(self):
        with patch("crewai_nimble.tools.AsyncNimble", None):
            with pytest.raises(ImportError, match="nimble_python"):
                await self.tool._arun(query="test")
