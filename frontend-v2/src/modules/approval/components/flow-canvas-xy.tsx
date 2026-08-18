import {
  Background,
  BackgroundVariant,
  MiniMap,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type EdgeTypes,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  LayoutGrid,
  Map,
  Maximize2,
  Minus,
  Plus,
  PlusCircle,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { buildFlowGraph } from '../helpers/flow-graph-converter'
import type { ApprovalNode } from '../types/approval'
import { PlusEdge } from './flow-canvas/edges/plus-edge'
import { ApprovalStepNode } from './flow-canvas/nodes/approval-step-node'
import { EndNode } from './flow-canvas/nodes/end-node'
import { StartNode } from './flow-canvas/nodes/start-node'

const nodeTypes: NodeTypes = {
  start: StartNode,
  end: EndNode,
  step: ApprovalStepNode,
}

const edgeTypes: EdgeTypes = {
  plus: PlusEdge,
}

interface FlowCanvasXYProps {
  nodes: ApprovalNode[]
  nodeDangChon: number | null
  onChon: (nodeId: number) => void
  onBoChon: () => void
  onXoa: (nodeId: number) => void
  onNhanBan: (node: ApprovalNode) => void
  onThem: (sauChang: number, vaoChang?: number) => void
}

function FlowCanvasInner({
  nodes: approvalNodes,
  nodeDangChon,
  onChon,
  onBoChon,
  onXoa,
  onNhanBan,
  onThem,
}: FlowCanvasXYProps) {
  const { fitView, zoomIn, zoomOut } = useReactFlow()
  const [showMiniMap, setShowMiniMap] = useState(true)

  const graphData = useMemo(() => {
    return buildFlowGraph({
      approvalNodes,
      selectedNodeId: nodeDangChon,
      onSelect: onChon,
      onDelete: onXoa,
      onDuplicate: onNhanBan,
      onAdd: onThem,
      onAddParallel: (seq) => onThem(seq - 1, seq),
    })
  }, [approvalNodes, nodeDangChon, onChon, onXoa, onNhanBan, onThem])

  const [nodes, setNodes, onNodesChange] = useNodesState(graphData.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(graphData.edges)

  useEffect(() => {
    setNodes(graphData.nodes)
    setEdges(graphData.edges)
  }, [graphData, setNodes, setEdges])

  const lastSeq = useMemo(() => {
    if (approvalNodes.length === 0) return 0
    return Math.max(...approvalNodes.map((n) => n.seq))
  }, [approvalNodes])

  return (
    <div className="relative h-full w-full bg-slate-50/50 dark:bg-zinc-950/50">
      <style>{`
        .react-flow__node {
          cursor: default;
        }
        .react-flow__node:focus,
        .react-flow__node:focus-visible {
          outline: none !important;
        }
        .react-flow__handle {
          opacity: 0.8;
        }
        .react-flow__handle:hover {
          opacity: 1;
        }
      `}</style>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeClick={(_event, node) => {
          if (node.type === 'step') {
            onChon(Number(node.id))
          }
        }}
        onPaneClick={onBoChon}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{
          type: 'plus',
        }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1.2}
          color="hsl(var(--muted-foreground) / 0.25)"
        />

        {showMiniMap && (
          <MiniMap
            position="bottom-right"
            zoomable
            pannable
            nodeStrokeWidth={2}
            className="!rounded-2xl !border !border-border !bg-card/90 !backdrop-blur-md !shadow-lg !overflow-hidden"
            nodeColor={(node) => {
              if (node.type === 'start') return '#6366f1'
              if (node.type === 'end') return '#10b981'
              return '#3b82f6'
            }}
          />
        )}

        {/* Floating Quick Action / Toolbar */}
        <Panel position="top-right" className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-xl border border-border/70 bg-card/90 p-1 shadow-sm backdrop-blur-md">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => zoomIn({ duration: 300 })}
              title="Phóng to"
              className="size-8 rounded-lg text-muted-foreground hover:text-foreground"
            >
              <Plus className="size-4" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => zoomOut({ duration: 300 })}
              title="Thu nhỏ"
              className="size-8 rounded-lg text-muted-foreground hover:text-foreground"
            >
              <Minus className="size-4" />
            </Button>
            <div className="mx-1 h-4 w-px bg-border" />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => fitView({ duration: 400, padding: 0.2 })}
              title="Vừa khung nhìn"
              className="size-8 rounded-lg text-muted-foreground hover:text-foreground"
            >
              <Maximize2 className="size-3.5" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => {
                setNodes(graphData.nodes)
                setEdges(graphData.edges)
                fitView({ duration: 400, padding: 0.2 })
              }}
              title="Tự động căn chỉnh sơ đồ"
              className="size-8 rounded-lg text-muted-foreground hover:text-foreground"
            >
              <LayoutGrid className="size-3.5" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => setShowMiniMap((prev) => !prev)}
              title={showMiniMap ? 'Ẩn bản đồ thu nhỏ' : 'Hiện bản đồ thu nhỏ'}
              className="size-8 rounded-lg text-muted-foreground hover:text-foreground"
            >
              <Map className="size-3.5" />
            </Button>
          </div>

          <Button
            type="button"
            onClick={() => onThem(lastSeq)}
            className="h-10 gap-2 rounded-xl bg-primary px-4 font-semibold text-primary-foreground shadow-md transition-all hover:shadow-lg active:scale-98"
          >
            <PlusCircle className="size-4" />
            Thêm bước duyệt
          </Button>
        </Panel>
      </ReactFlow>
    </div>
  )
}

export function FlowCanvasXY(props: FlowCanvasXYProps) {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner {...props} />
    </ReactFlowProvider>
  )
}
