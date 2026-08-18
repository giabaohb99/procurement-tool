import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from '@xyflow/react'
import { Plus } from 'lucide-react'

export interface PlusEdgeData {
  afterStage: number
  intoStage?: number
  onAdd?: (afterStage: number, intoStage?: number) => void
  [key: string]: unknown
}

export function PlusEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 16,
  })

  const edgeData = data as PlusEdgeData | undefined

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          strokeWidth: 2,
          stroke: '#94a3b8',
          ...style,
        }}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan group flex items-center justify-center z-10"
        >
          <button
            type="button"
            onClick={() => edgeData?.onAdd?.(edgeData.afterStage, edgeData.intoStage)}
            title="Chèn bước duyệt tại đây"
            className="flex size-6 items-center justify-center rounded-full border border-slate-300 bg-white text-slate-600 shadow-xs transition-all duration-200 hover:scale-125 hover:border-primary hover:bg-primary hover:text-primary-foreground hover:shadow-md active:scale-95 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
          >
            <Plus className="size-3.5 stroke-[2.5]" />
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  )
}
