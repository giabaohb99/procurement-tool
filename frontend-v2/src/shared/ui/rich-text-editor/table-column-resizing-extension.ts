import { Table } from '@tiptap/extension-table'
import { TableMap } from '@tiptap/pm/tables'
import { Plugin } from '@tiptap/pm/state'
import type { Node as ProseMirrorNode } from '@tiptap/pm/model'
import type { EditorView } from '@tiptap/pm/view'

/** Bắt được ranh giới cột trong khoảng này (px) thì cho kéo. */
const EDGE = 5

/** Cột không hẹp hơn ngần này, không thì chữ rơi thành từng ký tự một dòng. */
const MIN_COL_WIDTH = 32

/**
 * KÉO GIÃN CỘT kiểu Word: kéo một ranh giới thì cột bên trái và cột bên phải
 * CHIA NHAU chỗ đó, TỔNG BỀ NGANG BẢNG KHÔNG ĐỔI.
 *
 * Không dùng phần kéo cột dựng sẵn của ProseMirror: nó chỉ nới đúng cột đang
 * kéo, tổng bề ngang bảng phình theo, mà bảng đã ghi bề rộng cột thành px thì
 * đó thành bề rộng tối thiểu — CSS không ép nhỏ lại được nữa, kết quả là bảng
 * thò ra khỏi khổ giấy kèm một thanh cuộn ngang. Văn bản in ra giấy thì không
 * có chỗ nào để cuộn.
 *
 * Cách ghi giống phần kéo cao hàng (`table-row-resizing-extension.ts`): trong
 * lúc kéo ghi thẳng vào tài liệu nhưng đánh dấu "đừng vào lịch sử", buông tay
 * mới chốt một bước — Ctrl+Z một lần là về đúng trước khi kéo.
 */
export const TableWithColumnResizing = Table.extend({
  addProseMirrorPlugins() {
    // GIỮ LẠI plugin gốc rồi mới nối bản kéo cột của mình vào: trong đó có
    // `tableEditing` — thứ làm nên việc bôi đen cả hàng, cả cột, gộp ô. Ghi đè
    // trắng hàm này là mất sạch, bảng thành không chọn được gì.
    //
    // Đặt bản của mình lên TRƯỚC để nó nhận chuột ở mép cột trước phần kéo cột
    // dựng sẵn (bản dựng sẵn đã tắt bằng `resizable: false`, đây là rào thứ hai).
    return [columnResizingPlugin(), ...(this.parent?.() ?? [])]
  },
})

interface ColumnDrag {
  tablePos: number
  /** Ranh giới nằm giữa cột này và cột liền sau. */
  boundary: number
  startX: number
  scale: number
  /** Bề rộng mọi cột lúc bắt đầu kéo, và bản đang kéo dở. */
  startWidths: number[]
  widths: number[]
  frame: number | null
}

function columnResizingPlugin() {
  let drag: ColumnDrag | null = null

  function stopDrag(view: EditorView) {
    if (!drag) return
    const { tablePos, startWidths, widths, frame } = drag
    drag = null
    if (frame !== null) cancelAnimationFrame(frame)

    applyWidths(view, tablePos, startWidths, false)
    applyWidths(view, tablePos, widths, true)
  }

  return new Plugin({
    props: {
      handleDOMEvents: {
        mousemove(view, event) {
          if (drag) return false
          view.dom.classList.toggle('resize-cursor', Boolean(boundaryAt(view, event)))
          return false
        },

        mousedown(view, event) {
          const found = boundaryAt(view, event)
          if (!found) return false
          event.preventDefault()

          const { tablePos, boundary, widths, scale } = found
          drag = {
            tablePos,
            boundary,
            startX: event.clientX,
            scale,
            startWidths: widths,
            widths,
            frame: null,
          }

          // Nghe ở `window`: kéo mạnh tay là con trỏ chạy ra ngoài tờ giấy, mà
          // lúc đó vẫn phải theo cho tới khi buông.
          const move = (moveEvent: MouseEvent) => {
            if (!drag) return
            const delta = (moveEvent.clientX - drag.startX) / drag.scale
            drag.widths = shareWidth(drag.startWidths, drag.boundary, delta)
            // Gộp theo khung hình: chuột bắn cả trăm nhịp mỗi giây, ghi từng
            // nhịp thì thư viện chia trang tính lại chừng ấy lần, kéo thành giật.
            if (drag.frame !== null) return
            drag.frame = requestAnimationFrame(() => {
              if (!drag) return
              drag.frame = null
              applyWidths(view, drag.tablePos, drag.widths, false)
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

/**
 * Dồn `delta` px từ cột bên phải sang cột bên trái của ranh giới (hoặc ngược
 * lại), giữ nguyên tổng — đây chính là chỗ làm cho bảng không bao giờ quá khổ.
 */
function shareWidth(widths: number[], boundary: number, delta: number): number[] {
  const pair = widths[boundary] + widths[boundary + 1]
  const left = Math.round(
    Math.min(Math.max(widths[boundary] + delta, MIN_COL_WIDTH), pair - MIN_COL_WIDTH),
  )
  const next = [...widths]
  next[boundary] = left
  next[boundary + 1] = pair - left
  return next
}

/** Ghi bề rộng cột vào MỌI ô của bảng (mỗi ô giữ phần bề rộng của riêng nó). */
function applyWidths(view: EditorView, tablePos: number, widths: number[], record: boolean) {
  const table = view.state.doc.nodeAt(tablePos)
  if (!table || table.type.name !== 'table') return

  const map = TableMap.get(table)
  const tr = view.state.tr
  const seen = new Set<number>()

  for (let row = 0; row < map.height; row += 1) {
    for (let col = 0; col < map.width; col += 1) {
      const offset = map.map[row * map.width + col]
      if (seen.has(offset)) continue
      seen.add(offset)

      const cell = table.nodeAt(offset)
      if (!cell) continue
      const span = (cell.attrs.colspan as number) ?? 1
      const colwidth = Array.from({ length: span }, (_, index) => widths[col + index] ?? 0)
      if (String(cell.attrs.colwidth) === String(colwidth)) continue

      tr.setNodeMarkup(tablePos + 1 + offset, undefined, { ...cell.attrs, colwidth })
    }
  }

  if (!tr.docChanged) return
  if (!record) tr.setMeta('addToHistory', false)
  view.dispatch(tr)
}

interface Boundary {
  tablePos: number
  boundary: number
  widths: number[]
  scale: number
}

/** Ranh giới cột nằm ngay dưới con trỏ, kèm bề rộng hiện tại của mọi cột. */
function boundaryAt(view: EditorView, event: MouseEvent): Boundary | null {
  const target = event.target as HTMLElement | null
  const cellElement = target?.closest('td, th')
  if (!cellElement || !view.dom.contains(cellElement)) return null

  const rect = cellElement.getBoundingClientRect()
  const atRight = Math.abs(event.clientX - rect.right) <= EDGE
  const atLeft = Math.abs(event.clientX - rect.left) <= EDGE
  if (!atRight && !atLeft) return null

  const table = tableAround(view, cellElement)
  if (!table) return null

  // Cột đầu tiên mà ô này chiếm; đứng ở mép trái thì ranh giới là mép phải của
  // cột liền trước.
  const cellRect = TableMap.get(table.node).findCell(table.cellOffset)
  const boundary = atRight ? cellRect.right - 1 : cellRect.left - 1
  // Mép ngoài cùng của bảng chính là mép lề trang, kéo nó chẳng chia được gì.
  if (boundary < 0 || boundary >= TableMap.get(table.node).width - 1) return null

  const widths = measureColumns(table.element)
  if (!widths) return null

  // Ép tổng về đúng bề ngang vùng chữ NGAY TỪ ĐẦU: bảng đã lỡ quá khổ từ trước
  // (dán từ Word về, hay do bản cũ của trình soạn thảo) thì chỉ cần chạm vào
  // một ranh giới là nó co lại vừa trang, chứ không giữ nguyên cái sai.
  const available = table.element.parentElement?.clientWidth ?? 0
  const fitted = available > 0 ? scaleToFit(widths, available) : widths

  // `getBoundingClientRect` đã nhân mức phóng của trang, `offsetWidth` thì chưa.
  const scale = table.element.offsetWidth
    ? table.element.getBoundingClientRect().width / table.element.offsetWidth
    : 1

  return { tablePos: table.pos, boundary, widths: fitted, scale }
}

/** Co giãn đều mọi cột để tổng đúng bằng `available`, cột nào cũng còn đọc được. */
function scaleToFit(widths: number[], available: number): number[] {
  const total = widths.reduce((sum, width) => sum + width, 0)
  if (!total || Math.abs(total - available) <= 1) return widths

  const scaled = widths.map((width) =>
    Math.max(MIN_COL_WIDTH, Math.round((width / total) * available)),
  )
  // Làm tròn xong thường dư/thiếu vài px — dồn hết vào cột rộng nhất để tổng
  // khớp tuyệt đối, cột rộng nhất thì lệch mấy px cũng không ai thấy.
  const drift = available - scaled.reduce((sum, width) => sum + width, 0)
  const widest = scaled.indexOf(Math.max(...scaled))
  scaled[widest] = Math.max(MIN_COL_WIDTH, scaled[widest] + drift)
  return scaled
}

interface TableAround {
  pos: number
  node: ProseMirrorNode
  /** Vị trí của ô, tính từ đầu nội dung bảng (kiểu của `TableMap`). */
  cellOffset: number
  element: HTMLTableElement
}

function tableAround(view: EditorView, cellElement: Element): TableAround | null {
  const element = cellElement.closest('table')
  if (!element) return null

  const inside = view.posAtDOM(cellElement, 0)
  if (inside < 0) return null

  const $pos = view.state.doc.resolve(inside)
  for (let depth = $pos.depth; depth > 0; depth -= 1) {
    if ($pos.node(depth).type.name !== 'table') continue
    const pos = $pos.before(depth)
    // Ô nằm ở độ sâu ngay dưới hàng, tức sâu hơn bảng hai bậc.
    const cellPos = $pos.before(depth + 2)
    return { pos, node: $pos.node(depth), cellOffset: cellPos - pos - 1, element }
  }
  return null
}

/** Bề rộng thật của từng cột, đọc từ hàng đầu của bảng. */
function measureColumns(element: HTMLTableElement): number[] | null {
  const row = element.rows[0]
  if (!row) return null

  const widths: number[] = []
  for (const cell of row.cells) {
    const span = cell.colSpan || 1
    // Ô gộp nhiều cột thì chia đều cho các cột nó chiếm — không có cách nào
    // biết chính xác hơn, mà chia đều thì tổng vẫn đúng.
    const each = Math.round(cell.offsetWidth / span)
    for (let index = 0; index < span; index += 1) widths.push(each)
  }
  return widths
}
