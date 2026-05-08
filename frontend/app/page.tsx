"use client";

import { useEffect, useState, useCallback } from "react";
import { monitoringAPI, whatsappAPI, type DashboardStats, type WorkflowEvent } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import { useAppStore } from "@/stores/app-store";
import { formatTime, formatRelativeTime, getStatusColor, getAgentColor } from "@/lib/utils";
import {
  Bot, GitBranch, Activity, MessageSquare, Coins,
  CheckCircle, XCircle, Play, Send,
} from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [simulateMessage, setSimulateMessage] = useState("");
  const [sending, setSending] = useState(false);
  const { liveEvents, addLiveEvent } = useAppStore();

  // WebSocket for realtime events
  const handleWsEvent = useCallback((event: any) => {
    if (event.type === "workflow_event" && event.data) {
      addLiveEvent(event.data);
    }
    // Refresh stats on workflow completion
    if (event.type === "workflow_completed") {
      monitoringAPI.stats().then(setStats).catch(() => {});
    }
  }, [addLiveEvent]);

  const { isConnected } = useWebSocket(handleWsEvent);

  useEffect(() => {
    monitoringAPI.stats().then(setStats).catch(() => {});
    monitoringAPI.events(20).then(setEvents).catch(() => {});
  }, []);

  const handleSimulate = async () => {
    if (!simulateMessage.trim()) return;
    setSending(true);
    try {
      await whatsappAPI.simulate({ phone: "+1234567890", message: simulateMessage });
      setSimulateMessage("");
    } catch (e) { console.error(e); }
    setSending(false);
  };

  const allEvents = [...liveEvents, ...events].slice(0, 30);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Operations Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Real-time payment operations monitoring</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500" : "bg-red-500"}`} />
          <span className="text-muted-foreground">{isConnected ? "Live" : "Reconnecting..."}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Bot} label="Active Agents" value={stats?.total_agents ?? "—"} color="text-blue-400" />
        <StatCard icon={GitBranch} label="Workflows" value={stats?.total_workflows ?? "—"} color="text-purple-400" />
        <StatCard icon={Activity} label="Total Runs" value={stats?.total_runs ?? "—"} color="text-cyan-400"
          sub={stats ? `${stats.completed_runs} completed · ${stats.active_runs} active` : undefined} />
        <StatCard icon={Coins} label="Tokens Used" value={stats?.total_tokens_used?.toLocaleString() ?? "—"} color="text-amber-400" />
      </div>

      {/* Execution Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <MiniStat icon={Play} label="Running" value={stats.active_runs} color="text-blue-400" />
          <MiniStat icon={CheckCircle} label="Completed" value={stats.completed_runs} color="text-emerald-400" />
          <MiniStat icon={XCircle} label="Failed" value={stats.failed_runs} color="text-red-400" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Activity Feed */}
        <div className="lg:col-span-2 rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            Live Activity Feed
          </h2>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {allEvents.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No events yet. Trigger a workflow to see live activity.</p>
            ) : (
              allEvents.map((event, i) => (
                <div key={event.id || i} className="flex items-start gap-3 py-2 border-b border-border/50 last:border-0">
                  <span
                    className="w-2 h-2 rounded-full mt-1.5 shrink-0"
                    style={{ backgroundColor: getAgentColor(event.agent_name?.toLowerCase().replace(/agent$/i, "").replace(/ /g, "_").trim() || "") }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-foreground">{event.agent_name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getStatusColor(event.event_type === "node_complete" ? "completed" : event.event_type === "error" ? "failed" : "running")}`}>
                        {event.event_type}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5 truncate">{event.message}</p>
                  </div>
                  <span className="text-[10px] text-muted-foreground shrink-0">
                    {event.created_at ? formatTime(event.created_at) : "now"}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Simulate WhatsApp */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-emerald-400" />
            Simulate WhatsApp Message
          </h2>
          <p className="text-xs text-muted-foreground mb-3">
            Send a simulated customer message to trigger the full multi-agent orchestration pipeline.
          </p>
          <textarea
            value={simulateMessage}
            onChange={(e) => setSimulateMessage(e.target.value)}
            placeholder="e.g. My payment failed but amount was deducted from my account"
            className="w-full h-24 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring resize-none"
          />
          <button
            onClick={handleSimulate}
            disabled={sending || !simulateMessage.trim()}
            className="mt-3 w-full flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
            {sending ? "Sending..." : "Send Message"}
          </button>

          {/* Quick templates */}
          <div className="mt-4 space-y-2">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Quick Templates</p>
            {[
              "My payment failed but amount was deducted from my account",
              "I see an unauthorized charge of $299 on my card",
              "My refund has been pending for 7 days",
            ].map((tmpl, i) => (
              <button
                key={i}
                onClick={() => setSimulateMessage(tmpl)}
                className="w-full text-left text-xs text-muted-foreground hover:text-foreground px-2 py-1.5 rounded hover:bg-accent/50 transition-colors"
              >
                &quot;{tmpl}&quot;
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color, sub }: {
  icon: any; label: string; value: string | number; color: string; sub?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <p className="text-2xl font-semibold text-foreground">{value}</p>
      {sub && <p className="text-[10px] text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

function MiniStat({ icon: Icon, label, value, color }: {
  icon: any; label: string; value: number; color: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 flex items-center gap-3">
      <Icon className={`w-5 h-5 ${color}`} />
      <div>
        <p className="text-lg font-semibold">{value}</p>
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}
