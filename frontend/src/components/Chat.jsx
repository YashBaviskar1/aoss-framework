import { useState } from "react";
import { Send, Cpu, Bot, User, Loader2 } from "lucide-react";

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "system",
      content: "Welcome to AOSS Orchestrator. Enter a natural query to begin automation.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState(null);
  const [lastQuery, setLastQuery] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setLastQuery(input);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/get_commands", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ question: input, execute: true }),
      });

      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();

      setMessages((prev) => [...prev, { role: "agent", content: data }]);

      setLastResponse({
        results: data.plan.map((cmd) => ({
          command: cmd,
          status: "⏳ Pending",
          stdout: "",
        })),
      });
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { role: "agent", content: { plan: [] } }]);
      setLastResponse({
        results: [
          { command: "Error", status: "❌ Failed", stdout: err.message },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const Execute = async () => {
    if (!lastQuery) return;
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/agent", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ question: lastQuery, execute: true }),
      });

      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();

      setMessages((prev) => [...prev, { role: "agent", content: data }]);
      setLastResponse({ results: data.results });
    } catch (err) {
      console.error(err);
      setLastResponse({
        results: [
          { command: "Error", status: "❌ Failed", stdout: err.message },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-base-100 flex">
      {/* Left: Chat Section */}
      <div className="w-1/2 flex flex-col border-r border-base-300">
        {/* Header */}
        <div className="bg-base-200 border-b border-base-300 px-6 py-4 flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Cpu className="w-5 h-5 text-primary-content" />
          </div>
          <h1 className="font-semibold text-base-content">
            AOSS Orchestrator Chat
          </h1>
        </div>

        {/* Chat Messages: scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4" style={{ maxHeight: "calc(100vh - 160px)" }}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role !== "user" && (
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                  {msg.role === "system" ? (
                    <Bot className="w-5 h-5 text-primary" />
                  ) : (
                    <Cpu className="w-5 h-5 text-primary" />
                  )}
                </div>
              )}
              <div
                className={`max-w-md px-4 py-3 rounded-2xl text-sm shadow ${
                  msg.role === "user"
                    ? "bg-primary text-primary-content rounded-br-none"
                    : "bg-base-200 text-white rounded-bl-none"
                }`}
              >
                {msg.role === "agent" && msg.content.plan ? (
                  <div className="flex flex-col space-y-2">
                    {msg.content.plan.map((cmd, i) => (
                      <div key={i} className="flex items-center">
                        <span className="text-primary/70 mr-2">→</span>
                        <span className="font-mono">{cmd}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  msg.content
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-primary" />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-base-content/70 text-sm px-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Agents are processing your query…
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-base-300 bg-base-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <input
              type="text"
              className="flex-1 input input-bordered rounded-full text-white placeholder-white"
              placeholder='e.g. "Install Python"'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
            <button
              onClick={handleSend}
              className="btn btn-primary rounded-full px-5"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Right: Execution Summary Table */}
      <div className="w-1/2 p-6 flex flex-col">
        <h2 className="text-lg font-semibold mb-4">Execution Summary</h2>

        {/* Table: scrollable */}
        <div className="flex-1 overflow-y-auto" style={{ maxHeight: "calc(100vh - 140px)" }}>
          <table className="table-auto w-full border border-base-300">
            <thead className="bg-base-200">
              <tr>
                <th className="border px-4 py-2 text-left">Execution Series</th>
                <th className="border px-4 py-2 text-left">Status</th>
                <th className="border px-4 py-2 text-left">Server Logging</th>
              </tr>
            </thead>
            <tbody>
              {lastResponse?.results?.map((res, idx) => (
                <tr key={idx} className="odd:bg-base-100 even:bg-base-200">
                  <td className="border px-4 py-2 font-mono">{res.command}</td>
                  <td className="border px-4 py-2">{res.status}</td>
                  <td className="border px-4 py-2">
                    <pre className="whitespace-pre-wrap">{res.stdout}</pre>
                    {res.stderr && (
                      <pre className="whitespace-pre-wrap text-red-400">
                        {res.stderr}
                      </pre>
                    )}
                  </td>
                </tr>
              ))}
              {!lastResponse && (
                <tr>
                  <td className="border px-4 py-2 text-center" colSpan={3}>
                    No commands executed yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Execute Button */}
        <div className="mt-4 flex gap-3">
          <button className="btn btn-primary" onClick={Execute}>
            Execute
          </button>
        </div>
      </div>
    </div>
  );
}
