import { ChevronRight } from 'lucide-react'
import type { DragEvent, KeyboardEvent, ReactNode, RefCallback } from 'react'

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip'
import { cn } from '@/shared/utils/cn'
import { TreeIndentGuides } from './tree-indent-guides'
import { useTreeRowDnd } from './use-tree-row-dnd'
import type { FlatTreeNode, TreeNode } from './tree-types'

export interface TreeRowProps<T> {
  row: FlatTreeNode<T>
  node: TreeNode<T>
  expanded: boolean | undefined
  selected: boolean
  highlighted: boolean
  focused: boolean
  drop: 'valid' | 'invalid' | undefined
  /** Dòng này có nhận đổi THỨ TỰ (thả trước/sau, cùng cha) hay không — xem `resolve-drop-zone.ts`. */
  reorderable: boolean
  draggable: boolean
  /** Chữ tooltip cả dòng — bỏ trống = không bọc `Tooltip`. Xem `TreeViewProps.getTooltip`. */
  tooltip?: string
  refCallback: RefCallback<HTMLDivElement>
  onToggleExpand: (id: string | number) => void
  onSelect: (node: TreeNode<T>) => void
  /** Bấm ĐÚP — ví dụ đổi tên tại chỗ. Bỏ trống = không xử lý gì thêm ngoài `onSelect`. */
  onRowDoubleClick?: (node: TreeNode<T>) => void
  onFocusRow: (id: string | number) => void
  onKeyDownRow: (event: KeyboardEvent<HTMLDivElement>) => void
  onDragStartNode?: (node: TreeNode<T>) => void
  onDragStartEvent?: (node: TreeNode<T>, event: DragEvent<HTMLDivElement>) => void
  onDragEndNode?: () => void
  onDropNode?: (node: TreeNode<T>) => void
  /** Thả TRƯỚC/SAU dòng này — chỉ gọi khi vùng thả tính ra `before`/`after`. */
  onReorderDrop?: (node: TreeNode<T>, position: 'before' | 'after') => void
  /** MIME của payload NGOÀI cây (kéo từ khung khác) — bỏ trống = dòng không nhận kiểu thả này. */
  externalDropMimeType?: string
  /** Dòng này có nhận payload ngoài không — bỏ trống = nhận hết. */
  acceptsExternalDrop?: (node: TreeNode<T>) => boolean
  onExternalDropNode?: (node: TreeNode<T>, event: DragEvent<HTMLDivElement>) => void
  renderIcon?: (node: TreeNode<T>) => ReactNode
  renderBadge?: (node: TreeNode<T>) => ReactNode
  renderTrailing?: (node: TreeNode<T>) => ReactNode
  /** Hành động chỉ hiện khi RÊ CHUỘT qua dòng (ví dụ nút "+" thêm con) — cùng vùng ẩn/hiện với `renderTrailing`. */
  renderHoverActions?: (node: TreeNode<T>) => ReactNode
  renderLabel?: (node: TreeNode<T>) => ReactNode
}

/**
 * MỘT DÒNG của `TreeView`, kiểu VS Code Explorer — cao 24px, chữ 13px, đường
 * gióng thụt lề dọc (`TreeIndentGuides`). Tách khỏi `tree-view.tsx` (giữ tệp đó
 * dưới 200 dòng) và giao toàn bộ sự kiện kéo thả cho `useTreeRowDnd`.
 */
export function TreeRow<T>(props: TreeRowProps<T>) {
  const {
    row,
    node,
    expanded,
    selected,
    highlighted,
    focused,
    drop,
    draggable,
    tooltip,
    refCallback,
    onToggleExpand,
    onSelect,
    onRowDoubleClick,
    onFocusRow,
    onKeyDownRow,
    renderIcon,
    renderBadge,
    renderTrailing,
    renderHoverActions,
    renderLabel,
  } = props

  const { hoverZone, externalHover, dragHandlers } = useTreeRowDnd(props)
  //  Tô cả dòng chỉ khi con trỏ KHÔNG ở mép trên/dưới (mép = đổi thứ tự, vạch kẻ).
  const showIntoTint = hoverZone !== 'before' && hoverZone !== 'after'

  const content = (
    <div
      ref={refCallback}
      role="treeitem"
      aria-selected={selected}
      aria-expanded={expanded}
      aria-level={row.depth + 1}
      tabIndex={focused ? 0 : -1}
      className={cn(
        //  KHÔNG bo góc — dòng tô full-bleed sát hai mép khung kiểu VS Code
        //  Explorer, không phải một "chip" nổi giữa khoảng trắng.
        'group relative flex h-6 cursor-pointer items-center gap-1 py-1 pr-1.5 pl-2 text-[13px] outline-none',
        'hover:bg-accent/70',
        //  VS Code: dòng ĐANG CHỌN chỉ tô nền (`bg-accent`), KHÔNG viền — viền
        //  chỉ hiện khi TIÊU ĐIỂM BÀN PHÍM thật sự tới đây qua `:focus-visible`
        //  (trình duyệt tự ẩn khi tiêu điểm đến từ chuột). Trước đây dùng prop
        //  `focused` (roving tabindex, gần như LUÔN trùng `selected` vì
        //  `focusedId` khởi tạo bằng `selectedId`) nên dòng chọn lúc nào cũng
        //  kèm viền xanh dương — bug lead bắt 23/09/2026.
        'focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-ring',
        selected && 'bg-accent font-medium text-accent-foreground',
        highlighted && !selected && 'bg-amber-50',
        showIntoTint &&
          (drop === 'valid' || externalHover) &&
          'bg-emerald-50 ring-2 ring-inset ring-emerald-400',
        showIntoTint &&
          drop === 'invalid' &&
          'cursor-not-allowed bg-destructive/5 ring-2 ring-inset ring-destructive/60',
      )}
      draggable={draggable}
      {...dragHandlers}
      onClick={() => {
        onFocusRow(row.id)
        onSelect(node)
      }}
      onDoubleClick={() => onRowDoubleClick?.(node)}
      onKeyDown={onKeyDownRow}
    >
      {(hoverZone === 'before' || hoverZone === 'after') && (
        <span
          aria-hidden
          className={cn(
            'pointer-events-none absolute inset-x-2 h-0.5 rounded-full bg-primary',
            hoverZone === 'before' ? '-top-px' : '-bottom-px',
          )}
        />
      )}

      <TreeIndentGuides depth={row.depth} bold={selected} />

      {row.hasChildren ? (
        <button
          type="button"
          tabIndex={-1}
          aria-label={expanded ? 'Thu gọn' : 'Mở rộng'}
          className="flex size-4 shrink-0 items-center justify-center rounded hover:bg-muted"
          onClick={(event) => {
            event.stopPropagation()
            onToggleExpand(row.id)
          }}
        >
          <ChevronRight className={cn('size-3.5 transition-transform', expanded && 'rotate-90')} />
        </button>
      ) : (
        <span className="size-4 shrink-0" aria-hidden />
      )}

      {renderIcon?.(node)}

      {renderLabel ? renderLabel(node) : <span className="min-w-0 flex-1 truncate">{row.label}</span>}

      {renderBadge?.(node)}

      {(renderHoverActions || renderTrailing) && (
        <span
          className={cn(
            'flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity',
            'group-hover:opacity-100 group-focus-within:opacity-100 has-[[data-state=open]]:opacity-100',
          )}
        >
          {renderHoverActions?.(node)}
          {renderTrailing?.(node)}
        </span>
      )}
    </div>
  )

  if (!tooltip) return content
  //  `TooltipProvider` RIÊNG (cùng lối `icon-tooltip.tsx`) — nơi dùng `TreeView`
  //  không phải tự dựng provider chỉ vì một dòng cần tooltip, và bài kiểm dựng
  //  thẳng `TreeView`/`TreeRow` không cần biết tới Radix Tooltip context.
  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>{content}</TooltipTrigger>
        <TooltipContent side="right">{tooltip}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
