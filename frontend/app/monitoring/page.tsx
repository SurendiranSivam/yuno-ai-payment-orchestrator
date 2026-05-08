"use client";

import { useEffect, useState, useCallback } from "react";
import { monitoringAPI, type WorkflowEvent } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import { useAppStore } from "@/stores/app-store";
import { formatTime, getStatusColor, getAgentColor } from "@/lib/utils";
import { Activity, Radio } from "lucide-react";

export default function MonitoringPage() {
  const [historicalEvents, setHistoricalEvents] = useState<WorkflowEvent[]>([]);
  const { liveEvents, addLiveEvent } = useAppStore();

  const handleWsEvent = useCallback((event: any) => {
    if (event.type === "workflow_event" && event.data) {
      addLiveEvent(event.data);
    }
  }, [addLiveEvent]);

  const { isConnected } = useWebSocket(handleWsEvent);

  useEffect(() => {
    monitoringAPI.events(100).then(setHistoricalEvents).catch(() => {});
  }, []);

  const allEvents = [...liveEvents, ...historicalEvents].slice(0, 100);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Live Monitoring</h1>
          <p className="text-sm text-muted-foreground mt-1">Real-time agent execution event stream</p>
        </div>
        <div className="flex items-center gap-2">
          <Radio className={`w-4 h-4 ${isConnected ? "text-emerald-400 animate-pulse" : "text-red-400"}`} />
          <span className="text-xs text-muted-foreground">{isConnected ? "Connected" : "Disconnected"}</span>
        </div>
      </div>

      {/* Event Stream */}
      <div className="rounded-lg border border-border bg-card">
        {/* Header */}
        <div className="px-4 py-3 border-b border-border flex items-center gap-4 text-[10px] text-muted-foreground uppercase tracking-wider">
          <span className="w-20">Time</span>
          <span className="w-48">Agent</span>
          <span className="w-24">Event</span>
          <span className="flex-1">Message</span>
        </div>

        {/* Events */}
        <div className="max-h-[600px] overflow-y-auto divide-y divide-border/50">
          {allEvents.length === 0 ? (
            <div className="py-16 text-center">
              <Activity className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">No events yet</p>
              <p className="text-xs text-muted-foreground mt-1">Trigger a workflow from the dashboard to see live events</p>
            </div>
          ) : (
            allEvents.map((event, i) => {
              const roleKey = event.agent_name?.toLowerCase().replace(/agent$/i, "").replace(/ /g, "_").trim() || "";
              return (
                <div key={event.id || i} className="px-4 py-2.5 flex items-start gap-4 hover:bg-accent/30 transition-colors text-xs">
                  <span className="w-20 text-muted-foreground font-mono shrink-0">
                    {event.created_at ? formatTime(event.created_at) : "—"}
                  </span>
                  <div className="w-48 flex items-center gap-2 shrink-0">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: getAgentColor(roleKey) }} />
                    <span className="font-medium text-foreground truncate">{event.agent_name}</span>
                  </div>
                  <span className={`w-24 shrink-0`}>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getStatusColor(
                      event.event_type === "node_complete" ? "completed" :
                      event.event_type === "error" ? "failed" :
                      event.event_type === "node_start" ? "running" : "pending"
                    )}`}>
                      {event.event_type}
                    </span>
                  </span>
                  <span className="flex-1 text-muted-foreground">{event.message}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
