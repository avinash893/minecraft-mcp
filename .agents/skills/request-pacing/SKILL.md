---
name: request-pacing
description: >-
  Enforce slow pacing and rate limiting for API, network, panel, or server requests.
  Use whenever making repeated web requests, panel commands, retries, or server interactions to prevent spamming, 504 timeouts, or HTTP 429 rate limits.
---

# Request Pacing & Rate Limiting

## Core Principles
1. **Never Rapid Fire**: Never execute network or panel API requests in tight unpaused loops.
2. **Paced Retries**: Wait a minimum of 10–15 seconds between failed attempts or repetitive status queries.
3. **Respect Retry-After**: If a service returns `504 Gateway Timeout` or `429 Too Many Requests` or includes a `retry_after` header / message, wait the specified duration (e.g., 60s - 120s) before issuing another call.
4. **Exponential Backoff**: For polling daemon states or recovering from transient connection errors, progressively increase delay: 10s -> 20s -> 40s -> 60s.
