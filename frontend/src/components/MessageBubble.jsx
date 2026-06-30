const EMPHASIS_PATTERN = /(\*\*[^*]+?\*\*|__[^_]+?__)/g;

function renderEmphasis(text) {
  const parts = String(text ?? "").split(EMPHASIS_PATTERN);

  return parts.map((part, index) => {
    const isBold =
      (part.startsWith("**") && part.endsWith("**")) ||
      (part.startsWith("__") && part.endsWith("__"));

    if (!isBold) {
      return part;
    }

    return (
      <strong className="font-semibold" key={index}>
        {part.slice(2, -2)}
      </strong>
    );
  });
}

function SourceCard({ source, index }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
      <div className="flex items-center justify-between gap-3">
        <span className="font-semibold text-slate-950">Source {index + 1}</span>
        <span className="rounded-full bg-white px-2 py-1 font-medium text-slate-500 ring-1 ring-slate-200">
          {source.chunk_id ?? "chunk"}
        </span>
      </div>
      <p className="mt-2 font-medium text-slate-900">
        {source.title || "Document section"}
      </p>
      <p className="mt-1 text-[11px] uppercase tracking-[0.2em] text-slate-500">
        {source.source || "unknown source"}
      </p>
    </div>
  );
}

export function MessageBubble({ role, content, loading = false, sources = [] }) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser ? (
        <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white text-xs font-semibold text-slate-800 shadow-sm ring-1 ring-slate-200">
          AI
        </div>
      ) : null}

      <article
        className={[
          "max-w-[82%] whitespace-pre-wrap text-sm leading-6 shadow-sm sm:max-w-[72%]",
          isUser
            ? "rounded-2xl rounded-br-md bg-slate-950 px-4 py-3 text-white"
            : "rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-slate-900",
        ].join(" ")}
      >
        {loading ? (
          <div className="flex items-center gap-2 text-slate-500">
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:150ms]" />
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:300ms]" />
          </div>
        ) : (
          <div className="space-y-4">
            <div>{renderEmphasis(content)}</div>

            {!isUser && sources.length > 0 ? (
              <div className="space-y-2 border-t border-slate-200 pt-3">
                <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
                  Sources
                </div>
                <div className="grid gap-2 sm:grid-cols-2">
                  {sources.map((source, index) => (
                    <SourceCard key={source.id ?? `${source.source}-${index}`} source={source} index={index} />
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </article>
    </div>
  );
}
