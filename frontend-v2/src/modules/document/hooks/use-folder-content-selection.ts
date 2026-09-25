import { useMemo } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useItemSelection } from './use-item-selection'

interface UseFolderContentSelectionArgs {
  /** Khóa THƯ MỤC con đang hiển thị, đúng thứ tự trên màn hình (`folder:<id>`). */
  folderKeys: readonly string[]
  /** Khóa VĂN BẢN của TRANG đang hiển thị, đúng thứ tự (`document:<id>`). */
  documentKeys: readonly string[]
  /**
   * Chữ ký đổi là XÓA lựa chọn — PHẢI gồm thư mục đang xem, mọi điều kiện lọc,
   * và số trang. Thiếu một trong ba là bấm hàng loạt có thể động tới dòng của
   * NGỮ CẢNH CŨ đang không còn hiển thị (rà soát code-reviewer 23/09/2026,
   * M10): chọn 5 văn bản ở thư mục A rồi sang thư mục B, «Chuyển tới…» phải
   * không còn gì để chuyển — không phải âm thầm áp lên 5 văn bản cũ.
   */
  resetSignal: unknown
}

/**
 * Selection HỢP NHẤT cho khung nội dung thư mục — bọc {@link useItemSelection}
 * (chọn kiểu Drive, bấm/Ctrl/Shift/Esc/Ctrl+A) và CỘNG THÊM luật riêng của
 * màn này: đổi thư mục/bộ lọc/trang thì lựa chọn cũ hết ý nghĩa, phải xóa
 * ngay — không đợi người dùng tự bấm «Bỏ chọn».
 *
 * Xóa NGAY TRONG RENDER (không `useEffect`) — cùng mẫu chính thức React đã
 * dùng ở `useHasChanged`/`usePageResetOnFilterChange` của chính repo này:
 * `selection` là state CỤC BỘ trong cùng cây hook, không phải state của một
 * component KHÁC (khác hẳn lỗi đã vá ở `folder-documents-table.tsx`, nơi từng
 * gọi thẳng `setSearchParams` — thay đổi của Router — ngay trong render).
 */
export function useFolderContentSelection({
  folderKeys,
  documentKeys,
  resetSignal,
}: UseFolderContentSelectionArgs) {
  const orderedKeys = useMemo(() => [...folderKeys, ...documentKeys], [folderKeys, documentKeys])
  const selection = useItemSelection(orderedKeys)

  if (useHasChanged(JSON.stringify(resetSignal)) && selection.selectedIds.size > 0) {
    selection.clear()
  }

  return selection
}
