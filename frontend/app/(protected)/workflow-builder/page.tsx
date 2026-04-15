"use client";
import { useEffect, useState, useCallback, memo } from "react";
import {
  ReactFlow, ReactFlowProvider, Background, Controls,
  Handle, Position, addEdge, useEdgesState, useNodesState,
  useReactFlow, Panel, ConnectionMode,
  type Connection, type Edge, type Node, type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Play, Save, Pause, Plus, ChevronDown, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { workflowsApi, type Workflow, type WorkflowRun } from "@/lib/api";
import { formatTimeAgo } from "@/lib/utils";

// ── Node types ────────────────────────────────────────────────────────────────

type WorkflowKind = "trigger" | "condition" | "ai" | "crm" | "notification";

const KIND_COLORS: Record<WorkflowKind, string> = {
  trigger: "#3b82f6", condition: "#f59e0b", ai: "#7c3aed", crm: "#10b981", notification: "#f97316",
};
const KIND_LABELS: Record<WorkflowKind, string> = {
  trigger: "Trigger", condition: "Condition", ai: "AI Action", crm: "CRM Action", notification: "Notification",
};

const handleCls = "!h-3 !w-3 !min-h-0 !min-w-0 !border-2 !border-[#08090f] !rounded-full !transform-none";

const WorkflowNode = memo(({ data, selected }: NodeProps) => {
  const d = data as { kind: WorkflowKind; label: string; color: string };
  const cat = KIND_LABELS[d.kind];
  return (
    <div className="relative">
      <Handle type="target" position={Position.Left} id="in" className={`${handleCls} !bg-[#7c3aed]`} />
      <div
        className={`w-[148px] rounded-xl border border-white/10 bg-white/5 p-3.5 shadow-lg backdrop-blur-sm transition-all ${
          selected ? "border-[#f97316]/60 bg-white/[0.08] ring-2 ring-[#f97316]/40" : "hover:border-white/20 hover:bg-white/[0.07]"
        }`}
        style={{ boxShadow: `0 0 0 1px ${d.color}33` }}
      >
        <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg text-xs font-semibold" style={{ backgroundColor: `${d.color}28`, color: d.color }}>
          {cat.charAt(0)}
        </div>
        <div className="mb-0.5 text-sm font-medium text-white">{d.label}</div>
        <div className="text-xs text-white/45">{cat}</div>
      </div>
      {d.kind === "condition" ? (
        <>
          <Handle type="source" position={Position.Right} id="yes" style={{ top: "32%" }} className={`${handleCls} !bg-emerald-500`} />
          <Handle type="source" position={Position.Right} id="no" style={{ top: "68%" }} className={`${handleCls} !bg-amber-500`} />
        </>
      ) : (
        <Handle type="source" position={Position.Right} id="out" className={`${handleCls} !bg-[#3b82f6]`} />
      )}
    </div>
  );
});
WorkflowNode.displayName = "WorkflowNode";

const nodeTypes = { workflow: WorkflowNode };

// ── Canvas ────────────────────────────────────────────────────────────────────

function WorkflowCanvas({ initialNodes, initialEdges, onSave }: {
  initialNodes: Node[];
  initialEdges: Edge[];
  onSave: (nodes: Node[], edges: Edge[]) => void;
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const { screenToFlowPosition } = useReactFlow();

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: "rgba(249,115,22,0.5)", strokeWidth: 2 } }, eds));
  }, [setEdges]);

  const addNode = (kind: WorkflowKind) => {
    const id = `n-${Date.now()}`;
    setNodes((nds) => [...nds, {
      id, type: "workflow",
      position: screenToFlowPosition({ x: window.innerWidth / 2 - 74, y: window.innerHeight / 2 - 50 }),
      data: { kind, label: `New ${KIND_LABELS[kind]}`, color: KIND_COLORS[kind] },
    }]);
    toast.success(`Added ${KIND_LABELS[kind]} node`);
  };

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        onConnect={onConnect} nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose} fitView fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3} maxZoom={1.8} snapToGrid snapGrid={[16, 16]}
        deleteKeyCode={["Backspace", "Delete"]}
        defaultEdgeOptions={{ type: "smoothstep", animated: false, style: { stroke: "rgba(249,115,22,0.4)", strokeWidth: 2 } }}
        className="bg-[#08090f]" proOptions={{ hideAttribution: true }}
      >
        <Background gap={20} size={1} color="rgba(255,255,255,0.04)" />
        <Controls className="!m-2 !overflow-hidden !rounded-xl !border !border-white/10 !bg-[#0d0e1a]/95 !shadow-lg" showInteractive={false} />
        <Panel position="bottom-center" className="!m-0 w-full max-w-full px-3 pb-2">
          <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-2 rounded-2xl border border-white/10 bg-[#0d0e1a]/95 px-3 py-2.5 shadow-xl backdrop-blur-xl">
            <span className="w-full text-center text-xs text-white/40 sm:w-auto">Add node:</span>
            {(Object.entries(KIND_LABELS) as [WorkflowKind, string][]).map(([kind, label]) => (
              <button key={kind} onClick={() => addNode(kind)}
                className="flex min-h-10 items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80 transition-colors hover:bg-white/10"
              >
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: KIND_COLORS[kind] }} />
                {label}
              </button>
            ))}
            <button onClick={() => onSave(nodes, edges)}
              className="flex items-center gap-1.5 rounded-xl bg-[#f97316] px-3 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90"
            >
              <Save className="h-3.5 w-3.5" /> Save
            </button>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function WorkflowBuilderPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selected, setSelected] = useState<Workflow | null>(null);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState<{ id: string; name: string; trigger_type: string }[]>([]);

  const loadWorkflows = useCallback(async () => {
    try {
      const wfs = await workflowsApi.list();
      setWorkflows(wfs);
      if (!selected && wfs.length > 0) setSelected(wfs[0]);
    } catch {
      setWorkflows(MOCK_WORKFLOWS);
      setSelected(MOCK_WORKFLOWS[0]);
    } finally {
      setLoading(false);
    }
  }, [selected]);

  const loadRuns = useCallback(async (wfId: string) => {
    try {
      const r = await workflowsApi.runs(wfId);
      setRuns(r);
    } catch {
      setRuns([]);
    }
  }, []);

  useEffect(() => { loadWorkflows(); }, []);
  useEffect(() => {
    workflowsApi.templates().then(setTemplates).catch(() => {});
  }, []);
  useEffect(() => {
    if (selected) loadRuns(selected.id);
  }, [selected, loadRuns]);

  const handleSave = async (nodes: Node[], edges: Edge[]) => {
    if (!selected) return;
    try {
      await workflowsApi.update(selected.id, { nodes, edges });
      toast.success("Workflow saved", { description: selected.name });
    } catch {
      toast.error("Save failed");
    }
  };

  const handleToggleStatus = async () => {
    if (!selected) return;
    const newStatus = selected.status === "active" ? "paused" : "active";
    try {
      await workflowsApi.update(selected.id, { status: newStatus });
      setSelected({ ...selected, status: newStatus });
      setWorkflows((wfs) => wfs.map((w) => w.id === selected.id ? { ...w, status: newStatus } : w));
      toast.info(newStatus === "active" ? "Workflow activated" : "Workflow paused");
    } catch {
      toast.error("Status update failed");
    }
  };

  const handleRun = async () => {
    if (!selected) return;
    setRunning(true);
    try {
      const result = await workflowsApi.run(selected.id);
      toast.success(`Run complete — ${result.nodes_executed} nodes executed`, { duration: 4000 });
      loadRuns(selected.id);
    } catch {
      toast.error("Run failed");
    } finally {
      setRunning(false);
    }
  };

  const handleCreateFromTemplate = async (templateId: string) => {
    const tpl = templates.find((t) => t.id === templateId);
    if (!tpl) return;
    try {
      const wf = await workflowsApi.create({
        name: tpl.name, trigger_type: tpl.trigger_type, template_id: templateId,
      });
      setWorkflows((prev) => [wf, ...prev]);
      setSelected(wf);
      setShowTemplates(false);
      toast.success(`Created: ${tpl.name}`);
    } catch {
      toast.error("Failed to create workflow");
    }
  };

  if (loading) {
    return <div className="flex h-full items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-[#f97316]" /></div>;
  }

  const nodes = (selected?.nodes as Node[]) || [];
  const edges = (selected?.edges as Edge[]) || [];

  return (
    <ReactFlowProvider>
      <div className="flex h-full min-h-0 flex-col lg:flex-row">
        {/* Left sidebar — workflow list */}
        <aside className="belon-scroll w-full shrink-0 overflow-y-auto border-b border-white/5 lg:w-64 lg:border-b-0 lg:border-r">
          <div className="p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium text-white/70">Workflows</h2>
              <button onClick={() => setShowTemplates(!showTemplates)}
                className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs transition-colors hover:bg-white/10"
              >
                <Plus className="h-3 w-3" /> New
              </button>
            </div>

            {/* Template picker */}
            {showTemplates && (
              <div className="mb-3 rounded-xl border border-white/10 bg-white/5 p-2">
                <p className="mb-2 px-1 text-xs text-white/50">From template:</p>
                {templates.map((t) => (
                  <button key={t.id} onClick={() => handleCreateFromTemplate(t.id)}
                    className="w-full rounded-lg px-2 py-2 text-left text-xs text-white/70 transition-colors hover:bg-white/10"
                  >
                    {t.name}
                  </button>
                ))}
              </div>
            )}

            <div className="space-y-1.5">
              {workflows.map((wf) => (
                <button key={wf.id} onClick={() => setSelected(wf)}
                  className={`w-full rounded-xl border p-3 text-left transition-colors ${
                    selected?.id === wf.id ? "border-[#f97316]/30 bg-[#f97316]/10" : "border-white/10 bg-white/5 hover:bg-white/[0.07]"
                  }`}
                >
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-sm font-medium">{wf.name}</span>
                    <span className={`h-1.5 w-1.5 rounded-full ${wf.status === "active" ? "bg-emerald-500" : "bg-white/20"}`} />
                  </div>
                  <div className="text-xs text-white/40">{wf.run_count} runs · {wf.last_run_at ? formatTimeAgo(wf.last_run_at) : "never run"}</div>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Main canvas */}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          {/* Toolbar */}
          {selected && (
            <div className="shrink-0 border-b border-white/5 bg-[#0d0e1a]/50 px-4 py-3 backdrop-blur-xl lg:px-6">
              <div className="flex items-center justify-between gap-4">
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <h1 className="truncate text-lg font-medium">{selected.name}</h1>
                  <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs ${
                    selected.status === "active" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" : "border-white/10 bg-white/5 text-white/40"
                  }`}>
                    {selected.status === "active" ? "● Active" : "○ Paused"}
                  </span>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <button onClick={handleToggleStatus}
                    className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm transition-colors hover:bg-white/10"
                  >
                    {selected.status === "active" ? <><Pause className="h-3.5 w-3.5" /> Pause</> : <><Play className="h-3.5 w-3.5" /> Activate</>}
                  </button>
                  <button onClick={handleRun} disabled={running}
                    className="flex items-center gap-1.5 rounded-xl bg-[#f97316] px-3 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-60"
                  >
                    {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                    Test Run
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Flow canvas */}
          <div className="relative min-h-0 flex-1">
            {selected ? (
              <WorkflowCanvas
                key={selected.id}
                initialNodes={nodes}
                initialEdges={edges}
                onSave={handleSave}
              />
            ) : (
              <div className="flex h-full items-center justify-center text-white/40">
                Select or create a workflow
              </div>
            )}
          </div>

          {/* Recent runs */}
          {runs.length > 0 && (
            <div className="belon-scroll shrink-0 border-t border-white/5 bg-[#0d0e1a]/30 px-4 py-3 lg:px-6">
              <p className="mb-2 text-xs text-white/40">Recent runs</p>
              <div className="flex gap-2 overflow-x-auto">
                {runs.slice(0, 6).map((run) => (
                  <div key={run.id} className="shrink-0 rounded-lg border border-white/10 bg-white/5 px-3 py-2">
                    <div className="flex items-center gap-1.5">
                      {run.status === "completed" ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : <XCircle className="h-3.5 w-3.5 text-red-400" />}
                      <span className="text-xs text-white/60">{run.nodes_executed} nodes</span>
                      {run.duration_ms && <span className="text-xs text-white/35">{run.duration_ms}ms</span>}
                    </div>
                    <div className="mt-0.5 text-xs text-white/30">{formatTimeAgo(run.started_at)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </ReactFlowProvider>
  );
}

// ── Mock data ─────────────────────────────────────────────────────────────────

const MOCK_NODES: Node[] = [
  { id: "1", type: "workflow", position: { x: 80, y: 160 }, data: { kind: "trigger", label: "Deal Stage Changed", color: "#3b82f6" } },
  { id: "2", type: "workflow", position: { x: 300, y: 160 }, data: { kind: "condition", label: "Stage = Stalled?", color: "#f59e0b" } },
  { id: "3", type: "workflow", position: { x: 520, y: 100 }, data: { kind: "ai", label: "Analyze Deal Health", color: "#7c3aed" } },
  { id: "4", type: "workflow", position: { x: 740, y: 100 }, data: { kind: "ai", label: "Generate Email Draft", color: "#7c3aed" } },
  { id: "5", type: "workflow", position: { x: 520, y: 240 }, data: { kind: "crm", label: "Update Deal Notes", color: "#10b981" } },
  { id: "6", type: "workflow", position: { x: 940, y: 160 }, data: { kind: "notification", label: "Notify Rep", color: "#f97316" } },
];
const MOCK_EDGES: Edge[] = [
  { id: "e1-2", source: "1", target: "2" },
  { id: "e2-3", source: "2", target: "3", label: "Yes" },
  { id: "e2-5", source: "2", target: "5", label: "No" },
  { id: "e3-4", source: "3", target: "4" },
  { id: "e4-6", source: "4", target: "6" },
  { id: "e5-6", source: "5", target: "6" },
];
const MOCK_WORKFLOWS: Workflow[] = [
  { id: "m1", name: "Stalled Deal Recovery", description: null, status: "active", trigger_type: "signal_fired", nodes: MOCK_NODES, edges: MOCK_EDGES, run_count: 47, success_count: 44, fail_count: 3, last_run_at: new Date(Date.now() - 3600000).toISOString(), template_id: "stalled-deal-recovery", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "m2", name: "Instant Lead Qualification", description: null, status: "active", trigger_type: "contact_created", nodes: [], edges: [], run_count: 128, success_count: 121, fail_count: 7, last_run_at: new Date(Date.now() - 7200000).toISOString(), template_id: "lead-qualification", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "m3", name: "Churn Risk Alert", description: null, status: "paused", trigger_type: "signal_fired", nodes: [], edges: [], run_count: 23, success_count: 20, fail_count: 3, last_run_at: new Date(Date.now() - 86400000).toISOString(), template_id: "churn-risk-alert", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
];
