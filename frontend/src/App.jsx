import { ChatWindow } from "./components/ChatWindow";
import { InputBar } from "./components/InputBar";
import { useChat } from "./hooks/useChat";

export default function App() {
  const { messages, loading, error, send, clear } = useChat();

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-[#f7f7f5] text-slate-950">
      <header className="z-20 shrink-0 border-b border-slate-200 bg-[#f7f7f5]/95 px-4 backdrop-blur sm:px-6">
        <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-slate-950 text-sm font-semibold text-white">
              RAG
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-base font-semibold sm:text-lg">
                Research Paper Assistant
              </h1>
              <p className="truncate text-sm text-slate-500">
                Ask questions and get answers from the knowledge.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              className="shrink-0 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 shadow-sm transition hover:border-slate-400 hover:bg-slate-50"
              type="button"
              onClick={clear}
            >
              Clear chat
            </button>
          </div>
        </div>
      </header>

      <main className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <ChatWindow messages={messages} loading={loading} onPromptClick={send} />

        <div className="z-20 shrink-0 border-t border-slate-200 bg-[#f7f7f5]/95 px-4 pb-4 pt-3 backdrop-blur">
          <div className="mx-auto w-full max-w-3xl">
            {error ? (
              <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-[15px] text-red-700">
                {error}
              </div>
            ) : null}

            <InputBar onSend={send} loading={loading} />
          </div>
        </div>
      </main>
    </div>
  );
}
