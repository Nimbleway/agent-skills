---
name: nimble-media-reference
description: |
  Reference for nimble media command. Load when downloading binary files — images,
  videos, audio, or documents — from any URL. Contains: sync vs async decision,
  command flags, output handling, batch patterns, MIME filtering, geo-targeting,
  map→media pipeline, cost note, error handling.
metadata:
  author: Nimbleway
  version: "0.21.2"
---

# nimble media — reference

Downloads binary media files (images, videos, audio, documents) from any URL through
Nimble's infrastructure. Bypasses geo-restrictions and access controls.

## Commands

| Command                    | When to use                                              |
| -------------------------- | -------------------------------------------------------- |
| `nimble media run`         | Single file or small batch — result streamed directly    |
| `nimble media run-async`   | Large files or bulk batches — file saved to cloud storage |

---

## Parameters

### Both commands

| Flag                     | Type   | Required | Description                                                       |
| ------------------------ | ------ | -------- | ----------------------------------------------------------------- |
| `--url`                  | string | Yes      | URL of the media file to download                                 |
| `--expected-mime-type`   | string | No       | Acceptable MIME type — repeatable. Wildcards supported (`image/*`). Request fails if response doesn't match. |
| `--country`              | string | No       | ISO Alpha-2 code for geo-targeted download (e.g. `US`, `DE`)     |
| `--locale`               | string | No       | LCID locale (e.g. `en-US`, `auto` to infer from `--country`)     |

### Async-only (`run-async`)

| Flag                     | Type    | Required | Description                                              |
| ------------------------ | ------- | -------- | -------------------------------------------------------- |
| `--storage.url`          | string  | Yes      | Cloud storage path (e.g. `s3://my-bucket/media/`)        |
| `--storage.type`         | string  | No       | Provider: `s3` (default), `gcs`, `do`                   |
| `--storage.object-name`  | string  | No       | Custom filename without extension (extension auto-appended). Must be unique per request — use `product_{id}` or `media_{timestamp}` patterns. |
| `--callback-url`         | string  | No       | Webhook URL called on completion                         |
| `--storage-compress`     | bool    | No       | Compress stored file                                     |

---

## Sync vs async decision

Use **`media run`** when:
- Downloading 1–10 files
- File size is small to medium
- You want the binary directly (save locally)

Use **`media run-async`** when:
- Files are large (videos, high-res images)
- Downloading 20+ files — async + cloud storage avoids local disk and timeout issues
- Output goes directly into a pipeline (S3 bucket, training dataset)

---

## Output handling

`nimble media run` returns raw binary — pipe to a file with shell redirect:

```bash
# Single image
nimble media run --url "https://example.com/product.jpg" > ~/.nimble/downloads/product.jpg

# With MIME type validation
nimble media run \
  --url "https://example.com/hero.webp" \
  --expected-mime-type "image/webp" \
  --expected-mime-type "image/jpeg" \
  > ~/.nimble/downloads/hero.webp

# Geo-targeted download
nimble media run \
  --url "https://example.com/regional.jpg" \
  --country DE --locale de-DE \
  --expected-mime-type "image/*" \
  > ~/.nimble/downloads/regional.jpg
```

`nimble media run-async` returns a task object — poll with `nimble tasks get`:

```bash
# Submit async — file delivered to S3
nimble media run-async \
  --url "https://example.com/video.mp4" \
  --expected-mime-type "video/mp4" \
  --storage.url "s3://my-bucket/media/" \
  --storage.type s3 \
  --storage.object-name "video-$(date +%s)"

# Poll until done
nimble tasks get --task-id <task_id>
# state: pending → processing → success / failed
```

See `references/nimble-tasks/SKILL.md` for the full polling flow.

---

## Batch patterns

**2–5 files — parallel bash:**

```bash
mkdir -p .nimble
nimble media run --url "https://example.com/img1.jpg" > ~/.nimble/downloads/img1.jpg &
nimble media run --url "https://example.com/img2.jpg" > ~/.nimble/downloads/img2.jpg &
nimble media run --url "https://example.com/img3.jpg" > ~/.nimble/downloads/img3.jpg &
wait
```

**20+ files — async to cloud storage:**

Submit each URL as `run-async` with a unique `--storage.object-name`. Use Python asyncio (see `references/batch-patterns.md`) to submit all requests in parallel, collect task IDs, then poll for completion.

---

## MIME type filtering

Use `--expected-mime-type` to validate the file before accepting it. Wildcards supported:

| Filter                               | Accepts                        |
| ------------------------------------ | ------------------------------ |
| `image/*`                            | Any image format               |
| `image/webp` `image/jpeg`            | WebP or JPEG only              |
| `video/mp4`                          | MP4 video only                 |
| `image/*` `video/mp4`                | Any image or MP4               |

If the response MIME type doesn't match, the request fails — no partial data.
Omit the flag to accept any MIME type.

---

## nimble map → nimble media pipeline

When you need to download all media from a site section, use `nimble map` first to
discover the URLs, then `nimble media run` to download them:

```bash
# Step 1 — discover media URLs
nimble map --url "https://example.com/gallery" --limit 100 > ~/.nimble/downloads/gallery-urls.json

# Step 2 — extract image URLs from map output, then download in parallel
# (parse ~/.nimble/downloads/gallery-urls.json for image URLs, then batch with & + wait)
```

---

## Cost

Media Download is billed at **$2.00 / GB** (Media-VX6 driver). Only successful downloads count toward usage.

---

## Error handling

| Error                        | Cause                                           | Fix                                               |
| ---------------------------- | ----------------------------------------------- | ------------------------------------------------- |
| MIME type mismatch           | Response type didn't match `--expected-mime-type` | Broaden filter or remove it; check URL is correct |
| Empty / zero-byte output     | URL returned non-binary (HTML error page)       | Check URL directly; add `--expected-mime-type`    |
| Geo-restricted content       | Content blocked in default geo                  | Add `--country` matching the content's region     |
| Async task state `failed`    | Download failed server-side                     | Retry once; check `task.error` field in response  |
| Duplicate `object_name`      | Two async requests used the same name           | Use unique suffix: `name-$(date +%s%N)`           |
| 429 rate limit               | Stop immediately — do not retry                 | See `references/error-handling.md`                |
