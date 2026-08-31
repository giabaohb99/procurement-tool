import { X } from 'lucide-react'
import { useState } from 'react'

import { cn } from '@/shared/utils/cn'
import type { WorkTask, WorkTaskLink } from '../types/work'
import { WORK_LINK_TYPE_LABELS } from '../types/work'
import type { GanttRowItem } from '../utils/gantt-rows'
import { visibleLinks } from '../utils/gantt-links'
import { ROW_HEIGHT } from '../utils/gantt-layout'
import type { GanttTimeline } from '../utils/gantt-scale'

interface GanttLinkLayerProps {
  links: WorkTaskLink[]
  rows: GanttRowItem[]
  taskRows: Map<number, number>
  tasks: Map<number, WorkTask>
  timeline: GanttTimeline
  canEdit: boolean
  onDelete: (linkId: number) => void
}

/**
 * Lớp MŨI TÊN PHỤ THUỘC (B-15) — một tấm SVG phủ đúng vùng các hàng.
 *
 * Vẽ bằng SVG chứ không ghép `<div>` viền: một mũi tên có tới năm đoạn gấp khúc
 * cộng một tam giác đầu nhọn, ghép bằng div là sáu nút DOM cho mỗi mũi tên và
 * không có cách nào làm đầu nhọn cho tử tế.
 *
 * `pointer-events-none` cho cả tấm, rồi bật lại `auto` cho riêng từng đường:
 * tấm SVG phủ kín mọi thanh bên dưới, để nó ăn chuột thì không thanh nào kéo
 * được nữa — mà lỗi ấy nhìn hệt như "kéo thanh bị hỏng".
 */
export function GanttLinkLayer({
  links,
  rows,
  taskRows,
  tasks,
  timeline,
  canEdit,
  onDelete,
}: GanttLinkLayerProps) {
  const [hovered, setHovered] = useState<number | null>(null)
  const shapes = visibleLinks(links, taskRows, tasks, timeline)
  if (shapes.length === 0) return null

  return (
    <svg
      className="pointer-events-none absolute inset-0 z-20 overflow-visible"
      width={timeline.totalWidth}
      height={rows.length * ROW_HEIGHT}
      aria-hidden
    >
      {shapes.map(({ link, shape }) => {
        const active = hovered === link.id
        return (
          <g key={link.id}>
            {/*  Đường VÔ HÌNH dày 10px chỉ để bắt chuột: nét thật mảnh 1.5px,
                 rê trúng nó bằng chuột gần như không thể. */}
            <path
              d={shape.d}
              fill="none"
              stroke="transparent"
              strokeWidth={10}
              className="pointer-events-auto cursor-pointer"
              onPointerEnter={() => setHovered(link.id)}
              onPointerLeave={() => setHovered((id) => (id === link.id ? null : id))}
            />
            <path
              d={shape.d}
              fill="none"
              strokeWidth={active ? 2 : 1.5}
              className={cn(
                'stroke-muted-foreground/70 transition-[stroke,stroke-width]',
                active && 'stroke-primary',
              )}
            />
            <polygon
              points={shape.arrow}
              className={cn('fill-muted-foreground/70', active && 'fill-primary')}
            />
            <title>{WORK_LINK_TYPE_LABELS[link.link_type] ?? 'Phụ thuộc'}</title>

            {/*  Nút xóa chỉ hiện khi rê trúng đường — một nút cố định trên mỗi
                 mũi tên thì biểu đồ đông việc thành một rừng dấu X. */}
            {active && canEdit && (
              <foreignObject
                x={shape.midX - 9}
                y={shape.midY - 9}
                width={18}
                height={18}
                className="pointer-events-auto overflow-visible"
              >
                <button
                  type="button"
                  aria-label="Xóa phụ thuộc"
                  title="Xóa phụ thuộc"
                  onPointerEnter={() => setHovered(link.id)}
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(link.id)
                  }}
                  className="grid size-[18px] place-items-center rounded-full border border-primary bg-background text-primary shadow-sm hover:bg-primary hover:text-primary-foreground"
                >
                  <X className="size-3" />
                </button>
              </foreignObject>
            )}
          </g>
        )
      })}
    </svg>
  )
}
