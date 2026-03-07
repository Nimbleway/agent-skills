# Transcript — eval-map-docs (with skill)
## Command
```bash
nimble --transform "links.#.url" map --url "https://docs.python.org/3/" --limit 80
```
## Result
80 URLs returned. Top-level path segments discovered:
/3/library/ — standard library (most common)
/3/tutorial/ — beginner tutorial
/3/reference/ — language reference
/3/howto/ — HOWTOs
/3/c-api/ — C API
/3/using/ — platform-specific usage (iOS, Windows, editors)
/3/whatsnew/ — version changelogs
/3/faq/ — FAQ
/3/glossary.html — glossary
## Notes
- Map returned unordered URLs — required deduplication by path prefix
