import { useCallback, useState } from "react";

export function InputBar({ onSend, loading }) {
  const [text, setText] = useState("");

  const trimmed = text.trim();
  const disabled = loading || !trimmed;

  const submit = useCallback(() => {
    if (disabled) return;
    setText("");
    onSend(trimmed);
  }, [disabled, onSend, trimmed]);

  return (
    <form
      className="rounded-[1.4rem] border border-slate-200/80 bg-white/90 p-2 shadow-[0_18px_60px_rgba(15,23,42,0.12)] backdrop-blur"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <div className="flex items-end gap-2">
        <textarea
          className="max-h-40 min-h-14 flex-1 resize-none rounded-2xl border-0 bg-transparent px-4 py-3 text-sm leading-6 text-slate-900 outline-none placeholder:text-slate-400"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask about a paper, method, result, or comparison..."
          disabled={loading}
          rows={1}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
        />
        <button
          className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-slate-950 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          disabled={disabled}
          type="submit"
          aria-label="Send message"
        >
          {loading ? "..." : "↑"}
        </button>
      </div>
    </form>
  );
}
