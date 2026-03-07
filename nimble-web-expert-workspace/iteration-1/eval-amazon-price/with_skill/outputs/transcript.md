# Transcript — Amazon Price (with skill)

## Command run

```bash
nimble extract \
  --url "https://www.amazon.com/s?k=AirPods+Pro+2nd+generation" \
  --country US --parse \
  --parser '{
    "type": "schema_list",
    "selector": {"type": "css", "css_selector": "[data-component-type=s-search-result]"},
    "fields": {
      "product_name": {"type": "terminal", "selector": {"type": "css", "css_selector": "h2[aria-label] span"}, "extractor": {"type": "text"}},
      "asin": {"type": "terminal", "extractor": {"type": "attr", "attr": "data-asin"}},
      "price": {"type": "terminal", "selector": {"type": "css", "css_selector": "span.a-price span.a-offscreen"}, "extractor": {"type": "text"}}
    }
  }'
```

## Results

Top results from Amazon search:
- AirPods Pro 3 (new model) | $219.00
- AirPods 4 | $99.00
- **AirPods Pro (2nd Generation) with USB-C | $247.02** ← target result

## Notes

- CLI version installed: 0.4.3
- SKILL.md targets v0.5.0 — flag discrepancy found: `--focus` (v0.5.0) vs `--topic` (v0.4.3), `--max-results` vs `--num-results`
- Extract command syntax unchanged between versions
- Data is live, fetched March 2026
