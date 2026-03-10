---
name: nimble-browser-actions-reference
description: |
  Reference for --browser-action flag (Tier 4 extract). Load when data is behind clicks, scrolls, or form submissions.
  Contains: all action types (click, fill, scroll, auto_scroll, wait, wait_for_element, press), parameters, chaining examples.
---

# Browser Actions

Docs: https://docs.nimbleway.com/nimble-sdk/web-tools/extract/features/browser-actions

Programmatic browser control — click, scroll, fill forms, wait for elements. Use when target data is behind user interactions that must happen before extraction.

**Requires `--render`.**

All actions execute sequentially. Global timeout: 240 seconds.

## Table of Contents

- [CLI flag](#cli-flag)
- [Python SDK](#python-sdk)
- [All action types](#all-action-types)
- [Examples](#examples)
- [Tips](#tips)

---

## CLI flag

```bash
--browser-action '[{"type": "...", ...}, {"type": "...", ...}]'
```

Pass a JSON array of action objects.

## Python SDK

```python
from nimble_python import Nimble

nimble = Nimble()
resp = nimble.extract(
    url="https://example.com/product",
    render=True,
    browser_actions=[
        {"type": "click", "selector": ".tab-reviews", "required": False},
        {"type": "wait_for_element", "selector": ".review-list"},
    ],
    format="markdown",
)
print(resp["data"]["markdown"])
```

SDK: pass `browser_actions` as a Python list of dicts. Python booleans (`False`) are used instead of JSON `false`.

---

## All action types

| Type               | Key params                                               | Use for                           |
| ------------------ | -------------------------------------------------------- | --------------------------------- |
| `goto`             | `url`, `timeout`, `wait_until`, `referer`                | Navigate to a different URL       |
| `wait`             | `duration` ("1s", "500ms", "2000ms")                     | Pause between actions             |
| `wait_for_element` | `selector`, `timeout`, `visible`                         | Wait for DOM element to appear    |
| `click`            | `selector` OR `x`/`y`, `delay`, `count`, `scroll`        | Click buttons, tabs, links        |
| `press`            | `key` (Enter, Tab, Escape, Space, ArrowDown…)            | Keyboard interaction              |
| `fill`             | `selector`, `value`, `mode` (type/paste)                 | Type or paste into input field    |
| `scroll`           | `y` (px), `x` (px), `to` (CSS selector)                  | Scroll page or to element         |
| `auto_scroll`      | `max_duration` (s), `idle_timeout` (s), `click_selector` | Infinite scroll / lazy load       |
| `screenshot`       | `full_page`, `format`, `quality`                         | Capture page state for debugging  |
| `get_cookies`      | `domain` (optional filter)                               | Extract browser cookies           |
| `fetch`            | `url`, `method`, `headers`, `body`                       | HTTP request from browser context |

### `required` parameter

Add `"required": false` to any action to make it optional — the action chain continues even if the element is absent. Use for cookie banners, popups, optional UI elements.

---

## Examples

### CLI

```bash
# Click a tab and wait for content
nimble extract --url "https://example.com/product" --render \
  --browser-action '[
    {"type": "click", "selector": ".tab-reviews"},
    {"type": "wait_for_element", "selector": ".review-list"}
  ]'  --format markdown

# Dismiss optional cookie banner, then extract
nimble extract --url "https://example.com" --render \
  --browser-action '[
    {"type": "click", "selector": "#accept-cookies", "required": false},
    {"type": "wait", "duration": "500ms"}
  ]'  --format markdown

# Fill search form and submit
nimble extract --url "https://example.com/search" --render \
  --browser-action '[
    {"type": "fill", "selector": "#search-input", "value": "running shoes", "mode": "type"},
    {"type": "press", "key": "Enter"},
    {"type": "wait_for_element", "selector": ".results"}
  ]'  --format markdown

# Infinite scroll — load all lazy content
nimble extract --url "https://example.com/feed" --render \
  --browser-action '[
    {"type": "auto_scroll", "max_duration": 15, "idle_timeout": 3}
  ]'  --format markdown

# Auto-scroll with "Load More" button
nimble extract --url "https://example.com/products" --render \
  --browser-action '[
    {"type": "auto_scroll", "click_selector": ".load-more-btn", "max_duration": 20, "idle_timeout": 5}
  ]'  --format markdown

# Navigate to a tab URL, then extract
nimble extract --url "https://example.com" --render \
  --browser-action '[
    {"type": "goto", "url": "https://example.com/reviews"},
    {"type": "wait_for_element", "selector": ".review-item"}
  ]'  --format markdown

# Scroll to specific element
nimble extract --url "https://example.com/page" --render \
  --browser-action '[
    {"type": "scroll", "to": ".pricing-section"},
    {"type": "wait", "duration": "1s"}
  ]'  --format markdown

# Select dropdown then wait
nimble extract --url "https://example.com/product" --render \
  --browser-action '[
    {"type": "click", "selector": ".size-dropdown"},
    {"type": "click", "selector": "[data-value=\"XL\"]"},
    {"type": "wait_for_element", "selector": ".price-updated"}
  ]'  --format markdown

# Take screenshot for debugging
nimble extract --url "https://example.com" --render \
  --browser-action '[
    {"type": "screenshot", "full_page": true}
  ]' --format screenshot
```

### Python SDK

```python
# Click a tab and wait for content
resp = nimble.extract(
    url="https://example.com/product",
    render=True,
    browser_actions=[
        {"type": "click", "selector": ".tab-reviews"},
        {"type": "wait_for_element", "selector": ".review-list"},
    ],
    format="markdown",
)

# Fill search form and submit
resp = nimble.extract(
    url="https://example.com/search",
    render=True,
    browser_actions=[
        {"type": "fill", "selector": "#search-input", "value": "running shoes", "mode": "type"},
        {"type": "press", "key": "Enter"},
        {"type": "wait_for_element", "selector": ".results"},
    ],
    format="markdown",
)

# Infinite scroll
resp = nimble.extract(
    url="https://example.com/feed",
    render=True,
    browser_actions=[
        {"type": "auto_scroll", "max_duration": 15, "idle_timeout": 3},
    ],
    format="markdown",
)

# Dismiss optional cookie banner then extract
resp = nimble.extract(
    url="https://example.com",
    render=True,
    browser_actions=[
        {"type": "click", "selector": "#accept-cookies", "required": False},
        {"type": "wait", "duration": "500ms"},
    ],
    format="markdown",
)
```

---

## Tips

- **`required: false`** — always use for cookie banners, popups, optional elements
- **`wait_for_element` over `wait`** — prefer waiting for a specific element to appear rather than a fixed duration
- **`auto_scroll` `idle_timeout: 3-5`** — right setting for most infinite scroll pages
- **`fill` `mode: "paste"`** — faster for large text blocks; `mode: "type"` simulates human typing
- **`click` `scroll: true`** — auto-scrolls element into viewport before clicking
- All actions run within 240s total — budget your timeouts accordingly
