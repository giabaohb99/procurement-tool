import type Quill from 'quill'
import { Quill as QuillStatic } from 'react-quill'
import TableModule from 'quill1-table'
import 'quill1-table/src/css/quill.table.css'

import { registerTableCellWidth } from '@/lib/quill-table-column-resize'

// Bảng cho trình soạn thảo.
//
// Quill 1.3.7 (bản react-quill@2 dùng) KHÔNG có sẵn module bảng — bật `modules: { table: true }`
// sẽ ném "moduleClass is not a constructor". Dùng `quill1-table`: bản port của quill-better-table
// sang Quill 1, không kéo theo dependency runtime nào, có gộp/tách ô và undo/redo trong bảng.
//
// Thư viện vốn thiết kế để gắn nút vào thanh công cụ của Quill. Ở đây gọi thẳng handler `table`
// mà module tự đăng ký, nhờ vậy menu "Bảng" giữ được giao diện shadcn + nhãn tiếng Việt.

/** Lệnh của quill1-table (xem `table_handler` trong thư viện). Chèn bảng là `newtable_<hàng>_<cột>`. */
export type TableCommand =
  | 'append-row-above' | 'append-row-below'
  | 'append-col-before' | 'append-col-after'
  | 'merge-selection' | 'split-cell'
  | 'remove-row' | 'remove-col' | 'remove-table'

export interface TableActionItem {
  key: TableCommand
  label: string
  /** Thao tác xóa — hiện màu cảnh báo trong menu. */
  danger?: boolean
}

/** Các thao tác trên bảng đang đặt con trỏ, theo thứ tự hiện trong menu. */
export const TABLE_ACTIONS: TableActionItem[] = [
  { key: 'append-row-above', label: 'Chèn hàng phía trên' },
  { key: 'append-row-below', label: 'Chèn hàng phía dưới' },
  { key: 'append-col-before', label: 'Chèn cột bên trái' },
  { key: 'append-col-after', label: 'Chèn cột bên phải' },
  { key: 'merge-selection', label: 'Gộp các ô đang chọn' },
  { key: 'split-cell', label: 'Tách ô đã gộp' },
  { key: 'remove-row', label: 'Xóa hàng hiện tại', danger: true },
  { key: 'remove-col', label: 'Xóa cột hiện tại', danger: true },
  { key: 'remove-table', label: 'Xóa cả bảng', danger: true },
]

/** Số hàng/cột tối đa cho lưới chọn nhanh khi chèn bảng mới. */
export const TABLE_GRID_MAX = 6

/** Tùy chọn module truyền vào `modules.table` của Quill. */
export const TABLE_MODULE_OPTIONS = { cellSelectionOnClick: true }

/**
 * Phím tắt bắt buộc của quill1-table (truyền vào `modules.keyboard.bindings`).
 * Quill gắn handler mặc định ngay lúc khởi tạo nên chỉ chặn được bằng cách khai báo từ đầu —
 * thiếu phần này thì Backspace/Delete trong ô sẽ phá cấu trúc bảng và Ctrl+Z không hoàn tác đúng.
 */
export const TABLE_KEYBOARD_BINDINGS = {
  backspace: {
    key: 'backspace',
    handler(this: { quill: Quill }, range: unknown, context: unknown) {
      return TableModule.keyboardHandler(this.quill, 'backspace', range, context)
    },
  },
  delete: {
    key: 'delete',
    handler(this: { quill: Quill }, range: unknown, context: unknown) {
      return TableModule.keyboardHandler(this.quill, 'delete', range, context)
    },
  },
  undo: {
    shortKey: true,
    key: 'z',
    handler(this: { quill: Quill }, range: unknown, context: unknown) {
      return TableModule.keyboardHandler(this.quill, 'undo', range, context)
    },
  },
  redo: {
    shortKey: true,
    shiftKey: true,
    key: 'z',
    handler(this: { quill: Quill }, range: unknown, context: unknown) {
      return TableModule.keyboardHandler(this.quill, 'redo', range, context)
    },
  },
}

let registered = false

/** Đăng ký module bảng vào Quill (gọi được nhiều lần). Phải chạy TRƯỚC khi dựng editor. */
export function registerTableModule(): void {
  if (registered) return
  QuillStatic.register('modules/table', TableModule as never, true)
  TableModule.register() // blot table/tr/td/contain
  registerTableCellWidth() // nới blot ô để nhớ độ rộng cột
  registered = true
}

/** Handler `table` do module tự gắn vào thanh công cụ — là đường vào duy nhất của thư viện. */
function tableHandler(quill: Quill | null | undefined): ((value: string) => void) | null {
  if (!quill) return null
  const toolbar = quill.getModule('toolbar') as { handlers?: Record<string, unknown> } | undefined
  const handler = toolbar?.handlers?.table
  return typeof handler === 'function' ? (handler as (value: string) => void).bind(toolbar) : null
}

/** Editor hiện tại có dùng được bảng hay không — không có thì ẩn nút Bảng. */
export function hasTableSupport(quill: Quill | null | undefined): boolean {
  return tableHandler(quill) !== null
}

/** Chèn bảng mới tại con trỏ. Cần focus trước vì thư viện đọc vùng chọn hiện hành. */
export function insertTable(quill: Quill | null | undefined, rows: number, columns: number): boolean {
  const handler = tableHandler(quill)
  if (!handler || !quill) return false
  quill.focus()
  quill.getSelection(true)
  handler(`newtable_${rows}_${columns}`)
  return true
}

/** Chạy 1 thao tác trên bảng đang đặt con trỏ. Trả false nếu con trỏ không nằm trong bảng. */
export function runTableAction(quill: Quill | null | undefined, command: TableCommand): boolean {
  const handler = tableHandler(quill)
  if (!handler || !quill) return false
  try {
    handler(command)
    return true
  } catch {
    // Thư viện ném lỗi khi không xác định được ô đang đứng
    return false
  }
}
