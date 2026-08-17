import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { AlertTriangle, Copy, GripVertical, Trash2, Users } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { NODE_KIND, type ApprovalNode } from '../types/approval'

interface FlowNodeCardProps {
  node: ApprovalNode
  dangChon: boolean
  /** Chặng này có nhiều nhánh — thẻ hẹp lại và hiện nhãn nhánh. */
  laNhanh?: boolean
  onChon: () => void
  onXoa: () => void
  onNhanBan: () => void
}

/**
 * Một BƯỚC trên sơ đồ luồng — thẻ kéo được.
 *
 * Tay cầm kéo (`GripVertical`) tách khỏi phần thân bấm được: gắn listener kéo
 * lên cả thẻ thì mỗi lần bấm chọn bước đều bị hiểu nhầm thành bắt đầu kéo, và
 * người dùng không mở được bảng thuộc tính.
 */
export function FlowNodeCard({
  node,
  dangChon,
  laNhanh,
  onChon,
  onXoa,
  onNhanBan,
}: FlowNodeCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: node.id })

  const laBanSao = node.node_kind === NODE_KIND.cc

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn(
        'group relative rounded-lg border bg-background shadow-sm transition-colors',
        dangChon && 'border-primary ring-2 ring-primary/20',
        isDragging && 'z-10 opacity-60 shadow-lg',
        laNhanh ? 'w-full' : 'w-full',
      )}
    >
      <div className="flex items-start gap-2 p-3">
        <button
          type="button"
          className="mt-0.5 cursor-grab touch-none text-muted-foreground active:cursor-grabbing"
          aria-label="Kéo để đổi thứ tự"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="size-4" />
        </button>

        <button type="button" onClick={onChon} className="min-w-0 flex-1 text-left">
          <p className="flex flex-wrap items-center gap-1.5 text-sm font-medium">
            {node.name || `Bước ${node.seq}`}
            {laBanSao && (
              <Badge variant="outline" className="font-normal">
                {node.node_kind_label}
              </Badge>
            )}
            {node.is_default_branch && (
              <Badge variant="outline" className="font-normal">
                Mặc định
              </Badge>
            )}
          </p>

          <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Users className="size-3.5 shrink-0" />
            <span className="truncate">
              {node.approver_names || node.approver_kind_label}
            </span>
          </p>

          <p className="text-xs text-muted-foreground">
            {node.multi_mode_label}
            {node.sla_hours > 0 && ` · hạn ${node.sla_hours} giờ`}
          </p>

          {node.condition && (
            <p className="mt-1 truncate rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
              {node.condition}
            </p>
          )}

          {/*  Bước rẽ nhánh mà không ai duyệt được thì phiếu kẹt — cảnh báo ngay
               trên thẻ, không đợi mở bảng thuộc tính mới thấy. */}
          {!node.approver_ref && node.approver_kind === 1 && (
            <p className="mt-1 flex items-center gap-1 text-xs text-amber-800">
              <AlertTriangle className="size-3.5 shrink-0" />
              Chưa chọn người duyệt
            </p>
          )}
        </button>

        <div className="flex shrink-0 gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-7"
            title="Nhân bản bước"
            aria-label="Nhân bản bước"
            onClick={onNhanBan}
          >
            <Copy className="size-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-7 text-muted-foreground hover:text-destructive"
            title="Xóa bước"
            aria-label="Xóa bước"
            onClick={onXoa}
          >
            <Trash2 className="size-3.5" />
          </Button>
        </div>
      </div>
    </div>
  )
}
