"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { workflowAPI, workflowRunAPI, type Workflow, type WorkflowRun, type WorkflowRunDetail } from "@/lib/api";
import { formatTime, formatRelativeTime, getStatusColor, getAgentColor } from "@/lib/utils";
import { GitBranch, Clock, ChevronRight, Play } from "lucide-react";

// React Flow must be client-side only
const WorkflowCanvas = dynamic(() => import("@/components/workflows/WorkflowCanvas"), { ssr: false });

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [selectedRun, setSelectedRun] = useState<WorkflowRunDetail | null>(null);
  const [tab, setTab] = useState<"graph" | "runs">("graph");

  useEffect(() => {
    workflowAPI.list().then((wfs) => {
      setWorkflows(wfs);
      if (wfs.length > 0) setSelectedWorkflow(wfs[0]);
    }).catch(() => {});
    workflowRunAPI.list(10).then(setRuns).catch(() => {});
  }, []);

  const handleViewRun = async (runId: string) => {
    try {
      const detail = await workflowRunAPI.get(runId);
      setSelectedRun(detail);
      setTab("runs");
    } catch (e) { console.error(e); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Workflows</h1>
        <p className="text-sm text-muted-foreground mt-1">Visualize and manage orchestration workflows</p>
      </div>

      {/* Workflow Selector */}
      <div className="flex gap-3">
        {workflows.map((wf) => (
          <button key={wf.id} onClick={() => { setSelectedWorkflow(wf); setSelectedRun(null); }}
            className={`px-4 py-2 rounded-md text-sm border transition-colors ${
              selectedWorkflow?.id === wf.id ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:border-primary/50"
            }`}>
            <div className="flex items-center gap-2">
              <GitBranch className="w-3.5 h-3.5" />
              {wf.name}
              {wf.is_template && <span className="text-[9px] px-1.5 py-0.5 rounded bg-accent">Template</span>}
            </div>
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-border">
        <button onClick={() => setTab("graph")}
          className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === "graph" ? "border-primary text-primary" : "border-transparent text-muted-foreground"}`}>
          Workflow Graph
        </button>
        <button onClick={() => setTab("runs")}
          className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === "runs" ? "border-primary text-primary" : "border-transparent text-muted-foreground"}`}>
          Execution History
        </button>
      </div>

      {/* Content */}
      {tab === "graph" && selectedWorkflow && (
        <div className="rounded-lg border border-border bg-card" style={{ height: "500px" }}>
          <WorkflowCanvas graphDefinition={selectedWorkflow.graph_definition} />
        </div>
      )}

      {tab === "runs" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Runs List */}
          <div className="rounded-lg border border-border bg-card p-4 space-y-3">
            <h3 className="text-sm font-medium">Recent Runs</h3>
            {runs.length === 0 ? (
              <p className="text-xs text-muted-foreground py-4 text-center">No workflow runs yet</p>
            ) : runs.map((run) => (
              <button key={run.id} onClick={() => handleViewRun(run.id)}
                className={`w-full text-left p-3 rounded-md border transition-colors ${
                  selectedRun?.id === run.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/30"
                }`}>
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getStatusColor(run.status)}`}>{run.status}</span>
                  <span className="text-[10px] text-muted-foreground">{run.trigger_source}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1 truncate">{run.input_data?.customer_message || "—"}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{run.started_at ? formatRelativeTime(run.started_at) : ""}</p>
              </button>
            ))}
          </div>

          {/* Run Detail */}
          <div className="rounded-lg border border-border bg-card p-4 space-y-4">
            {selectedRun ? (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">Execution Timeline</h3>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getStatusColor(selectedRun.status)}`}>{selectedRun.status}</span>
                </div>

                {/* Events timeline */}
                <div className="space-y-3 max-h-[350px] overflow-y-auto">
                  {selectedRun.events.map((event, i) => (
                    <div key={event.id} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: getAgentColor(event.agent_name?.toLowerCase().replace(/agent$/i, "").replace(/ /g, "_").trim()) }} />
                        {i < selectedRun.events.length - 1 && <div className="w-0.5 flex-1 bg-border mt-1" />}
                      </div>
                      <div className="pb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium">{event.agent_name}</span>
                          <span className="text-[10px] text-muted-foreground">{event.created_at ? formatTime(event.created_at) : ""}</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">{event.message}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Token usage */}
                {selectedRun.token_usage.length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium mb-2">Token Usage</h4>
                    <div className="space-y-1">
                      {selectedRun.token_usage.map((t) => (
                        <div key={t.id} className="flex items-center justify-between text-[10px]">
                          <span className="text-muted-foreground">{t.agent_name}</span>
                          <span>{t.total_tokens.toLocaleString()} tokens</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">Select a run to view execution details</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
