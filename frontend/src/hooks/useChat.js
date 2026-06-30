import { useCallback, useState } from "react";
import { askQuestion } from "../api/chatApi";

function createMessage(role, content, extra = {}) {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    ...extra,
  };
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const send = useCallback(async (text) => {
    const trimmed = (text ?? "").trim();
    if (!trimmed || loading) return;

    const userMsg = createMessage("user", trimmed);

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      const data = await askQuestion(trimmed);
      const botMsg = createMessage("assistant", data.answer, {
        sources: Array.isArray(data.sources) ? data.sources : [],
      });
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setError(err?.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, send, clear };
}
