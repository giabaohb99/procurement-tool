import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { AlertTriangle, FileInput, Flag, GitBranch, Plus } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import type { ApprovalNode } from '../types/approval'
import { FlowNodeCard } from './flow-node-card'

interface FlowCanvasProps {
  nodes: ApprovalNode[]
  nodeDangChon: number | null
  onChon: (nodeId: number) => void
  onXoa: (nodeId: number) => void
  onNhanBan: (node: ApprovalNode) => void
  /** Thêm bước vào SAU chặng này. `0` = thêm vào đầu luồng. */
  onThem: (sauChang: number) => void
  /** Thêm một NHÁNH song song vào đúng chặng này. */
  onThemNhanh: (chang: number) => void
  onDoiThuTu: (stages: number[][]) => void
}

/**
 * SƠ ĐỒ LUỒNG DUYỆT — dựng theo lối Lark Approval.
 *
 * Đọc từ trên xuống: **Người trình → các chặng → Kết thúc**. Mỗi chặng một khối;
 * chặng có nhiều nhánh thì các nhánh nằm cạnh nhau và chỉ MỘT nhánh chạy — đó là
 * thứ bảng danh sách không nói ra được, và cũng là chỗ người khai hay hiểu nhầm
 * thành "hai bước nối tiếp".
 *
 * Kéo thả để đổi thứ tự; dấu **+** giữa hai chặng để chèn bước vào đúng chỗ đó.
 * Bắt người dùng gõ số chặng vào một ô nhập là bắt họ tự làm việc của máy.
 */
export function FlowCanvas({
  nodes,
  nodeDangChon,
  onChon,
  onXoa,
  onNhanBan,
  onThem,
  onThemNhanh,
  onDoiThuTu,
}: FlowCanvasProps) {
  const sensors = useSensors(
    //  Phải kéo đi 6px mới tính là kéo — không có ngưỡng này thì mỗi cú bấm
    //  chọn bước đều bị nuốt thành một thao tác kéo dài 0 pixel.
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const cacChang = [...new Set(nodes.map((node) => node.seq))].sort((a, b) => a - b)
  const theoChang = cacChang.map((seq) => nodes.filter((node) => node.seq === seq))

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const tu = nodes.find((node) => node.id === Number(active.id))
    const den = nodes.find((node) => node.id === Number(over.id))
    if (!tu || !den || tu.seq === den.seq) return

    //  Kéo giữa các CHẶNG = hoán vị vị trí hai chặng đó. Kéo trong cùng một
    //  chặng không đổi gì: các nhánh song song không có thứ tự với nhau.
    const newOrder = cacChang.slice()
    const i = newOrder.indexOf(tu.seq)
    const j = newOrder.indexOf(den.seq)
    newOrder.splice(i, 1)
    newOrder.splice(j, 0, tu.seq)

    onDoiThuTu(newOrder.map((seq) => nodes.filter((n) => n.seq === seq).map((n) => n.id)))
  }

  return (
    <div className="flex flex-col items-center gap-0 py-2">
      <StartMarker icon={FileInput} label="Người trình duyệt" />

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext
          items={nodes.map((node) => node.id)}
          strategy={verticalListSortingStrategy}
        >
          {theoChang.map((cungChang, index) => {
            const seq = cacChang[index]
            const hasBranch = cungChang.length > 1
            const missingDefault = hasBranch && !cungChang.some((node) => node.is_default_branch)

            return (
              <div key={seq} className="flex w-full flex-col items-center">
                <Connector onThem={() => onThem(index)} />

                <div className="w-full max-w-xl">
                  <div className="mb-1.5 flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-muted-foreground">
                      Chặng {index + 1}
                      {hasBranch && ` · ${cungChang.length} nhánh, chỉ một nhánh chạy`}
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs"
                      onClick={() => onThemNhanh(seq)}
                    >
                      <GitBranch className="size-3.5" />
                      Thêm nhánh
                    </Button>
                  </div>

                  {missingDefault && (
                    <p className="mb-1.5 flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-2.5 py-1.5 text-xs text-amber-900">
                      <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-amber-700" />
                      <span>
                        Chặng rẽ nhánh mà <b>chưa có nhánh mặc định</b> — phiếu không khớp
                        điều kiện nào sẽ kẹt và biến mất khỏi mọi danh sách.
                      </span>
                    </p>
                  )}

                  <div className={cn('grid gap-2', hasBranch && 'sm:grid-cols-2')}>
                    {cungChang.map((node) => (
                      <FlowNodeCard
                        key={node.id}
                        node={node}
                        isQuick={hasBranch}
                        selection={nodeDangChon === node.id}
                        onChon={() => onChon(node.id)}
                        onXoa={() => onXoa(node.id)}
                        onNhanBan={() => onNhanBan(node)}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )
          })}
        </SortableContext>
      </DndContext>

      <Connector onThem={() => onThem(cacChang.length)} />
      <StartMarker icon={Flag} label="Kết thúc — phiếu được duyệt" />
    </div>
  )
}

/** Mốc đầu và mốc cuối — để người đọc biết sơ đồ chạy theo chiều nào. */
function StartMarker({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <Badge variant="outline" className="gap-1.5 bg-muted/50 py-1 font-normal">
      <Icon className="size-3.5" />
      {label}
    </Badge>
  )
}

/** Đoạn nối giữa hai chặng, kèm nút chèn bước vào ĐÚNG chỗ đó. */
function Connector({ onThem }: { onThem: () => void }) {
  return (
    <div className="group/noi flex flex-col items-center">
      <span aria-hidden className="h-4 w-px bg-border" />
      <Button
        type="button"
        variant="outline"
        size="icon"
        className="size-6 rounded-full opacity-40 transition-opacity group-hover/noi:opacity-100"
        title="Chèn bước vào đây"
        aria-label="Chèn bước vào đây"
        onClick={onThem}
      >
        <Plus className="size-3.5" />
      </Button>
      <span aria-hidden className="h-4 w-px bg-border" />
    </div>
  )
}
