"use client";

import { useEffect, useState } from "react";
import { agentAPI, type Agent, type AgentCreatePayload } from "@/lib/api";
import { getAgentColor, formatRelativeTime } from "@/lib/utils";
import { Bot, Plus, Pencil, Trash2, X, Power } from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAgents = async () => {
    try { setAgents(await agentAPI.list()); }
    catch { } finally { setLoading(false); }
  };

  useEffect(() => { fetchAgents(); }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this agent?")) return;
    await agentAPI.delete(id);
    fetchAgents();
  };

  const handleEdit = (agent: Agent) => {
    setEditingAgent(agent);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingAgent(null);
    fetchAgents();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">AI Agents</h1>
          <p className="text-sm text-muted-foreground mt-1">Configure and manage orchestration agents</p>
        </div>
        <button
          onClick={() => { setEditingAgent(null); setShowForm(true); }}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" /> New Agent
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading agents...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {agents.map((agent) => (
            <div key={agent.id} className="rounded-lg border border-border bg-card p-5 space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: getAgentColor(agent.role) + "20" }}>
                    <Bot className="w-5 h-5" style={{ color: getAgentColor(agent.role) }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium">{agent.name}</h3>
                    <p className="text-xs text-muted-foreground">{agent.role.replace(/_/g, " ")}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full ${agent.is_active ? "bg-emerald-500" : "bg-gray-500"}`} />
                  <button onClick={() => handleEdit(agent)} className="p-1.5 hover:bg-accent rounded transition-colors">
                    <Pencil className="w-3.5 h-3.5 text-muted-foreground" />
                  </button>
                  <button onClick={() => handleDelete(agent.id)} className="p-1.5 hover:bg-destructive/20 rounded transition-colors">
                    <Trash2 className="w-3.5 h-3.5 text-red-400" />
                  </button>
                </div>
              </div>

              <p className="text-xs text-muted-foreground line-clamp-2">{agent.system_prompt || "No system prompt configured"}</p>

              <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                <span className="px-1.5 py-0.5 rounded bg-accent">{agent.model}</span>
                {agent.config?.tools && <span>{agent.config.tools.length} tools</span>}
                {agent.config?.channels && <span>{agent.config.channels.join(", ")}</span>}
                {agent.created_at && <span>Created {formatRelativeTime(agent.created_at)}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Agent Form Dialog */}
      {showForm && (
        <AgentFormDialog agent={editingAgent} onClose={handleFormClose} />
      )}
    </div>
  );
}

function AgentFormDialog({ agent, onClose }: { agent: Agent | null; onClose: () => void }) {
  const [form, setForm] = useState<AgentCreatePayload>({
    name: agent?.name || "",
    role: agent?.role || "customer_support",
    system_prompt: agent?.system_prompt || "",
    model: agent?.model || "gpt-4o",
    config: agent?.config || {},
    is_active: agent?.is_active ?? true,
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (agent) {
        await agentAPI.update(agent.id, form);
      } else {
        await agentAPI.create(form);
      }
      onClose();
    } catch (err) { console.error(err); }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-card border border-border rounded-lg w-full max-w-lg p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{agent ? "Edit Agent" : "Create Agent"}</h2>
          <button onClick={onClose} className="p-1 hover:bg-accent rounded"><X className="w-4 h-4" /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Role</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option value="customer_support">Customer Support</option>
                <option value="fraud_detection">Fraud Detection</option>
                <option value="payment_verification">Payment Verification</option>
                <option value="escalation_resolution">Escalation Resolution</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">System Prompt</label>
            <textarea value={form.system_prompt} onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
              rows={4} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Model</label>
              <select value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4.1">GPT-4.1</option>
              </select>
            </div>
            <div className="flex items-center gap-2 pt-5">
              <label className="text-xs text-muted-foreground">Active</label>
              <button type="button" onClick={() => setForm({ ...form, is_active: !form.is_active })}
                className={`w-10 h-5 rounded-full transition-colors ${form.is_active ? "bg-emerald-500" : "bg-gray-600"}`}>
                <span className={`block w-4 h-4 rounded-full bg-white transform transition-transform ${form.is_active ? "translate-x-5" : "translate-x-0.5"}`} />
              </button>
            </div>
          </div>

          <button type="submit" disabled={saving}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {saving ? "Saving..." : agent ? "Update Agent" : "Create Agent"}
          </button>
        </form>
      </div>
    </div>
  );
}
