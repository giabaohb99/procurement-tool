import { Handle, Position } from '@xyflow/react'
import { CheckCircle2 } from 'lucide-react'

export function EndNode() {
  return (
    <div className="group relative flex w-[240px] items-center gap-3 rounded-2xl border border-emerald-500/25 bg-card/95 p-3.5 shadow-sm backdrop-blur-xs transition-all hover:border-emerald-500/60 hover:shadow-md dark:border-emerald-500/35">
      <Handle
        type="target"
        position={Position.Top}
        className="!size-3 !-top-1.5 !border-2 !border-card !bg-emerald-500 transition-transform group-hover:scale-125 group-hover:!bg-emerald-600"
      />

      <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 text-emerald-600 dark:text-emerald-400">
        <CheckCircle2 className="size-5" />
      </div>
      <div className="min-w-0 flex-1">
        <span className="text-xs font-semibold text-foreground tracking-tight">Hoàn tất / Ban hành</span>
        <p className="truncate text-[11px] text-muted-foreground mt-0.5">Áp dụng kết quả phê duyệt</p>
      </div>
    </div>
  )
}
