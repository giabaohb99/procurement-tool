import type Quill from 'quill'
import { Quill as QuillStatic } from 'react-quill'

// Kéo giãn cột cho bảng trong trình soạn thảo.
//
// quill1-table KHÔNG có sẵn tính năng này, và blot ô của nó chỉ round-trip đúng 7 thuộc tính
// (`table_id|row_id|cell_id|merge_id|colspan|rowspan|hide_border`) — mọi style/class khác đặt lên
// <td> đều MẤT khi tải lại bài. Nên ở đây phải làm hai việc:
//   1. Nới blot ô thêm trường thứ 8 = độ rộng cột, và thêm matcher đọc lại độ rộng khi nạp HTML.
//   2. Bắt sự kiện chuột ở mép phải ô để kéo giãn.
//
// ⚠️ Chỗ này bám vào cấu trúc bên trong của quill1-table. Nâng cấp thư viện thì kiểm tra lại
// `TableCellBlot.formats()` và matcher `TD, TH` trong index.js của thư viện.

/** Thuộc tính lưu độ rộng trên chính thẻ <td> (đơn vị px). */
const WIDTH_ATTR = 'width_q'

/** Vị trí trường độ rộng trong chuỗi giá trị của blot ô. */
const WIDTH_INDEX = 7

/** Cột không được hẹp hơn mức này, nếu không sẽ không còn chỗ để bắt lại mép kéo. */
const MIN_WIDTH = 48

/** Bề rộng vùng bắt chuột ở mép phải ô. */
const EDGE = 6

function applyWidth(node: HTMLElement, width: number): void {
  const px = Math.max(MIN_WIDTH, Math.round(width))
  node.setAttribute(WIDTH_ATTR, String(px))
  node.style.width = `${px}px`
}

let patched = false

/**
 * Nới blot ô của quill1-table để nhớ độ rộng cột.
 * Phải gọi SAU khi module bảng đã đăng ký blot `td`.
 */
export function registerTableCellWidth(): void {
  if (patched) return
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const TableCellBase: any = QuillStatic.import('formats/td')
  if (!TableCellBase) return

  class TableCellWithWidth extends TableCellBase {
    static create(value: string): HTMLElement {
      const node = super.create(value) as HTMLElement
      const width = Number((value || '').split('|')[WIDTH_INDEX])
      if (Number.isFinite(width) && width > 0) applyWidth(node, width)
      return node
    }

    formats(): Record<string, unknown> {
      const base = super.formats() as Record<string, string>
      const node = (this as unknown as { domNode: HTMLElement }).domNode
      const width = node.getAttribute(WIDTH_ATTR) || ''
      return { ...base, td: `${base.td}|${width}` }
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  QuillStatic.register(TableCellWithWidth as any, true)
  patched = true
}

/**
 * Đọc lại độ rộng khi Quill nạp HTML.
 *
 * PHẢI đăng ký trên từng instance SAU khi module bảng dựng xong: matcher của thư viện ghi đè
 * thuộc tính `td` bằng đúng 7 trường, matcher nào chạy trước sẽ bị nó xoá mất phần độ rộng.
 */
export function attachTableWidthMatcher(quill: Quill): void {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Delta: any = QuillStatic.import('delta')

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  quill.clipboard.addMatcher('TD, TH', (node: HTMLElement, delta: any) => {
    const width = node.getAttribute?.(WIDTH_ATTR)
    if (!width) return delta
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const ops = delta.ops.map((op: any) => (op.attributes?.td
      ? { ...op, attributes: { ...op.attributes, td: `${op.attributes.td}|${width}` } }
      : op))
    return new Delta(ops)
  })
}

/**
 * Bật kéo giãn cột trên một editor. Trả hàm gỡ bỏ.
 *
 * `onCommit` được gọi khi thả chuột để nơi gọi đồng bộ lại nội dung (đánh dấu "chưa lưu").
 */
export function attachTableColumnResize(quill: Quill, onCommit: () => void): () => void {
  const root = quill.root as HTMLElement
  let drag: { cells: HTMLElement[]; startX: number; startWidth: number } | null = null

  /** Ô có mép phải nằm ngay dưới con trỏ — chỉ khi đó mới kéo giãn. */
  const cellAtEdge = (e: MouseEvent): HTMLElement | null => {
    const target = e.target as HTMLElement | null
    const cell = target?.closest?.('td') as HTMLElement | null
    if (!cell || !root.contains(cell)) return null
    const rect = cell.getBoundingClientRect()
    return e.clientX >= rect.right - EDGE && e.clientX <= rect.right + EDGE ? cell : null
  }

  const onMouseMove = (e: MouseEvent) => {
    if (drag) {
      const width = drag.startWidth + (e.clientX - drag.startX)
      drag.cells.forEach((cell) => applyWidth(cell, width))
      e.preventDefault()
      return
    }
    root.style.cursor = cellAtEdge(e) ? 'col-resize' : ''
  }

  const onMouseDown = (e: MouseEvent) => {
    const cell = cellAtEdge(e)
    if (!cell) return
    const table = cell.closest('table')
    if (!table) return

    // Ghi độ rộng lên MỌI ô cùng cột để mỗi ô tự lưu được, không phụ thuộc hàng đầu còn hay mất
    const index = (cell as HTMLTableCellElement).cellIndex
    const cells = Array.from(table.rows)
      .map((row) => row.cells[index] as HTMLElement | undefined)
      .filter((c): c is HTMLElement => !!c)

    drag = { cells, startX: e.clientX, startWidth: cell.getBoundingClientRect().width }
    // Chặn sớm để thao tác chọn ô của quill1-table không cướp mất cú kéo
    e.preventDefault()
    e.stopPropagation()
  }

  const onMouseUp = () => {
    if (!drag) return
    drag = null
    root.style.cursor = ''
    // update() cho Quill quét lại DOM -> formats() đọc thuộc tính mới, delta khớp với màn hình
    quill.update('user')
    onCommit()
  }

  root.addEventListener('mousemove', onMouseMove)
  // capture: chạy trước listener chọn ô mà quill1-table gắn ở quill.container
  root.addEventListener('mousedown', onMouseDown, true)
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)

  return () => {
    root.removeEventListener('mousemove', onMouseMove)
    root.removeEventListener('mousedown', onMouseDown, true)
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
}
