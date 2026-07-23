const EVENT_VALUES = new Set(["overflow", "litter", "dirty", "normal"]);
const REGION_VALUES = new Set(["overflow_area", "scattered_litter", "pileup", "dirty_ground", "blocked_opening"]);

const REGION_TITLES = {
  overflow_area: "满溢证据",
  scattered_litter: "散落证据",
  pileup: "堆放证据",
  dirty_ground: "脏污证据",
  blocked_opening: "投放口阻挡证据"
};

function jsonResponse(payload, status = 200, origin = "*") {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Vary": "Origin"
    }
  });
}

function getAllowedOrigin(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = String(env.ALLOWED_ORIGINS || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return allowed.includes(origin) ? origin : allowed[0] || "*";
}

function clampNumber(value, min, max, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.max(min, Math.min(max, number));
}

function normalizePrediction(item) {
  const event = EVENT_VALUES.has(item?.event) ? item.event : "normal";
  return {
    event,
    score: clampNumber(item?.score, 0.01, 0.99, 0.5)
  };
}

function normalizeRegion(item, width, height) {
  const label = REGION_VALUES.has(item?.label) ? item.label : "scattered_litter";
  const x1 = Math.round((clampNumber(item?.x1, 0, 1000, 0) / 1000) * width);
  const y1 = Math.round((clampNumber(item?.y1, 0, 1000, 0) / 1000) * height);
  const x2 = Math.round((clampNumber(item?.x2, 0, 1000, 1000) / 1000) * width);
  const y2 = Math.round((clampNumber(item?.y2, 0, 1000, 1000) / 1000) * height);
  return {
    label,
    title: REGION_TITLES[label],
    score: clampNumber(item?.score, 0.01, 0.99, 0.5),
    x1: Math.min(x1, x2),
    y1: Math.min(y1, y2),
    x2: Math.max(x1, x2),
    y2: Math.max(y1, y2)
  };
}

function extractJson(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed) throw new Error("empty VLM response");
  try {
    return JSON.parse(trimmed);
  } catch {
    const match = trimmed.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("VLM response is not JSON");
    return JSON.parse(match[0]);
  }
}

function publicErrorMessage(error) {
  const message = String(error?.message || "");
  if (/key limit exceeded|quota|rate limit|insufficient/i.test(message)) {
    return "VLM 上游额度已用尽，请补充额度或切换模型后重试。";
  }
  if (/LLM_PROXY_API_KEY/i.test(message)) {
    return "VLM 服务密钥未配置。";
  }
  if (/upstream VLM failed/i.test(message)) {
    return "VLM 上游服务暂时不可用。";
  }
  return "VLM 分析失败，请稍后重试或提交人工复核。";
}

function buildPrompt(width, height, context) {
  return [
    "你是垃圾投放点固定机位巡检系统的视觉研判模块。",
    "业务定义：overflow 表示垃圾桶或投放点容量明显超出，包括桶口满溢、桶旁堆积、垃圾袋或纸箱堆放在投放点周边。",
    "业务定义：litter 表示少量散落垃圾；dirty 表示地面污渍、水渍、黑斑、油污或长期脏污；normal 表示无明显异常。",
    "blocked_opening 只在投放口、投放门、桶盖或通道被外部物体物理遮挡、导致无法投放时使用；不要把桶内垃圾满、桶旁堆积或普通满溢误判为 blocked_opening。",
    "请判断客户现有模型难以稳定识别的疑难现场截图。",
    "只输出 JSON，不要输出 markdown，不要解释 JSON 之外的内容。",
    `图片尺寸为 ${width}x${height}。`,
    "证据区域坐标必须使用 0-1000 归一化坐标系：左上角为 (0,0)，右下角为 (1000,1000)。",
    "不要输出像素坐标；不要输出超过 0-1000 的坐标；必须保证 x1 < x2 且 y1 < y2。",
    "事件类别只能从 overflow、litter、dirty、normal 中选择。",
    "证据区域 label 只能从 overflow_area、scattered_litter、pileup、dirty_ground、blocked_opening 中选择。",
    "如果没有明确证据区域，regions 返回空数组，不要编造坐标。",
    "输出格式：",
    '{"predictions":[{"event":"overflow","score":0.88}],"regions":[{"label":"overflow_area","score":0.84,"x1":120,"y1":280,"x2":720,"y2":910}],"rationale":"一句话说明核心视觉依据"}',
    `现场上下文：${JSON.stringify(context || {})}`
  ].join("\n");
}

async function callVlm(env, body) {
  if (!env.LLM_PROXY_API_KEY) {
    throw new Error("LLM_PROXY_API_KEY is not configured");
  }
  const width = clampNumber(body.width, 1, 10000, 768);
  const height = clampNumber(body.height, 1, 10000, 432);
  const response = await fetch(`${env.LLM_PROXY_BASE_URL || "https://llm-proxy.densematrix.ai"}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.LLM_PROXY_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: env.VLM_MODEL || "claude-opus-4.6",
      response_format: { type: "json_object" },
      temperature: 0.1,
      messages: [
        {
          role: "user",
          content: [
            { type: "text", text: buildPrompt(width, height, body.context) },
            { type: "image_url", image_url: { url: body.image } }
          ]
        }
      ]
    })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload?.error?.message || payload?.message || `upstream VLM failed: ${response.status}`;
    throw new Error(message);
  }
  const content = payload?.choices?.[0]?.message?.content;
  const parsed = extractJson(Array.isArray(content) ? content.map((item) => item.text || "").join("\n") : content);
  return {
    predictions: (Array.isArray(parsed.predictions) ? parsed.predictions : []).map(normalizePrediction).sort((a, b) => b.score - a.score),
    regions: (Array.isArray(parsed.regions) ? parsed.regions : []).map((item) => normalizeRegion(item, width, height)),
    rationale: String(parsed.rationale || "视觉大模型已完成画面理解，并生成结构化研判结果。"),
    model: env.VLM_MODEL || "claude-opus-4.6",
    upstreamRequestId: payload.id || null
  };
}

export default {
  async fetch(request, env) {
    const origin = getAllowedOrigin(request, env);
    if (request.method === "OPTIONS") {
      return jsonResponse({ ok: true }, 200, origin);
    }
    if (request.method !== "POST") {
      return jsonResponse({ error: "method not allowed" }, 405, origin);
    }
    try {
      const body = await request.json();
      if (!body.image || typeof body.image !== "string" || !body.image.startsWith("data:image/")) {
        return jsonResponse({ error: "image must be a data:image URL" }, 400, origin);
      }
      const startedAt = Date.now();
      const result = await callVlm(env, body);
      return jsonResponse({ ...result, elapsedMs: Date.now() - startedAt }, 200, origin);
    } catch (error) {
      return jsonResponse({ error: publicErrorMessage(error) }, 502, origin);
    }
  }
};
