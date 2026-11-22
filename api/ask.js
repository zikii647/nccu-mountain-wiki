import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

let cachedBundle = null;
let cachedSystemPrompt = null;

function loadWikiBundle() {
  if (cachedBundle) return cachedBundle;
  const candidates = [
    path.join(process.cwd(), "api", "_wiki_bundle.json"),
    new URL("./_wiki_bundle.json", import.meta.url),
  ];
  for (const loc of candidates) {
    try {
      const raw = fs.readFileSync(loc, "utf8");
      cachedBundle = JSON.parse(raw);
      return cachedBundle;
    } catch {
      // try next candidate
    }
  }
  throw new Error("找不到知識庫打包檔 api/_wiki_bundle.json，請確認已執行 npm run build。");
}

function buildSystemPrompt(bundle) {
  if (cachedSystemPrompt) return cachedSystemPrompt;

  const docsText = bundle.documents
    .map((doc) => `===== 檔案：${doc.path} =====\n${doc.content}`)
    .join("\n\n");

  cachedSystemPrompt = `你是「政大登山隊 Wiki 知識庫問答助手」，最高宗旨是「確保大家上山安全平安」。

請嚴格遵守以下不可違反的規則：
1. **唯讀依據 Wiki**：你只能依據下方提供的「政大登山隊 Wiki 知識庫（wiki/）」內容，使用**繁體中文＋台灣登山慣用術語**回答問題。
2. **強制標註出處**：回答中每一個關鍵規則、數據、案例、費用標準或安全警示，**必須標註對應的 wiki/ 檔名出處**（格式例如：\`wiki/guides/trip-settlement-and-finance-sop.md\` 或 \`wiki/trips/2025-12-daba-four-peaks.md\`）。
3. **誠實回答未記載、嚴禁憑空捏造**：若使用者詢問的事項、路線、數據、藥物劑量、裝備門檻或規定在下方 wiki/ 內容中**沒有記載**，必須誠實明確回答**「目前社團 Wiki 未記載」**，絕對不可憑空腦補或推測（尤其是撤退路線、水源狀況、用藥劑量／禁忌、裝備門檻與財務費率）。
4. **區分原始記載與 AI 安全提醒**：若引用的 wiki/ 段落標註為「AI 安全提醒／待補齊／時效提醒」，回答時須明確區隔其提醒性質，不可混作原始出隊紀錄。
5. **跨年份矛盾並陳**：若不同隊伍或年份對同一地點（如水源、路況、營地）有不同記載，須並陳雙方年份與出處，並提醒以最新紀錄優先參考且行前仍須查核最新山況。
6. **排版清楚易讀**：使用簡潔的 Markdown 標題、條列清單與標準警示框（\`> [!WARNING]\` 或 \`> [!CAUTION]\`）呈現重點，方便幹部在手機上快速查閱。

以下是完整的政大登山隊 Wiki 知識庫（共 ${bundle.docCount} 份檔案）：

${docsText}`;

  return cachedSystemPrompt;
}

function verifyPasscode(input, expected) {
  if (typeof input !== "string" || typeof expected !== "string" || !expected) {
    return false;
  }
  const a = Buffer.from(input.trim(), "utf8");
  const b = Buffer.from(expected.trim(), "utf8");
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

function sanitizeHistory(history) {
  if (!Array.isArray(history)) return [];
  const valid = [];
  // Keep at most the latest 10 turns to stay fast and focused
  const recent = history.slice(-10);
  for (const item of recent) {
    if (!item || typeof item !== "object") continue;
    const role = item.role === "assistant" || item.role === "model" ? "model" : "user";
    const text = typeof item.content === "string" ? item.content.trim() : "";
    if (!text) continue;
    valid.push({
      role,
      parts: [{ text: text.slice(0, 4000) }],
    });
  }
  return valid;
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") {
    res.setHeader("Allow", "POST, OPTIONS");
    return res.status(204).end();
  }

  if (req.method !== "POST") {
    res.setHeader("Allow", "POST, OPTIONS");
    return res.status(405).json({ error: "僅支援 POST 請求。" });
  }

  const clubPasscode = process.env.CLUB_PASSCODE;
  const geminiApiKey = process.env.GEMINI_API_KEY;
  const envModel =
    typeof process.env.GEMINI_MODEL === "string" ? process.env.GEMINI_MODEL.trim() : "";
  const modelCandidates = Array.from(
    new Set([envModel, "gemini-3.5-flash-lite", "gemini-3.8-flash"].filter(Boolean))
  );
  const PER_MODEL_TIMEOUT_MS = 20000;

  if (!clubPasscode) {
    return res.status(500).json({ error: "伺服器尚未設定環境變數 CLUB_PASSCODE。" });
  }

  let body = req.body;
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch {
      return res.status(400).json({ error: "請求 JSON 格式錯誤。" });
    }
  }
  if (!body || typeof body !== "object") {
    return res.status(400).json({ error: "請提供有效的 JSON 請求內容。" });
  }

  const { passcode, question, history, verifyOnly } = body;

  if (!verifyPasscode(passcode, clubPasscode)) {
    return res.status(401).json({ error: "社團通關密碼錯誤，請重新輸入或向幹部確認。" });
  }

  let bundle;
  try {
    bundle = loadWikiBundle();
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }

  // Allow lightweight passcode check on login screen
  if (verifyOnly === true) {
    return res.status(200).json({
      ok: true,
      docCount: bundle.docCount,
      generatedAt: bundle.generatedAt,
    });
  }

  if (typeof question !== "string" || !question.trim()) {
    return res.status(400).json({ error: "請輸入要查詢的問題。" });
  }

  const trimmedQuestion = question.trim();
  if (trimmedQuestion.length > 2000) {
    return res.status(400).json({ error: "問題長度超過 2,000 字上限，請精簡後再試。" });
  }

  if (!geminiApiKey) {
    return res.status(500).json({ error: "伺服器尚未設定環境變數 GEMINI_API_KEY。" });
  }

  const systemPrompt = buildSystemPrompt(bundle);
  const contents = [
    ...sanitizeHistory(history),
    {
      role: "user",
      parts: [{ text: trimmedQuestion }],
    },
  ];

  const attempts = [];
  let lastStatus = 502;
  let lastErrorMsg = "模型暫時無法回應，請稍後再試。";

  for (const currentModel of modelCandidates) {
    const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(
      currentModel
    )}:generateContent`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), PER_MODEL_TIMEOUT_MS);

    try {
      const upstream = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-goog-api-key": geminiApiKey,
        },
        signal: controller.signal,
        body: JSON.stringify({
          systemInstruction: {
            parts: [{ text: systemPrompt }],
          },
          contents,
          generationConfig: {
            temperature: 0.2,
            maxOutputTokens: 1200,
          },
        }),
      });

      const data = await upstream.json().catch(() => ({}));

      if (!upstream.ok) {
        const apiMsg = data?.error?.message || `HTTP ${upstream.status}`;
        attempts.push(`${currentModel}: HTTP ${upstream.status}`);
        lastStatus = upstream.status === 429 ? 429 : upstream.status === 503 ? 503 : 502;
        lastErrorMsg =
          upstream.status === 429
            ? "目前查詢流量較高（API 額度限制），請稍候幾秒再試。"
            : upstream.status === 503
              ? "目前 Gemini 模型負載過高（503），請稍候幾秒再試。"
              : `模型回覆失敗（${currentModel}）：${apiMsg}`;

        // Retry next fallback model on 503 / 429 / 504
        if (upstream.status === 503 || upstream.status === 429 || upstream.status === 504) {
          continue;
        }
        return res.status(lastStatus).json({ error: lastErrorMsg, attempts });
      }

      const parts = data?.candidates?.[0]?.content?.parts || [];
      const answer = parts
        .map((p) => (typeof p.text === "string" ? p.text : ""))
        .join("")
        .trim();

      if (!answer) {
        attempts.push(`${currentModel}: empty response`);
        lastStatus = 502;
        lastErrorMsg = "模型未回傳有效內容，請換個方式提問或稍後再試。";
        continue;
      }

      const cited = Array.from(
        new Set(answer.match(/wiki\/[A-Za-z0-9_./-]+\.md/g) || [])
      );

      return res.status(200).json({
        answer,
        model: currentModel,
        docCount: bundle.docCount,
        sources: cited,
      });
    } catch (err) {
      const isTimeout = err?.name === "AbortError";
      attempts.push(`${currentModel}: ${isTimeout ? "timeout (20s)" : err.message}`);
      lastStatus = isTimeout ? 504 : 502;
      lastErrorMsg = isTimeout
        ? "模型回應逾時，已嘗試備援模型仍無回應，請稍後再試。"
        : `連線至 Gemini API 時發生錯誤：${err.message}`;
      // Auto-fallback to next model on timeout or network error
      continue;
    } finally {
      clearTimeout(timer);
    }
  }

  return res.status(lastStatus).json({
    error: `${lastErrorMsg}（已嘗試：${attempts.join(" → ")}）`,
    attempts,
  });
}
