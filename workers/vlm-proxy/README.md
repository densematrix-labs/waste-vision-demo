# VLM Proxy Worker

Cloudflare Worker for real VLM analysis. The browser posts image data to this Worker; the Worker calls DenseMatrix LLM Proxy and returns structured evidence regions.

Required secret:

```bash
LLM_PROXY_API_KEY
```

Deploy:

```bash
cd workers/vlm-proxy
npx wrangler secret put LLM_PROXY_API_KEY
npx wrangler deploy
```

Runtime endpoint expected by the demo:

```bash
https://waste-vision-vlm.densematrix.ai/analyze
```

The current upstream proxy must have working VLM quota. If the upstream returns a quota error, the Worker returns a visible VLM service error instead of fabricating results.
