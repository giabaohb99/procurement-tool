import { Handle, Position } from '@xyflow/react'
import { Play } from 'lucide-react'

export function StartNode() {
  return (
    <div className="group relative flex w-[240px] items-center gap-3 rounded-2xl border border-indigo-500/20 bg-card/95 p-3.5 shadow-sm backdrop-blur-xs transition-all hover:border-indigo-500/50 hover:shadow-md dark:border-indigo-500/30">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/20 to-indigo-600/10 text-indigo-600 dark:text-indigo-400">
        <Play className="size-4 fill-current ml-0.5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold text-foreground tracking-tight">Người trình duyệt</span>
          <span className="inline-flex size-1.5 rounded-full bg-indigo-500 animate-pulse" />
        </div>
        <p className="truncate text-[11px] text-muted-foreground mt-0.5">Khởi tạo phiếu phê duyệt</p>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!size-3 !-bottom-1.5 !border-2 !border-card !bg-indigo-500 transition-transform group-hover:scale-125 group-hover:!bg-indigo-600"
      />
    </div>
  )
}
