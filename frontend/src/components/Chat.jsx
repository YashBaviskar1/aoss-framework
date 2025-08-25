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

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    // Fake agent response simulating backend structure
    setTimeout(() => {
      const response = {
        plan: [
          "sudo apt install htop",
          "htop"
        ],
        results: [
          {
            command: "sudo apt install htop",
            status: "✅ Success",
            stdout: "Reading package lists...\nBuilding dependency tree..."
          },
          {
            command: "htop",
            status: "❌ Failed",
            stdout: "Terminal cannot launch htop properly."
          }
        ]
      };

      const agentMsg = {
        role: "agent",
        content: response
      };

      setMessages((prev) => [...prev, agentMsg]);
      setLastResponse(response);
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-base-100 flex">
      {/* Left: Chat Window */}
      <div className="w-1/2 flex flex-col border-r border-base-300">
        {/* Header */}
        <div className="bg-base-200 border-b border-base-300 px-6 py-4 flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Cpu className="w-5 h-5 text-primary-content" />
          </div>
          <h1 className="font-semibold text-base-content">AOSS Orchestrator Chat</h1>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
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

        {/* Input Box */}
        <div className="border-t border-base-300 bg-base-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <input
              type="text"
              className="flex-1 input input-bordered rounded-full text-white placeholder-white"
              placeholder='e.g. "Scale web servers to handle 5x load"'
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

      {/* Right: Output Table */}
      <div className="w-1/2 p-6 overflow-y-auto">
        <h2 className="text-lg font-semibold mb-4">Execution Summary</h2>
        <table className="table-auto w-full border border-base-300">
          <thead className="bg-base-200">
            <tr>
              <th className="border px-4 py-2 text-left">Execution Series</th>
              <th className="border px-4 py-2 text-left">Status</th>
              <th className="border px-4 py-2 text-left">Server Logging </th>
            </tr>
          </thead>
          <tbody>
            {lastResponse?.results?.map((res, idx) => (
              <tr key={idx} className="odd:bg-base-100 even:bg-base-200">
                <td className="border px-4 py-2 font-mono">{res.command}</td>
                <td className="border px-4 py-2">{res.status}</td>
                <td className="border px-4 py-2">
                  <pre className="whitespace-pre-wrap">{res.stdout}</pre>
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
    </div>
  );
}
