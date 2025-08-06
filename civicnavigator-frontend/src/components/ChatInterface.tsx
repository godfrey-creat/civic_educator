import { useState } from "react";
import { sendChatMessage } from "../utils/api";
import type { ChatMessage, Citation } from "../types";

interface Props {
  role: "resident" | "staff";
}

export default function ChatInterface({ role }: Props) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setIsLoading(true);
    try {
      const data = await sendChatMessage(input, role);
      const newMessage: ChatMessage = {
        user: input,
        bot: data.reply,
        citations: data.citations,
        confidence: data.confidence,
      };
      setMessages((prev) => [...prev, newMessage]);
      setInput("");
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          user: input,
          bot: "⚠️ Unable to process request.",
          citations: [],
          confidence: 0,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-panel border border-divider text-textPrimary rounded-xl p-4 mb-6 shadow">
      <h2 className="text-2xl font-semibold mb-4">Chat</h2>
      <div className="h-64 overflow-y-auto mb-4 p-3 border border-divider rounded bg-midnight">
        {messages.map((msg, idx) => (
          <div key={idx} className="mb-4">
            <p><strong>You:</strong> {msg.user}</p>
            <p><strong>Bot:</strong> {msg.bot}</p>
            {msg.citations?.length > 0 && (
              <ul className="list-decimal ml-6 text-sm text-textMuted">
                {msg.citations.map((c: Citation, i: number) => (
                  <li key={i}>
                    <span className="font-medium">{c.title}</span>: {c.snippet}
                    {c.source_link && (
                      <a
                        href={c.source_link}
                        target="_blank"
                        rel="noreferrer"
                        className="text-accentCyan ml-1"
                      >
                        [Source]
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-grow bg-midnight border border-divider text-textPrimary p-2 rounded-l"
          placeholder="Ask about services..."
          aria-label="chat input"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-accentPink hover:bg-pink-500 text-white px-4 py-2 rounded-r"
        >
          {isLoading ? "Loading..." : "Send"}
        </button>
      </form>
    </div>
  );
}
