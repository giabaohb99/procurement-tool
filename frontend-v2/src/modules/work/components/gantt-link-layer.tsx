import { Check, Trash2 } from 'lucide-react'
import { useState } from 'react'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import type { WorkTask, WorkTaskLink } from '../types/work'
import { WORK_LINK_TYPE_CODES, WORK_LINK_TYPE_LABELS } from '../types/work'
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
  onChangeType: (linkId: number, linkType: number) => void
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
  onChangeType,
  onDelete,
}: GanttLinkLayerProps) {
  const [hovered, setHovered] = useState<number | null>(null)
  //  Menu đang mở của mũi tên nào. Không có nó thì mở menu ra là con trỏ rời
  //  khỏi đường, `hovered` về `null`, viên mã biến mất và menu đóng theo — bấm
  //  mãi không vào được menu.
  const [openId, setOpenId] = useState<number | null>(null)
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
        const active = hovered === link.id || openId === link.id
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

            {/*  Viên MÃ KIỂU chỉ hiện khi rê trúng đường (hoặc khi menu của
                 chính nó đang mở) — gắn cố định trên mỗi mũi tên thì biểu đồ
                 đông việc thành một rừng nhãn. Nó vừa là nhãn vừa là nút: bấm
                 ra menu đổi kiểu và xóa. */}
            {(active || openId === link.id) && canEdit && (
              <foreignObject
                x={shape.midX - 17}
                y={shape.midY - 9}
                width={34}
                height={18}
                className="pointer-events-auto overflow-visible"
              >
                <LinkMenu
                  link={link}
                  onPointerEnter={() => setHovered(link.id)}
                  onOpenChange={(open) => setOpenId(open ? link.id : null)}
                  onChangeType={onChangeType}
                  onDelete={onDelete}
                />
              </foreignObject>
            )}
          </g>
        )
      })}
    </svg>
  )
}

interface LinkMenuProps {
  link: WorkTaskLink
  onPointerEnter: () => void
  onOpenChange: (open: boolean) => void
  onChangeType: (linkId: number, linkType: number) => void
  onDelete: (linkId: number) => void
}

/**
 * Viên mã kiểu trên thân mũi tên (`FS` · `SS` · `FF` · `SF`) — vừa là NHÃN vừa
 * là nút mở menu đổi kiểu / xóa.
 *
 * Gộp hai việc vào một viên thay vì bày hai nút tròn cạnh nhau: chỗ trống trên
 * một đường gấp khúc chỉ đủ cho một thứ, mà hai nút 18px sát nhau thì bấm nhầm
 * "xóa" khi định "đổi kiểu" là chuyện sớm muộn.
 *
 * ⚠️ Đổi kiểu **không** cần dò lại vòng lặp (chiều mũi tên giữ nguyên) nên nó là
 * thao tác rẻ — nhưng đổi HAI ĐẦU thì máy chủ từ chối: xóa rồi nối lại để đi qua
 * đúng bộ kiểm của `create_link`.
 */
function LinkMenu({ link, onPointerEnter, onOpenChange, onChangeType, onDelete }: LinkMenuProps) {
  return (
    <DropdownMenu onOpenChange={onOpenChange}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label={`Phụ thuộc: ${WORK_LINK_TYPE_LABELS[link.link_type] ?? 'không rõ'}`}
          onPointerEnter={onPointerEnter}
          onClick={(e) => e.stopPropagation()}
          className="grid h-[18px] w-[34px] place-items-center rounded-full border border-primary bg-background text-[10px] font-semibold text-primary shadow-sm hover:bg-primary hover:text-primary-foreground"
        >
          {WORK_LINK_TYPE_CODES[link.link_type] ?? '??'}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="center" className="w-52">
        <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
          Kiểu phụ thuộc
        </DropdownMenuLabel>
        {Object.entries(WORK_LINK_TYPE_LABELS).map(([value, label]) => {
          const type = Number(value)
          return (
            <DropdownMenuItem key={value} onClick={() => onChangeType(link.id, type)}>
              {/*  Ô tick giữ chỗ cả khi chưa chọn, không thì mỗi lần đổi kiểu
                   cả danh sách xê ngang một nhịp. */}
              <Check className={cn('size-4', link.link_type !== type && 'invisible')} />
              <span className="font-medium">{WORK_LINK_TYPE_CODES[type]}</span>
              <span className="text-muted-foreground">{label}</span>
            </DropdownMenuItem>
          )
        })}
        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive" onClick={() => onDelete(link.id)}>
          <Trash2 className="size-4" />
          Xóa phụ thuộc
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
