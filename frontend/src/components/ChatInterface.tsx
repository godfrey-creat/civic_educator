import { useState } from "react";
import { sendChatMessage } from "../utils/api";

interface Message {
  role: "user" | "bot";
  text: string;
  citations?: {
    title: string;
    snippet: string;
    source_link?: string;
  }[];
}

interface ChatInterfaceProps {
  role: "resident" | "staff";
}

export default function ChatInterface({ role }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage: Message = { role: "user", text: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const res = await sendChatMessage(userMessage.text, role);
      const botMessage: Message = {
        role: "bot",
        text: res.reply || "",
        citations: Array.isArray(res.citations) ? res.citations : [],
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setError("⚠️ Unable to process request.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-panel border border-divider rounded-xl p-4 shadow">
      <h2 className="text-xl font-semibold mb-4">Chat</h2>

      {/* Message history */}
      <div
        className="space-y-3 mb-4 max-h-[400px] overflow-y-auto"
        aria-live="polite"
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`p-2 rounded ${
              m.role === "user" ? "bg-accentCyan/10" : "bg-midnight/50"
            }`}
          >
            {m.role === "bot" ? (
              <p data-testid="chat-reply">{m.text}</p>
            ) : (
              <p>{m.text}</p>
            )}

            {/* Citations */}
            {m.role === "bot" && m.citations && m.citations.length > 0 && (
              <div className="mt-2 space-y-2">
                {m.citations.map((c, i) => (
                  <div key={i} role="article">
                    <p className="font-bold">{c.title}</p>
                    <p className="text-sm text-textMuted">{c.snippet}</p>
                    {c.source_link && (
                      <a
                        href={c.source_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accentCyan hover:underline"
                      >
                        [Source]
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Error message */}
      {error && <p className="text-error mb-2">{error}</p>}

      {/* Input + send */}
      <div className="flex gap-2">
        <input
          aria-label="chat input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-grow bg-midnight border border-divider text-textPrimary p-2 rounded"
          placeholder="Type your question..."
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={isLoading}
          className="bg-accentCyan hover:bg-cyan-400 text-midnight px-4 py-2 rounded"
        >
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}
