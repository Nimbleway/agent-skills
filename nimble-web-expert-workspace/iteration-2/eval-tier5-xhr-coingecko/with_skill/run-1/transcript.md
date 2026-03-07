# Transcript — eval-tier5-xhr-coingecko (with skill)
## Command
```bash
nimble extract \
  --url "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd" \
  --is-xhr
```
## Result
Success — JSON returned in 456ms. Raw response:
{"bitcoin":{"usd":66098},"ethereum":{"usd":1939.39},"solana":{"usd":83.78}}
## Notes
- No --render flag used — JSON API doesn't need browser rendering
- --is-xhr flag required for JSON/XHR endpoints
- CoinGecko free tier, no auth needed
