import type { SelectionModifierKeys } from '../hooks/use-item-selection'

/**
 * Luật BẤM trên một mục của khung nội dung thư mục (thư mục con · văn bản, cả
 * chế độ Danh sách lẫn Lưới) — chốt 24/09/2026: **bấm MỘT LẦN là MỞ**, thay
 * cho bấm đúp (người dùng không quen bấm đúp trên web, bấm một lần chỉ thấy
 * dòng đổi màu rồi tưởng hỏng). Chọn nhiều vẫn còn nhưng phải kèm phím:
 * Ctrl/⌘+bấm = thêm/bớt, Shift+bấm = chọn dải — đúng luật `useItemSelection`.
 *
 * Một hàm dùng chung cho ba nơi (`FolderListRow`, `FolderGridDocumentCard`,
 * `FolderChildCards`) để ba chế độ không lệch nhau.
 */
export function dispatchFolderItemClick(
  modifiers: SelectionModifierKeys,
  handlers: { onSelect: (modifiers: SelectionModifierKeys) => void; onOpen: () => void },
): void {
  if (modifiers.ctrlKey || modifiers.metaKey || modifiers.shiftKey) handlers.onSelect(modifiers)
  else handlers.onOpen()
}

/** Đọc ĐÚNG ba phím bổ trợ từ sự kiện chuột — tránh truyền cả `MouseEvent` đi xa. */
export function readModifierKeys(event: SelectionModifierKeys): SelectionModifierKeys {
  return { ctrlKey: event.ctrlKey, metaKey: event.metaKey, shiftKey: event.shiftKey }
}
