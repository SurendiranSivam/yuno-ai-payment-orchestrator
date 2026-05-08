"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  type Node,
  type Edge,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Bot, Play, Flag } from "lucide-react";

interface WorkflowCanvasProps {
  graphDefinition: {
    nodes?: any[];
    edges?: any[];
  };
}

// Custom agent node renderer — has both source (bottom) and target (top) handles
function AgentNode({ data }: { data: any }) {
  const color = data.color || "#3b82f6";
  return (
    <div className="rounded-lg border bg-card shadow-lg min-w-[200px]"
      style={{ borderColor: color + "40" }}>
      <Handle type="target" position={Position.Top} className="!bg-slate-500 !w-2 !h-2 !border-0" />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
        style={{ backgroundColor: color + "15" }}>
        <Bot className="w-3.5 h-3.5" style={{ color }} />
        <span className="text-xs font-medium text-foreground">{data.label}</span>
      </div>
      <div className="px-3 py-2">
        <span className="text-[10px] text-muted-foreground">{data.role?.replace(/_/g, " ") || "Agent"}</span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-slate-500 !w-2 !h-2 !border-0" />
    </div>
  );
}

// Input node — only has a source handle (bottom) since it's the start
function InputNode({ data }: { data: any }) {
  return (
    <div className="rounded-lg border border-primary/30 bg-primary/10 px-4 py-2.5 flex items-center gap-2">
      <Play className="w-3.5 h-3.5 text-primary" />
      <span className="text-xs font-medium text-primary">{data.label}</span>
      <Handle type="source" position={Position.Bottom} className="!bg-primary !w-2 !h-2 !border-0" />
    </div>
  );
}

// Output node — only has a target handle (top) since it's the end
function OutputNode({ data }: { data: any }) {
  return (
    <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 flex items-center gap-2">
      <Handle type="target" position={Position.Top} className="!bg-emerald-500 !w-2 !h-2 !border-0" />
      <Flag className="w-3.5 h-3.5 text-emerald-400" />
      <span className="text-xs font-medium text-emerald-400">{data.label}</span>
    </div>
  );
}

const nodeTypes: NodeTypes = {
  agent: AgentNode,
  input: InputNode,
  output: OutputNode,
};

export default function WorkflowCanvas({ graphDefinition }: WorkflowCanvasProps) {
  const nodes: Node[] = useMemo(() =>
    (graphDefinition?.nodes || []).map((n: any) => ({
      id: n.id,
      type: n.type || "agent",
      position: n.position || { x: 0, y: 0 },
      data: n.data || {},
    })),
    [graphDefinition]
  );

  const edges: Edge[] = useMemo(() =>
    (graphDefinition?.edges || []).map((e: any) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      type: "smoothstep",
      animated: e.animated ?? true,
      style: { stroke: "#475569", strokeWidth: 1.5 },
      labelStyle: { fontSize: 10, fill: "#94a3b8" },
    })),
    [graphDefinition]
  );

  if (!graphDefinition?.nodes?.length) {
    return (
      <div className="w-full h-full flex items-center justify-center text-sm text-muted-foreground">
        No workflow graph defined
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      proOptions={{ hideAttribution: true }}
      defaultEdgeOptions={{
        type: "smoothstep",
        animated: true,
      }}
    >
      <Background color="#1e293b" gap={20} />
      <Controls className="!bg-card !border-border" />
      <MiniMap
        nodeColor={(n) => (n.data?.color as string) || "#3b82f6"}
        maskColor="rgba(0,0,0,0.6)"
        className="!bg-card !border-border"
      />
    </ReactFlow>
  );
}
