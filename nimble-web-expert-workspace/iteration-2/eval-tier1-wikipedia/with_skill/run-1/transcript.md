# Transcript — eval-tier1-wikipedia (with skill)
## Command
```bash
nimble --transform "data.markdown" extract \
  --url "https://en.wikipedia.org/wiki/Quantum_computing" \
  --parse --format markdown
```
## Result
Success — 174KB of Wikipedia article returned as markdown (Tier 1, static extraction, no --render needed).
Content included: Bloch sphere description, qubit, superposition, entanglement, quantum gates, Shor's algorithm, current hardware.
## Notes
- No render flag needed — Wikipedia is static HTML
- Output piped via head to avoid flooding context
