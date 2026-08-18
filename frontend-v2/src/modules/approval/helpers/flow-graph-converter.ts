import { MarkerType, type Edge, type Node } from '@xyflow/react'

import type { ApprovalNode } from '../types/approval'

export interface FlowGraphData {
  nodes: Node[]
  edges: Edge[]
}

interface ConverterOptions {
  approvalNodes: ApprovalNode[]
  selectedNodeId: number | null
  onSelect?: (nodeId: number) => void
  onDelete?: (nodeId: number) => void
  onDuplicate?: (node: ApprovalNode) => void
  onAdd?: (afterStage: number, intoStage?: number) => void
  onAddParallel?: (seq: number) => void
}

const START_NODE_ID = 'node-start'
const END_NODE_ID = 'node-end'

const START_WIDTH = 240
const END_WIDTH = 240
const STEP_WIDTH = 280
const BRANCH_GAP = 50
const STAGE_Y_GAP = 190

const DEFAULT_MARKER = {
  type: MarkerType.ArrowClosed,
  width: 14,
  height: 14,
  color: '#94a3b8',
}

export function buildFlowGraph(options: ConverterOptions): FlowGraphData {
  const {
    approvalNodes,
    selectedNodeId,
    onSelect,
    onDelete,
    onDuplicate,
    onAdd,
    onAddParallel,
  } = options

  const rawNodes: Node[] = []
  const rawEdges: Edge[] = []

  // 1. Add Start Node at top center (x: -START_WIDTH / 2, y: 0)
  rawNodes.push({
    id: START_NODE_ID,
    type: 'start',
    position: { x: -START_WIDTH / 2, y: 0 },
    data: {},
    deletable: false,
    selectable: false,
  })

  let currentY = STAGE_Y_GAP

  if (approvalNodes.length === 0) {
    // End node position
    rawNodes.push({
      id: END_NODE_ID,
      type: 'end',
      position: { x: -END_WIDTH / 2, y: currentY },
      data: {},
      deletable: false,
      selectable: false,
    })

    // Connect Start -> End directly
    rawEdges.push({
      id: `edge-${START_NODE_ID}-${END_NODE_ID}`,
      source: START_NODE_ID,
      target: END_NODE_ID,
      type: 'plus',
      markerEnd: DEFAULT_MARKER,
      data: { afterStage: 0, onAdd },
    })
  } else {
    // Group nodes by seq (stages)
    const stages = [...new Set(approvalNodes.map((n) => n.seq))].sort((a, b) => a - b)
    const stageMap = new Map<number, ApprovalNode[]>()
    for (const seq of stages) {
      stageMap.set(seq, approvalNodes.filter((n) => n.seq === seq))
    }

    // Position each stage symmetrically around X = 0
    stages.forEach((seq, stageIndex) => {
      const stageNodes = stageMap.get(seq) || []
      const stageY = (stageIndex + 1) * STAGE_Y_GAP
      currentY = stageY + STAGE_Y_GAP

      const count = stageNodes.length
      const totalWidth = count * STEP_WIDTH + (count - 1) * BRANCH_GAP
      const startX = -totalWidth / 2

      stageNodes.forEach((node, nodeIndex) => {
        const nodeIdStr = String(node.id)
        const nodeX = startX + nodeIndex * (STEP_WIDTH + BRANCH_GAP)

        rawNodes.push({
          id: nodeIdStr,
          type: 'step',
          position: { x: nodeX, y: stageY },
          selected: selectedNodeId === node.id,
          data: {
            node,
            isDefaultBranch: node.is_default_branch,
            hasBranching: count > 1,
            branchIndex: nodeIndex + 1,
            totalBranches: count,
            onSelect,
            onDelete,
            onDuplicate,
            onAddParallel,
          },
        })
      })
    })

    // End Node at bottom center
    rawNodes.push({
      id: END_NODE_ID,
      type: 'end',
      position: { x: -END_WIDTH / 2, y: currentY },
      data: {},
      deletable: false,
      selectable: false,
    })

    // Connect Start Node -> First Stage Nodes
    const firstStage = stages[0]
    const firstStageNodes = stageMap.get(firstStage) || []
    for (const targetNode of firstStageNodes) {
      const targetId = String(targetNode.id)
      rawEdges.push({
        id: `edge-${START_NODE_ID}-${targetId}`,
        source: START_NODE_ID,
        target: targetId,
        type: 'plus',
        markerEnd: DEFAULT_MARKER,
        data: { afterStage: 0, onAdd },
      })
    }

    // Connect intermediate stages
    for (let i = 0; i < stages.length - 1; i++) {
      const currentSeq = stages[i]
      const nextSeq = stages[i + 1]
      const currentNodes = stageMap.get(currentSeq) || []
      const nextNodes = stageMap.get(nextSeq) || []

      for (const src of currentNodes) {
        for (const dest of nextNodes) {
          const srcId = String(src.id)
          const destId = String(dest.id)
          rawEdges.push({
            id: `edge-${srcId}-${destId}`,
            source: srcId,
            target: destId,
            type: 'plus',
            markerEnd: DEFAULT_MARKER,
            data: { afterStage: currentSeq, onAdd },
          })
        }
      }
    }

    // Connect Last Stage Nodes -> End Node
    const lastStage = stages[stages.length - 1]
    const lastStageNodes = stageMap.get(lastStage) || []
    for (const src of lastStageNodes) {
      const srcId = String(src.id)
      rawEdges.push({
        id: `edge-${srcId}-${END_NODE_ID}`,
        source: srcId,
        target: END_NODE_ID,
        type: 'plus',
        markerEnd: DEFAULT_MARKER,
        data: { afterStage: lastStage, onAdd },
      })
    }
  }

  return { nodes: rawNodes, edges: rawEdges }
}
