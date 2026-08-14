import { TableRow } from '@tiptap/extension-table'
import { Plugin } from '@tiptap/pm/state'
import type { EditorView } from '@tiptap/pm/view'

/** Bắt được mép hàng trong khoảng này (px) thì cho kéo. */
const EDGE = 5

/** Hàng không được bóp thấp hơn ngần này, không thì chữ bị cắt cụt. */
const MIN_ROW_HEIGHT = 24

/**
 * KÉO GIÃN CHIỀU CAO HÀNG của bảng.
 *
 * ProseMirror chỉ dựng sẵn phần kéo giãn CỘT; hàng thì không có, nên phải tự
 * làm: rê chuột tới mép dưới một hàng thì con trỏ đổi thành mũi tên hai chiều,
 * kéo là hàng cao lên / thấp xuống NGAY theo tay, y như kéo cột.
 */
export const TableRowWithHeight = TableRow.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      height: {
        default: null,
        parseHTML: (element) => {
          const height = Number.parseInt(element.style.height, 10)
          return Number.isFinite(height) ? height : null
        },
        renderHTML: (attributes) =>
          attributes.height ? { style: `height: ${attributes.height}px` } : {},
      },
    }
  },

  addProseMirrorPlugins() {
    return [rowResizingPlugin()]
  },
})

interface RowDrag {
  /** Vị trí của hàng TRONG TÀI LIỆU, không phải thẻ DOM. */
  pos: number
  startY: number
  startHeight: number
  scale: number
  /** Chiều cao trước khi kéo, để gộp cả lần kéo thành MỘT bước hoàn tác. */
  originalHeight: number | null
  height: number
  frame: number | null
}

/**
 * Trong lúc kéo, chiều cao ghi THẲNG vào tài liệu theo từng khung hình nhưng
 * đánh dấu "đừng vào lịch sử".
 *
 * Không sửa `style` của thẻ `<tr>` cho nhanh được: ProseMirror vẽ lại thẻ theo
 * thuộc tính trong tài liệu (mà `tiptap-pagination-plus` thì tính lại trang
 * liên tục), nên style đặt tay bị xóa ngay — mắt chỉ thấy hàng nhảy một phát
 * lúc buông tay chứ không chạy theo con trỏ.
 *
 * Buông tay mới ghi một bước vào lịch sử: trả về chiều cao cũ rồi đặt lại chiều
 * cao mới, nhờ vậy Ctrl+Z một lần là về đúng trước khi kéo, thay vì phải bấm
 * mấy chục lần cho từng nhịp chuột.
 */
function rowResizingPlugin() {
  let drag: RowDrag | null = null

  function applyHeight(view: EditorView, pos: number, height: number | null, record: boolean) {
    const node = view.state.doc.nodeAt(pos)
    if (!node || node.type.name !== 'tableRow') return
    if (node.attrs.height === height) return

    const tr = view.state.tr.setNodeMarkup(pos, undefined, { ...node.attrs, height })
    if (!record) tr.setMeta('addToHistory', false)
    view.dispatch(tr)
  }

  function stopDrag(view: EditorView) {
    if (!drag) return
    const { pos, height, originalHeight, frame } = drag
    drag = null
    if (frame !== null) cancelAnimationFrame(frame)

    applyHeight(view, pos, originalHeight, false)
    applyHeight(view, pos, height, true)
  }

  return new Plugin({
    props: {
      handleDOMEvents: {
        // Chỉ lo phần đổi con trỏ; việc kéo nghe ở `window` (xem `mousedown`).
        mousemove(view, event) {
          if (drag) return false
          view.dom.classList.toggle('row-resize-cursor', Boolean(rowAtEdge(view, event)))
          return false
        },

        mousedown(view, event) {
          const row = rowAtEdge(view, event)
          if (!row) return false

          const pos = rowPosition(view, row)
          if (pos === null) return false
          event.preventDefault()

          // `getBoundingClientRect` đã nhân mức phóng của trang, còn
          // `offsetHeight` thì chưa — chia hai số ấy ra đúng hệ số đang phóng.
          const rect = row.getBoundingClientRect()
          const scale = row.offsetHeight ? rect.height / row.offsetHeight : 1
          drag = {
            pos,
            startY: event.clientY,
            startHeight: row.offsetHeight,
            scale,
            originalHeight: view.state.doc.nodeAt(pos)?.attrs.height ?? null,
            height: row.offsetHeight,
            frame: null,
          }

          // Nghe ở `window` chứ không ở vùng soạn thảo: kéo mạnh tay là con trỏ
          // chạy ra ngoài tờ giấy, mà lúc đó vẫn phải theo cho tới khi buông.
          const move = (moveEvent: MouseEvent) => {
            if (!drag) return
            const delta = (moveEvent.clientY - drag.startY) / drag.scale
            drag.height = Math.round(Math.max(MIN_ROW_HEIGHT, drag.startHeight + delta))
            // Gộp theo khung hình: chuột bắn ra cả trăm nhịp mỗi giây, ghi từng
            // nhịp thì thư viện chia trang tính lại chừng ấy lần, kéo thành giật.
            if (drag.frame !== null) return
            drag.frame = requestAnimationFrame(() => {
              if (!drag) return
              drag.frame = null
              applyHeight(view, drag.pos, drag.height, false)
            })
          }

          const stop = () => {
            window.removeEventListener('mousemove', move)
            window.removeEventListener('mouseup', stop)
            stopDrag(view)
          }

          window.addEventListener('mousemove', move)
          window.addEventListener('mouseup', stop)
          return true
        },
      },
    },
  })
}

/** Vị trí của nút `tableRow` chứa thẻ `<tr>` này. */
function rowPosition(view: EditorView, row: HTMLTableRowElement): number | null {
  const inside = view.posAtDOM(row, 0)
  if (inside < 0) return null

  const $pos = view.state.doc.resolve(inside)
  for (let depth = $pos.depth; depth > 0; depth -= 1) {
    if ($pos.node(depth).type.name === 'tableRow') return $pos.before(depth)
  }
  return null
}

/** Hàng có mép trên/dưới nằm ngay dưới con trỏ, hoặc `null` nếu không có. */
function rowAtEdge(view: EditorView, event: MouseEvent): HTMLTableRowElement | null {
  const target = event.target as HTMLElement | null
  if (!target || !view.dom.contains(target)) return null

  const row = target.closest('tr')
  if (!row || !view.dom.contains(row)) return null

  const rect = row.getBoundingClientRect()
  if (Math.abs(event.clientY - rect.bottom) <= EDGE) return row as HTMLTableRowElement
  // Đứng sát mép TRÊN thì người dùng đang nhắm mép dưới của hàng liền trước —
  // hai mép đó là một đường kẻ, chọn nhầm hàng là kéo ra kết quả ngược ý.
  if (Math.abs(event.clientY - rect.top) <= EDGE) {
    return (row.previousElementSibling as HTMLTableRowElement) ?? null
  }
  return null
}
