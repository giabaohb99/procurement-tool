import { useMemo, type DragEvent, type ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'
import { flattenTree } from './flatten-tree'
import { TreeRow } from './tree-row'
import type { TreeNode } from './tree-types'
import { useTreeViewRovingFocus } from './use-tree-view-roving-focus'

export interface TreeViewProps<T = unknown> {
  nodes: TreeNode<T>[]
  /** Nhãn accessible cho cả cây (`aria-label`) — bắt buộc, trình đọc màn hình cần biết đây là cây gì. */
  ariaLabel: string
  selectedId?: string | number | null
  onSelect?: (node: TreeNode<T>) => void
  /** Enter/Space — xem chú thích ở `UseTreeViewRovingFocusOptions.onActivate` (`use-tree-view-roving-focus.ts`). Bỏ trống = Enter/Space gọi `onSelect`. */
  onActivate?: (node: TreeNode<T>) => void
  /**
   * Tiêu điểm bàn phím CHUYỂN SANG node khác (↑↓, Home/End, →/← lùi ra cha) —
   * khác `onSelect` (chỉ bấm chuột / Enter / Space). Dùng cho nơi muốn xem
   * trước đổi NGAY THEO CON TRỎ, kiểu danh sách thư/tệp (tab «Tệp» của văn
   * bản, phase 09) — không bắt buộc, bỏ trống thì di chuyển chỉ đổi tiêu điểm.
   */
  onFocusChange?: (node: TreeNode<T>) => void
  /** Bấm ĐÚP một dòng — ví dụ đổi tên tại chỗ (thư mục văn bản). */
  onRowDoubleClick?: (node: TreeNode<T>) => void
  /** Tập id đang MỞ — giữ ở ngoài (`useTreeExpansion`), component này không tự có state gập/mở. */
  expandedIds: Set<string | number>
  onToggleExpand: (id: string | number) => void
  /** id các node cần TÔ SÁNG (kết quả lọc, xem `filterTree`) — bỏ trống = không tô. */
  highlightIds?: Set<string | number>
  /** Icon riêng trước tên node — trả `null` để không vẽ gì cho node đó. */
  renderIcon?: (node: TreeNode<T>) => ReactNode
  /** Nhãn phụ / huy hiệu SAU tên node (số đếm, trạng thái…). */
  renderBadge?: (node: TreeNode<T>) => ReactNode
  /** Nút/hành động cuối dòng — CHỈ hiện khi rê chuột/focus qua dòng đó (cùng vùng ẩn/hiện với `renderHoverActions`). */
  renderTrailing?: (node: TreeNode<T>) => ReactNode
  /** Hành động phụ chỉ hiện khi rê chuột — ví dụ nút "+" thêm con ngay trên dòng. */
  renderHoverActions?: (node: TreeNode<T>) => ReactNode
  /**
   * Ghi đè PHẦN NHÃN (mặc định `<span>{row.label}</span>`) — dùng cho đổi tên
   * TẠI CHỖ (thư mục văn bản, phase 05): nơi gọi tự thay bằng một ô nhập khi
   * node đang được sửa. Bỏ trống = vẽ nhãn thường.
   */
  renderLabel?: (node: TreeNode<T>) => ReactNode
  /**
   * Chữ tooltip khi rê chuột qua CẢ DÒNG — dùng cho tên bị rút gọn/cắt bớt
   * (thư mục pháp nhân hiện `display_name` gọn nhưng tooltip cần tên pháp lý
   * đầy đủ + đường dẫn từ gốc). Trả `undefined`/chuỗi rỗng = không bọc
   * tooltip cho dòng đó (đỡ dựng `Tooltip.Root` cho MỌI dòng khi phần lớn
   * không cần). Cố ý CHUỖI THUẦN chứ không phải `ReactNode` như các `render*`
   * khác — tooltip chỉ cần chữ, không cần JSX.
   */
  getTooltip?: (node: TreeNode<T>) => string | undefined
  /**
   * KÉO THẢ NỘI BỘ (native HTML5 DnD, không phải `@dnd-kit` — hợp bài toán "node
   * A thả được vào node B không" hơn là "kéo thẻ giữa các cột" kiểu kanban).
   * Bốn props dưới đây tùy chọn, không phụ thuộc lẫn nhau; nơi gọi tự giữ
   * "đang kéo node nào" và tự tính hợp lệ bằng hàm thuần rồi trả qua `dropState`.
   */
  canDrag?: (node: TreeNode<T>) => boolean
  onDragStartNode?: (node: TreeNode<T>) => void
  /**
   * Như `onDragStartNode` nhưng kèm NGUYÊN `DragEvent` — dùng khi nơi gọi cần
   * tự ghi `dataTransfer` với MIME/hình dạng RIÊNG của nó (ví dụ lá văn bản
   * trong cây thư mục ghi payload kéo thả liên khung
   * `application/x-doc-folder-items`, xem `folder-drag-payload.ts`).
   * `onDragStartNode` không đọc được `dataTransfer` nên không thay được việc
   * này — hai props độc lập, nơi gọi dùng cái nào tùy nhu cầu, không loại trừ
   * nhau.
   */
  onDragStartEvent?: (node: TreeNode<T>, event: DragEvent<HTMLDivElement>) => void
  /** Kéo kết thúc (thả hợp lệ HOẶC hủy nửa chừng) — nơi gọi dọn state "đang kéo". */
  onDragEndNode?: () => void
  /** `undefined` = node này không phải đích thả (không tô, không nhận `drop`). */
  dropState?: (node: TreeNode<T>) => 'valid' | 'invalid' | undefined
  onDropNode?: (node: TreeNode<T>) => void
  /**
   * ĐỔI THỨ TỰ ANH EM (thả TRƯỚC/SAU một dòng, không đổi cha) — độc lập với
   * `dropState`/`onDropNode` (đổi CHA). `canReorderWith` trả `false`/bỏ trống
   * = dòng này không nhận kiểu thả này; `tree-row.tsx` tự chia vùng thả theo
   * con trỏ khi CẢ HAI khả năng cùng hợp lệ trên một dòng (`resolve-drop-zone.ts`).
   */
  canReorderWith?: (node: TreeNode<T>) => boolean
  onReorderDrop?: (node: TreeNode<T>, position: 'before' | 'after') => void
  /** Nhận payload NGOÀI cây (ví dụ kéo thẻ từ khung khác thả vào) — chỉ so MIME của `dataTransfer`, độc lập với `canDrag`/`dropState`. Bỏ trống = tắt hẳn. */
  externalDropMimeType?: string
  /** Dòng này có nhận payload ngoài không — bỏ trống = nhận hết (mọi dòng có MIME khớp). */
  acceptsExternalDrop?: (node: TreeNode<T>) => boolean
  onExternalDropNode?: (node: TreeNode<T>, event: DragEvent<HTMLDivElement>) => void
  className?: string
}

/**
 * CÂY CHỌN dùng chung — thư mục văn bản và cây tệp theo phiên bản (tab «Tệp»,
 * `document-file-tree.tsx`) đều dựng trên component này. KHÔNG chứa gì riêng
 * của văn bản hay thư mục. Theo đúng mẫu APG «treeview»: `role="tree"` bọc
 * ngoài, mỗi dòng `role="treeitem"` mang `aria-expanded`/`aria-selected` (vẽ ở
 * `tree-row.tsx`).
 *
 * Điều hướng ROVING TABINDEX — chỉ MỘT dòng nhận `tabIndex=0` (dòng giữ tiêu
 * điểm), còn lại `-1`; quy tắc ↑↓→←/Home/End nằm ở hàm thuần
 * `resolveTreeKeyAction` (`tree-keyboard-nav.ts`), tách ra để test không cần
 * dựng DOM.
 */
export function TreeView<T = unknown>({
  nodes,
  ariaLabel,
  selectedId = null,
  onSelect,
  onActivate,
  onFocusChange,
  onRowDoubleClick,
  expandedIds,
  onToggleExpand,
  highlightIds,
  renderIcon,
  renderBadge,
  renderTrailing,
  renderHoverActions,
  renderLabel,
  getTooltip,
  canDrag,
  onDragStartNode,
  onDragStartEvent,
  onDragEndNode,
  dropState,
  onDropNode,
  canReorderWith,
  onReorderDrop,
  externalDropMimeType,
  acceptsExternalDrop,
  onExternalDropNode,
  className,
}: TreeViewProps<T>) {
  const flat = useMemo(
    () => flattenTree(nodes, (id) => expandedIds.has(id)),
    [nodes, expandedIds],
  )
  const { focusedId, setFocusedId, toNode, handleKeyDown, refCallback } = useTreeViewRovingFocus({
    flat,
    selectedId,
    expandedIds,
    onToggleExpand,
    onSelect,
    onActivate,
    onFocusChange,
  })

  if (flat.length === 0) return null

  return (
    <div role="tree" aria-label={ariaLabel} className={cn('flex flex-col', className)}>
      {flat.map((row, index) => (
        <TreeRow
          key={row.id}
          row={row}
          node={toNode(row)}
          expanded={row.hasChildren ? expandedIds.has(row.id) : undefined}
          selected={selectedId !== null && selectedId !== undefined && row.id === selectedId}
          highlighted={highlightIds?.has(row.id) ?? false}
          focused={row.id === focusedId}
          drop={dropState?.(toNode(row))}
          reorderable={canReorderWith?.(toNode(row)) ?? false}
          draggable={canDrag?.(toNode(row)) ?? false}
          tooltip={getTooltip?.(toNode(row))}
          refCallback={refCallback(row.id)}
          onToggleExpand={onToggleExpand}
          onSelect={(node) => onSelect?.(node)}
          onRowDoubleClick={onRowDoubleClick}
          onFocusRow={setFocusedId}
          onKeyDownRow={(event) => handleKeyDown(event, index)}
          onDragStartNode={onDragStartNode}
          onDragStartEvent={onDragStartEvent}
          onDragEndNode={onDragEndNode}
          onDropNode={onDropNode}
          onReorderDrop={onReorderDrop}
          externalDropMimeType={externalDropMimeType}
          acceptsExternalDrop={acceptsExternalDrop}
          onExternalDropNode={onExternalDropNode}
          renderIcon={renderIcon}
          renderBadge={renderBadge}
          renderTrailing={renderTrailing}
          renderHoverActions={renderHoverActions}
          renderLabel={renderLabel}
        />
      ))}
    </div>
  )
}
