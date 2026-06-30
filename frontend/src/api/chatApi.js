const API_URL = import.meta.env.VITE_API_URL;

function getApiBaseUrl() {
  if (!API_URL) {
    throw new Error(
      "Missing VITE_API_URL. Create frontend/.env from frontend/.env.example"
    );
  }
  return API_URL.replace(/\/+$/, "");
}

function getErrorMessage(detail, fallback) {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg;
  }

  return fallback;
}

export async function askQuestion(question, useRerank = true) {
  const res = await fetch(`${getApiBaseUrl()}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, use_rerank: useRerank }),
  });

  if (!res.ok) {
    let message = `Server error: ${res.status}`;
    try {
      const data = await res.json();
      message = getErrorMessage(data?.detail, message);
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  return res.json();
}
