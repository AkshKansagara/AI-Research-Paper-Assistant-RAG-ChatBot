import { MessageBubble } from "./MessageBubble";

const starterPrompts = [
  "What is multi head attention and why is it used?",
  "What is positional encoding and why does the transformer need it?",
  "How RAG Works?",
  "How does the encoder decoder structure work in the transformer?.",
];

export function ChatWindow({ messages, loading, onPromptClick }) {
  const isEmpty = messages.length === 0;

  return (
    <div
      className="flex-1 overflow-auto px-4 py-6"
      role="log"
      aria-live="polite"
    >
      <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col">
        {isEmpty ? (
          <div className="flex flex-1 flex-col items-center justify-center py-10 text-center">
            <div className="mb-8 max-w-2xl">
              <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-xl bg-slate-950 text-sm font-semibold text-white">
                RAG
              </div>
              <h2 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-[2.6rem]">
                Ask questions about the papers.
              </h2>
              <p className="mt-3 text-[15px] leading-7 text-slate-600 sm:text-base">
                Get a direct answer from the backend with the most relevant
                sources attached below it.
              </p>
            </div>

            <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-2">
              {starterPrompts.map((prompt) => (
                <button
                  className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-center text-[15px] text-slate-800 shadow-sm transition hover:border-slate-300 hover:bg-slate-50"
                  key={prompt}
                  type="button"
                  onClick={() => onPromptClick(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((m, idx) => {
              if (!m.content) return null;
              return (
                <MessageBubble
                  key={m.id ?? idx}
                  role={m.role}
                  content={m.content}
                  sources={m.sources ?? []}
                />
              );
            })}

            {loading ? <MessageBubble role="assistant" loading /> : null}
          </div>
        )}
      </div>
    </div>
  );
}
