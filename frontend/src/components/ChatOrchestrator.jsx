import { Link, useLocation } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

import { useState, useEffect, useRef } from 'react';
import { useUser } from '@clerk/clerk-react';
import {
    LayoutDashboard,
    Server,
    ShieldCheck,
    BarChart3,
    Bot,
    Cpu,
    Send,
    Play,
    CheckCircle,
    XCircle,
    TerminalSquare,
    Loader2,
    BrainCircuit,
    Database,
    Globe,
    Lock
} from 'lucide-react';

// --- Helper component for Sidebar Links ---
function NavLink({ to, icon: Icon, children }) {
    const location = useLocation();
    const isActive = location.pathname === to;

    return (
        <li>
            <Link
                to={to}
                className={`
          flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors duration-200
          ${isActive
                        ? 'bg-primary/10 text-primary font-semibold'
                        : 'text-base-content/70 hover:bg-base-200 hover:text-primary'
                    }
        `}
            >
                <Icon className="w-5 h-5" />
                <span>{children}</span>
            </Link>
        </li>
    );
}

export default function ChatOrchestrator() {
    const { user, isLoaded } = useUser();
    const [servers, setServers] = useState([]);
    const [selectedServerId, setSelectedServerId] = useState('');
    const [query, setQuery] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [planning, setPlanning] = useState(false);
    const [executing, setExecuting] = useState(false);

    // --- NEW STATE FOR AGENTIC FEATURES ---
    const [selectedModel, setSelectedModel] = useState('llama-3.3-70b-versatile');
    const [selectedAgent, setSelectedAgent] = useState('general');

    const [showBrainPanel, setShowBrainPanel] = useState(true);
    const bottomRef = useRef(null);

    const AGENTS = [
        { id: 'general', name: 'General SRE', icon: Bot, color: 'text-blue-500' },
        { id: 'network', name: 'NetOps Specialist', icon: Globe, color: 'text-green-500' },
        { id: 'database', name: 'DB Administrator', icon: Database, color: 'text-yellow-500' },
        { id: 'security', name: 'SecOps Auditor', icon: Lock, color: 'text-red-500' },
    ];

    const MODELS = [
        { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 (70B)' },
        { id: 'llama3-70b-8192', name: 'Llama 3 (70B)' },
        { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B' },
        { id: 'gemma-7b-it', name: 'Gemma 7B' },
    ];

    // Fetch servers on load
    useEffect(() => {
        if (isLoaded && user) {
            fetch(`http://localhost:8000/api/dashboard/${user.id}`)
                .then(res => res.json())
                .then(data => {
                    setServers(data.servers);
                    if (data.servers.length > 0) {
                        setSelectedServerId(data.servers[0].id);
                    }
                })
                .catch(err => console.error("Error fetching servers:", err));
        }
    }, [isLoaded, user]);

    // Scroll to bottom
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatHistory, planning, executing]);

    // Auto-open Brain Panel when healing starts
    useEffect(() => {
        if (!chatHistory.length) return;
        const lastMsg = chatHistory[chatHistory.length - 1];
        if (lastMsg.type === 'result' && lastMsg.result.execution_results) {
            const lastEvent = lastMsg.result.execution_results[lastMsg.result.execution_results.length - 1];
            if (lastEvent && lastEvent.type === 'healing_start') {
                setShowBrainPanel(true);
            }
        }
    }, [chatHistory]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!query.trim() || !selectedServerId) return;

        const currentQuery = query;
        const currentAgent = AGENTS.find(a => a.id === selectedAgent); // Get details for UI
        setQuery('');

        // Add User Message with Agent Metadata
        setChatHistory(prev => [...prev, {
            type: 'user',
            content: currentQuery,
            agentUsed: currentAgent
        }]);

        setPlanning(true);

        try {
            const res = await fetch('http://localhost:8000/api/chat/plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    serverId: selectedServerId,
                    query: currentQuery,
                    // PASS SELECTED OPTIONS
                    model: selectedModel,
                    agent_type: selectedAgent
                })
            });
            const data = await res.json();

            if (data.plan) {
                setChatHistory(prev => [...prev, {
                    type: 'plan',
                    query: currentQuery,
                    plan: data.plan,
                    agentUsed: currentAgent // Track who generated this
                }]);
            } else {
                setChatHistory(prev => [...prev, { type: 'error', content: "Failed to generate plan." }]);
            }
        } catch (err) {
            setChatHistory(prev => [...prev, { type: 'error', content: err.message }]);
        } finally {
            setPlanning(false);
        }
    };

    const handleExecutePlan = async (originalQuery, plan) => {
        setExecuting(true);

        // 1. Create a placeholder result message immediately
        const placeholderId = Date.now();
        setChatHistory(prev => [...prev, {
            type: 'result',
            id: placeholderId,
            result: {
                status: 'Running',
                execution_results: [],
                agent_summary: null
            }
        }]);

        try {
            const res = await fetch('http://localhost:8000/api/chat/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ serverId: selectedServerId, query: originalQuery, plan: plan })
            });

            if (!res.body) throw new Error("No response body");

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                // Split by newline to get JSON objects
                const lines = buffer.split('\n');
                // Keep the last partial line in buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);

                        // UPDATE UI STATE BASED ON EVENT
                        setChatHistory(prev => prev.map(msg => {
                            if (msg.id !== placeholderId) return msg;

                            // Mutate copy of result for this message
                            const newResult = { ...msg.result };

                            switch (event.type) {
                                case 'step_start':
                                    // Optionally show "running" state for a step, 
                                    // but we usually just append when result comes. 
                                    // Could add a "current_step" indicator if we wanted.
                                    break;

                                case 'step_result':
                                case 'error':
                                    newResult.execution_results = [...(newResult.execution_results || []), event.result];
                                    break;

                                case 'healing_start':
                                    newResult.execution_results = [...(newResult.execution_results || []), {
                                        type: 'healing_start',
                                        stderr: event.stderr
                                    }];
                                    break;

                                case 'healing_plan':
                                    newResult.execution_results = [...(newResult.execution_results || []), {
                                        type: 'healing_plan',
                                        stdout: event.stdout
                                    }];
                                    break;

                                case 'agent_summary':
                                    newResult.agent_summary = event.content;
                                    break;

                                case 'complete':
                                    newResult.status = event.final_status;
                                    break;
                            }
                            return { ...msg, result: newResult };
                        }));

                    } catch (e) {
                        console.error("Error parsing stream line:", line, e);
                    }
                }
            }

        } catch (err) {
            setChatHistory(prev => [...prev, { type: 'error', content: "Execution failed: " + err.message }]);
        } finally {
            setExecuting(false);
        }
    };

    const renderBrainActivity = () => {
        // Collect all healing events from all messages
        const activity = [];
        chatHistory.forEach(msg => {
            if (msg.type === 'result' && msg.result.execution_results) {
                // Determine if this execution is currently active (running)
                // We don't have a direct "active" flag on the msg, but we can verify status
                const isRunning = msg.result.status === "Running";

                // Add execution steps as "activity" too if we want, or just healing?
                // The user wants to see "execution output of each step"
                // Let's also add normal steps to the "Brain" panel ONLY IF RUNNING, to show progress?
                // Or keep Brain panel for "Brain" things (healing/summary) and let the main chat show output.
                // Re-reading user request: "see execution output of each sep... like which step is it at"

                // The main chat ALREADY shows execution output in the `msg.type === 'result'` block.
                // By updating `execution_results` live, the Main Chat view will auto-update!
                // So "Brain Panel" can stay focused on "Thoughts", while main view shows "Console".

                msg.result.execution_results.forEach(res => {
                    if (res.type === 'healing_start' || res.type === 'healing_plan') {
                        activity.push(res);
                    }
                });
            }
        });

        if (activity.length === 0) return (
            <div className="flex flex-col items-center justify-center h-full text-base-content/40 space-y-4">
                <BrainCircuit className="w-12 h-12 opacity-20" />
                <p className="text-sm text-center px-4">Agent Brain is idle.<br />Execute a command to trigger reasoning.</p>
            </div>
        );

        return (
            <div className="space-y-4 p-4">
                {activity.map((item, idx) => (
                    <div key={idx} className="bg-base-100 border border-base-300 rounded-lg p-3 shadow-sm text-sm animate-in fade-in slide-in-from-right duration-500">
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-base-200">
                            {item.type === 'healing_start'
                                ? <Loader2 className="w-4 h-4 text-warning animate-spin" />
                                : <CheckCircle className="w-4 h-4 text-success" />
                            }
                            <span className="font-bold opacity-80">{item.type === 'healing_start' ? 'Failure Detected' : 'Fix Generated'}</span>
                        </div>
                        {item.type === 'healing_start' && (
                            <div className="space-y-2">
                                <p className="text-warning-content bg-warning/10 p-2 rounded text-xs">{item.stderr}</p>
                                <div className="text-xs opacity-60 italic">Consulting Knowledge Base...</div>
                            </div>
                        )}
                        {item.type === 'healing_plan' && (
                            <div className="bg-neutral text-neutral-content p-2 rounded font-mono text-xs overflow-x-auto">
                                {item.stdout}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="flex min-h-screen bg-base-200">
            {/* ===== Sidebar (Copied from Dashboard) ===== */}
            <aside className="w-64 bg-base-100 text-base-content flex flex-col border-r border-base-300/50 pt-24 hidden md:flex">
                <div className="flex items-center space-x-3 px-6 py-5 border-b border-base-300/50">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                        <Cpu className="w-6 h-6 text-primary" />
                    </div>
                    <span className="text-xl font-bold">AOSS</span>
                </div>
                <nav className="flex-1 px-4 py-4">
                    <ul className="space-y-2">
                        <NavLink to="/dashboard" icon={LayoutDashboard}>Dashboard</NavLink>
                        <NavLink to="/services" icon={Server}>Services</NavLink>
                        <NavLink to="/compliance" icon={ShieldCheck}>Compliance</NavLink>
                        <NavLink to="/monitoring" icon={BarChart3}>Monitoring</NavLink>
                        <NavLink to="/chat" icon={Bot}>Orchestrate</NavLink>
                    </ul>
                </nav>
                <div className="px-6 py-4 border-t border-base-300/50">
                    <div className="flex items-center space-x-3">
                        <div className="avatar placeholder">
                            <div className="bg-neutral-focus text-neutral-content rounded-full w-10">
                                <span>{user?.firstName?.[0] || 'A'}</span>
                            </div>
                        </div>
                        <div>
                            <p className="font-semibold text-sm">{user?.fullName || 'User'}</p>
                            <p className="text-xs text-base-content/60">Admin</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col h-screen overflow-hidden pt-20 relative">

                {/* Header */}
                <header className="bg-base-100 border-b border-base-300 px-6 py-4 flex justify-between items-center shadow-sm z-10 shrink-0">
                    <div className="flex items-center gap-4">
                        <Bot className="w-8 h-8 text-primary" />
                        <div>
                            <h1 className="text-lg font-bold">Agent Orchestrator</h1>
                            <p className="text-xs text-base-content/60">Multi-Agent SRE System</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* 1. Agent Selector */}
                        <div className="dropdown dropdown-end">
                            <label tabIndex={0} className="btn btn-sm btn-ghost border border-base-300 gap-2">
                                {AGENTS.find(a => a.id === selectedAgent)?.icon &&
                                    (() => {
                                        const Icon = AGENTS.find(a => a.id === selectedAgent).icon;
                                        return <Icon className={`w-4 h-4 ${AGENTS.find(a => a.id === selectedAgent).color}`} />;
                                    })()
                                }
                                {AGENTS.find(a => a.id === selectedAgent)?.name}
                            </label>
                            <ul tabIndex={0} className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                                <li className="menu-title text-xs opacity-50">Select Agent Persona</li>
                                {AGENTS.map(agent => (
                                    <li key={agent.id}>
                                        <a onClick={() => setSelectedAgent(agent.id)} className={selectedAgent === agent.id ? 'active' : ''}>
                                            <agent.icon className={`w-4 h-4 ${agent.color}`} />
                                            {agent.name}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <select
                            className="select select-bordered select-sm text-xs w-40"
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                        >
                            {MODELS.map(m => (
                                <option key={m.id} value={m.id}>{m.name}</option>
                            ))}
                        </select>

                        <select
                            className="select select-bordered select-sm w-40 font-mono"
                            value={selectedServerId}
                            onChange={(e) => { setSelectedServerId(e.target.value); setChatHistory([]); }}
                        >
                            <option disabled value="">Target Server</option>
                            {servers.map(s => (
                                <option key={s.id} value={s.id}>{s.server_tag}</option>
                            ))}
                        </select>

                        <button
                            className={`btn btn-sm btn-ghost border border-base-300 gap-2 ${showBrainPanel ? 'bg-primary/10 text-primary' : ''}`}
                            onClick={() => setShowBrainPanel(!showBrainPanel)}
                            title="Toggle Agent Brain"
                        >
                            <BrainCircuit className="w-4 h-4" />
                            <span className="hidden lg:inline">{showBrainPanel ? 'Hide Brain' : 'Show Brain'}</span>
                        </button>
                    </div>
                </header>

                {/* Split View Content */}
                <div className="flex-1 flex overflow-hidden">

                    {/* Left: Chat Area */}
                    <div className="flex-1 flex flex-col border-r border-base-300 bg-base-200">
                        <div className="flex-1 overflow-y-auto p-8 space-y-6">
                            {/* Chat History Rendering... */}
                            {chatHistory.length === 0 && (
                                <div className="h-full flex flex-col items-center justify-center text-base-content/40 space-y-4">
                                    <div className="flex -space-x-4">
                                        <div className="w-12 h-12 rounded-full bg-blue-100 border-2 border-base-200 flex items-center justify-center"><Bot className="w-6 h-6 text-blue-500" /></div>
                                        <div className="w-12 h-12 rounded-full bg-green-100 border-2 border-base-200 flex items-center justify-center"><Globe className="w-6 h-6 text-green-500" /></div>
                                        <div className="w-12 h-12 rounded-full bg-yellow-100 border-2 border-base-200 flex items-center justify-center"><Database className="w-6 h-6 text-yellow-500" /></div>
                                    </div>
                                    <p>Select a specialized agent and start orchestrating.</p>
                                </div>
                            )}

                            {chatHistory.map((msg, idx) => (
                                <div key={idx} className={`flex w-full ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    {msg.type === 'user' && (
                                        <div className="flex flex-col items-end gap-1 max-w-[80%]">
                                            <div className="bg-primary text-primary-content rounded-xl rounded-tr-none px-6 py-4 shadow-md">
                                                <p>{msg.content}</p>
                                            </div>
                                            <span className="text-[10px] uppercase tracking-wider opacity-50 mr-2 flex items-center gap-1">
                                                Asking {msg.agentUsed?.name}
                                            </span>
                                        </div>
                                    )}

                                    {msg.type === 'plan' && (
                                        <div className="bg-base-100 border border-base-300 rounded-xl rounded-tl-none p-0 max-w-[80%] shadow-md w-full md:w-2/3">
                                            <div className="bg-base-200 px-6 py-3 rounded-t-xl border-b border-base-300 flex justify-between items-center">
                                                <span className="font-semibold flex items-center gap-2">
                                                    {msg.agentUsed?.icon && <msg.agentUsed.icon className={`w-4 h-4 ${msg.agentUsed.color}`} />}
                                                    {msg.agentUsed?.name || 'Agent'} Plan
                                                </span>
                                                <span className="text-xs badge badge-ghost">{msg.plan.length} steps</span>
                                            </div>
                                            <div className="p-4 space-y-3">
                                                {msg.plan.map((step, i) => (
                                                    <div key={i} className="flex gap-3 text-sm">
                                                        <div className="w-6 h-6 rounded-full bg-base-300 flex items-center justify-center shrink-0 text-xs font-mono">
                                                            {step.step}
                                                        </div>
                                                        <div className="flex-1">
                                                            <code className="bg-neutral text-neutral-content px-2 py-1 rounded text-xs block mb-1">
                                                                {step.command}
                                                            </code>
                                                            <p className="text-base-content/70 text-xs">{step.description}</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="p-4 border-t border-base-300 bg-base-50/50 rounded-b-xl flex justify-end gap-2">
                                                <button className="btn btn-primary btn-sm gap-2" onClick={() => handleExecutePlan(msg.query, msg.plan)} disabled={executing}>
                                                    {executing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                                                    {executing ? 'Executing...' : 'Execute Plan'}
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {msg.type === 'result' && (
                                        <div className="flex flex-col gap-2 w-full md:w-2/3 max-w-[80%]">
                                            {/* Execution Log Block */}
                                            <div className="bg-base-100 border border-base-300 rounded-xl rounded-tl-none p-0 shadow-md">
                                                <div className="bg-success/10 text-success-content px-6 py-3 rounded-t-xl border-b border-success/20 flex justify-between items-center">
                                                    <span className="font-semibold flex items-center gap-2">
                                                        {msg.result.status === 'Running' ? <Loader2 className="w-4 h-4 animate-spin" /> : <TerminalSquare className="w-4 h-4" />}
                                                        {msg.result.status === 'Running' ? 'Executing...' : 'Execution Complete'}
                                                    </span>
                                                    <span className={`badge ${msg.result.status === 'Success' ? 'badge-success' :
                                                        msg.result.status === 'Running' ? 'badge-warning' : 'badge-error'
                                                        }`}>{msg.result.status}</span>
                                                </div>
                                                <div className="p-4 space-y-2 max-h-60 overflow-y-auto">
                                                    {msg.result.execution_results && msg.result.execution_results.map((res, i) => (
                                                        !['healing_start', 'healing_plan'].includes(res.type) && (
                                                            <div key={i} className="text-xs border-b border-base-200 pb-2 last:border-0">
                                                                <div className="flex justify-between font-mono mb-1">
                                                                    <span className="font-bold opacity-70">$ {res.command || 'Unknown execution step'}</span>
                                                                    <span className={(res.exit_code === 0) ? "text-success" : "text-error"}>
                                                                        {res.exit_code === 0 ? "OK" : `ERR (${res.exit_code ?? '?'})`}
                                                                    </span>
                                                                </div>
                                                                {res.error && <div className="text-error font-semibold px-2">System Error: {res.error}</div>}

                                                                {(res.stdout || res.stderr) && (
                                                                    <details className="group">
                                                                        <summary className="cursor-pointer text-xs opacity-50 hover:opacity-100 select-none flex items-center gap-1">
                                                                            <span>View Output</span>
                                                                            <span className="group-open:rotate-90 transition-transform">▸</span>
                                                                        </summary>
                                                                        <div className="mt-2 pl-2 border-l-2 border-base-300">
                                                                            {res.stdout && (
                                                                                <pre className="text-base-content/60 overflow-x-auto whitespace-pre-wrap max-h-32 text-[10px] bg-base-200/50 p-1 rounded">
                                                                                    {res.stdout.length > 1000 ? res.stdout.substring(0, 1000) + "... (truncated)" : res.stdout}
                                                                                </pre>
                                                                            )}
                                                                            {res.stderr && (
                                                                                <pre className="text-error/80 overflow-x-auto whitespace-pre-wrap max-h-32 text-[10px] bg-error/5 p-1 rounded mt-1">
                                                                                    {res.stderr}
                                                                                </pre>
                                                                            )}
                                                                        </div>
                                                                    </details>
                                                                )}
                                                            </div>
                                                        )
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Agent Interpretation Block (Stacked Below) */}
                                            {msg.result.agent_summary && (
                                                <div className="bg-base-200 border border-primary/20 rounded-xl rounded-tl-none p-0 shadow-md animate-in fade-in duration-700 delay-150">
                                                    <div className="bg-primary/5 px-6 py-3 rounded-t-xl border-b border-primary/10 flex items-center gap-2">
                                                        <Bot className="w-4 h-4 text-primary" />
                                                        <span className="font-semibold text-primary text-sm">Agent Interpretation</span>
                                                    </div>
                                                    <div className="p-4 text-sm bg-base-200/50 rounded-b-xl">
                                                        <article className="prose prose-sm max-w-none prose-headings:text-base-content prose-p:text-base-content/70 prose-strong:text-base-content/90 prose-code:text-primary prose-code:bg-primary/10 prose-code:px-1 prose-code:rounded">
                                                            <ReactMarkdown>{msg.result.agent_summary}</ReactMarkdown>
                                                        </article>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {msg.type === 'error' && (
                                        <div className="bg-error/10 text-error rounded-xl px-6 py-4 max-w-[80%] border border-error/20 flex gap-3">
                                            <XCircle className="w-6 h-6 shrink-0" />
                                            <p>{msg.content}</p>
                                        </div>
                                    )}
                                </div>
                            ))}
                            {planning && (
                                <div className="flex justify-start w-full">
                                    <div className="bg-base-100 text-base-content border border-base-300 rounded-xl rounded-tl-none px-6 py-4 shadow-sm flex items-center gap-3">
                                        <Loader2 className="w-5 h-5 animate-spin text-primary" />
                                        <span>{AGENTS.find(a => a.id === selectedAgent)?.name} is thinking...</span>
                                    </div>
                                </div>
                            )}
                            <div ref={bottomRef} />
                        </div>
                        {/* Input Area */}
                        <div className="p-4 bg-base-100 border-t border-base-300 mt-auto">
                            <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative">
                                <input
                                    type="text"
                                    className="input input-bordered w-full pr-12 shadow-sm focus:outline-none focus:ring-2 ring-primary/20"
                                    placeholder={selectedServerId ? `Ask the ${AGENTS.find(a => a.id === selectedAgent)?.name} to do something...` : "Select a server first"}
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    disabled={!selectedServerId || planning || executing}
                                />
                                <button type="submit" className="absolute right-2 top-2 btn btn-ghost btn-sm btn-circle text-primary" disabled={!selectedServerId || !query.trim() || planning || executing}>
                                    <Send className="w-5 h-5" />
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Right: Agent Brain Activity Panel */}
                    <div className={`border-l border-base-300/50 flex flex-col transition-all duration-300 ease-in-out bg-base-50 overflow-hidden ${showBrainPanel ? 'w-80 opacity-100' : 'w-0 opacity-0'}`} style={{ visibility: showBrainPanel ? 'visible' : 'hidden' }}>
                        <div className="px-4 py-3 border-b border-base-300/50 bg-base-100 flex items-center justify-between w-80">
                            <div className="flex items-center gap-2">
                                <BrainCircuit className="w-4 h-4 text-purple-600" />
                                <span className="font-semibold text-sm">Agent Brain</span>
                            </div>
                            <button onClick={() => setShowBrainPanel(false)} className="btn btn-ghost btn-xs btn-circle">
                                <XCircle className="w-3 h-3" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto w-80">
                            {renderBrainActivity()}
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
}
