# Transcript — eval-tier3-yelp (with skill)
## First attempt (browser-action recipe from SKILL.md — failed)
```bash
nimble extract --url "..." --render --browser-action [...] --render-options '{"userbrowser": true}' ...
```
Error: `flag provided but not defined: -render-options`
**Root cause**: `--render-options` is a v0.5.0+ flag. v0.4.3 does not support it.

## Second attempt (Tier 3 stealth fallback — success)
```bash
nimble --transform "data.markdown" extract \
  --url "https://www.yelp.com/search?find_desc=italian+restaurant&find_loc=San+Francisco,CA" \
  --render --driver vx10-pro --country US --parse --format markdown
```
Result: Markdown returned with Yelp restaurant listings, names, ratings, and review counts.
## Notes
- --render-options flag doesn't exist in v0.4.3 — SKILL.md browser-action recipe needs a v0.4.x compat note
- Stealth driver vx10-pro was sufficient for Yelp
