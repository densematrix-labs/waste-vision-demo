const EVENT_VALUES = new Set(["pileup", "normal"]);
const REGION_VALUES = new Set(["pileup"]);

const REGION_TITLES = {
  pileup: "堆放证据"
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
  const label = REGION_VALUES.has(item?.label) ? item.label : "pileup";
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
  if (!trimmed) throw new Error("empty model response");
  try {
    return JSON.parse(trimmed);
  } catch {
    const match = trimmed.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("model response is not JSON");
    return JSON.parse(match[0]);
  }
}

function publicErrorMessage(error) {
  const message = String(error?.message || "");
  if (/key limit exceeded|quota|rate limit|insufficient/i.test(message)) {
    return "智能分析上游额度已用尽，请补充额度或切换模型后重试。";
  }
  if (/LLM_PROXY_API_KEY/i.test(message)) {
    return "智能分析服务密钥未配置。";
  }
  if (/upstream model failed/i.test(message)) {
    return "智能分析上游服务暂时不可用。";
  }
  return "智能分析失败，请稍后重试或提交人工复核。";
}

function buildPrompt(width, height, context) {
  return [
    "你是垃圾投放点固定机位巡检系统的桶旁堆放识别模块。",
    "本次只判断一个业务问题：投放点周边是否存在垃圾堆放。",
    "pileup 定义：垃圾袋、纸箱、泡沫箱、大件杂物或多个投放物集中堆在垃圾桶外、投放点前方或投放点旁边，明显超出正常临时投放状态。",
    "normal 定义：投放点周边没有成堆垃圾袋、纸箱或大件杂物。地面污渍、水渍、阴影、单个小碎片、桶内垃圾接近满、桶盖打开，都不算 pileup。",
    "不要判断其他清运或保洁类别；这些类别不在本次 demo 范围内。",
    "如果只有少量零散小垃圾或地面污痕，必须输出 normal 且 regions 为空。",
    "如果判断为 normal，regions 必须为空，不要为了展示而画框。",
    "如果判断为 pileup，输出所有主要且彼此分离的堆放证据区域：每个区域只框一个堆放主体或堆放团块，避免重复框同一堆。",
    "证据区域必须紧贴垃圾袋、纸箱、泡沫箱或大件杂物本体；不要框整片地面，不要框垃圾桶本体，不要框道路、墙面、阴影、污渍或背景。",
    "如果多个堆放物彼此接触或明显属于同一堆，合并成一个紧凑框；如果相隔较远，分成多个框。",
    "不要为了显得全面而扩大框；宁可少框，也不要把非垃圾区域框进去。",
    "请输出一小段适合给客户看的现场说明，说明为什么触发或不触发堆放工单。",
    "现场说明只使用“桶外堆放”“投放点周边堆放”“未发现堆放”等业务语言，不要使用满溢、散落、脏污等其他类别词。",
    "只输出 JSON，不要输出 markdown，不要解释 JSON 之外的内容。",
    `图片尺寸为 ${width}x${height}。`,
    "证据区域坐标必须使用 0-1000 归一化坐标系：左上角为 (0,0)，右下角为 (1000,1000)。",
    "不要输出像素坐标；不要输出超过 0-1000 的坐标；必须保证 x1 < x2 且 y1 < y2。",
    "事件类别只能从 pileup、normal 中选择。",
    "证据区域 label 只能使用 pileup。",
    "如果没有明确证据区域，regions 返回空数组，不要编造坐标。",
    "输出格式：",
    '{"predictions":[{"event":"pileup","score":0.88},{"event":"normal","score":0.12}],"regions":[{"label":"pileup","score":0.84,"x1":120,"y1":280,"x2":360,"y2":760},{"label":"pileup","score":0.72,"x1":500,"y1":320,"x2":650,"y2":700}],"rationale":"一句话说明核心视觉依据"}',
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
    const message = payload?.error?.message || payload?.message || `upstream model failed: ${response.status}`;
    throw new Error(message);
  }
  const content = payload?.choices?.[0]?.message?.content;
  const parsed = extractJson(Array.isArray(content) ? content.map((item) => item.text || "").join("\n") : content);
  const predictions = (Array.isArray(parsed.predictions) ? parsed.predictions : [])
    .map(normalizePrediction)
    .sort((a, b) => b.score - a.score);
  const topEvent = predictions[0]?.event || "normal";
  const regions = topEvent === "pileup"
    ? (Array.isArray(parsed.regions) ? parsed.regions : []).map((item) => normalizeRegion(item, width, height)).slice(0, 6)
    : [];
  return {
    predictions,
    regions,
    rationale: String(parsed.rationale || "云端分析已完成画面理解，并生成结构化识别结果。"),
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
