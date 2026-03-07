# Transcript — eval-tier4-amazon-multi (with skill)
## Command
```bash
nimble extract --url "https://www.amazon.com/s?k=noise+cancelling+headphones" --country US --parse \
  --parser '{"type":"schema_list","selector":...}'
```
## Result
Success — 22 products returned. Parser extracted product_name, ASIN, price, rating from each [data-component-type=s-search-result] element. URLs constructed as https://www.amazon.com/dp/{ASIN}.
## Notes
- Used amazon.com/s? search URL (not single /dp/ product page) — correct per SKILL.md
- No render flag needed for Amazon search results
