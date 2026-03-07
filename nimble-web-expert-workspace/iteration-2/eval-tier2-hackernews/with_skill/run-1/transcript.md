# Transcript — eval-tier2-hackernews (with skill)
## Command
```bash
nimble --transform "data.markdown" extract \
  --url "https://news.ycombinator.com" \
  --parse --format markdown
```
## Result
Success — Tier 1 (static, no render needed). HN is server-side rendered HTML.
Got 30 stories with title, points, and comment count. No --render flag required.
## Notes
- HN does NOT require JavaScript rendering — plain HTML extraction works
- Stories include point counts and comment counts inline in the markdown
