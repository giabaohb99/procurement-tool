import type { Editor } from '@tiptap/react'
import { selectedRect } from '@tiptap/pm/tables'

/**
 * Nhóm lệnh về BẢNG, khai một lần cho cả hai chỗ gọi: nút "Bảng" trên thanh
 * công cụ và mục "Bảng" trong menu chuột phải.
 *
 * Xếp theo đúng thứ tự menu bảng của Word: chèn → thêm hàng/cột → xóa → gộp
 * tách ô → hàng/cột tiêu đề → dọn dẹp bề ngang → xóa cả bảng.
 */
export interface TableCommand {
  label: string
  run: () => void
  /** Chỉ có nghĩa khi con trỏ đang nằm trong một bảng. */
  needsTable: boolean
  /** Vẽ vạch ngăn phía trên dòng này. */
  separatorBefore?: boolean
  destructive?: boolean
}

export function tableCommands(editor: Editor): TableCommand[] {
  const run = () => editor.chain().focus()

  return [
    {
      label: 'Chèn bảng 3×3',
      needsTable: false,
      run: () => run().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
    },

    {
      label: 'Thêm hàng bên trên',
      needsTable: true,
      separatorBefore: true,
      run: () => run().addRowBefore().run(),
    },
    { label: 'Thêm hàng bên dưới', needsTable: true, run: () => run().addRowAfter().run() },
    { label: 'Thêm cột bên trái', needsTable: true, run: () => run().addColumnBefore().run() },
    { label: 'Thêm cột bên phải', needsTable: true, run: () => run().addColumnAfter().run() },

    {
      label: 'Xóa hàng',
      needsTable: true,
      separatorBefore: true,
      run: () => run().deleteRow().run(),
    },
    { label: 'Xóa cột', needsTable: true, run: () => run().deleteColumn().run() },

    {
      label: 'Gộp ô',
      needsTable: true,
      separatorBefore: true,
      run: () => run().mergeCells().run(),
    },
    { label: 'Tách ô', needsTable: true, run: () => run().splitCell().run() },

    {
      label: 'Bật / tắt hàng tiêu đề',
      needsTable: true,
      separatorBefore: true,
      run: () => run().toggleHeaderRow().run(),
    },
    {
      label: 'Bật / tắt cột tiêu đề',
      needsTable: true,
      run: () => run().toggleHeaderColumn().run(),
    },
    {
      label: 'Chia đều bề ngang các cột',
      needsTable: true,
      // Xóa bề ngang đã kéo tay của từng ô; bảng đang `table-layout: fixed` nên
      // bỏ số đo ra là các cột tự chia đều nhau.
      run: () => run().setCellAttribute('colwidth', null).run(),
    },

    {
      label: 'Xóa bảng',
      needsTable: true,
      separatorBefore: true,
      destructive: true,
      run: () => run().deleteTable().run(),
    },
  ]
}

/** Đổ màu nền cho MỌI ô đang chọn (bôi đen cả hàng hay cả cột đều được). */
export function setCellBackground(editor: Editor, color: string | null) {
  editor.chain().focus().setCellAttribute('backgroundColor', color).run()
}

export type TableBorderPreset =
  'all' | 'outside' | 'inside' | 'top' | 'right' | 'bottom' | 'left' | 'none'

type BorderSide = 'top' | 'right' | 'bottom' | 'left'

const BORDER_ATTRIBUTE: Record<BorderSide, string> = {
  top: 'borderTop',
  right: 'borderRight',
  bottom: 'borderBottom',
  left: 'borderLeft',
}

/**
 * Áp kiểu viền lên vùng ô đang chọn.
 *
 * `setCellAttribute` chỉ biết ghi cùng một thuộc tính cho mọi ô, không biết ô
 * nào nằm ở mép ngoài hay bên trong vùng chọn. Dùng `TableMap` để xác định vị
 * trí từng ô, nhờ đó các preset viền hoạt động giống Word cả khi chọn nhiều ô.
 */
export function setCellBorders(editor: Editor, preset: TableBorderPreset, borderValue: string) {
  if (!editor.isActive('table')) return

  const rect = selectedRect(editor.state)
  const transaction = editor.state.tr

  for (const offset of rect.map.cellsInRect(rect)) {
    const position = rect.tableStart + offset
    const cell = transaction.doc.nodeAt(position)
    if (!cell) continue

    const cellRect = rect.map.findCell(offset)
    const sides = borderSidesForCell(preset, rect, cellRect)
    if (sides.length === 0) continue

    const attrs = { ...cell.attrs }
    for (const side of sides) {
      // `hidden` giống `none` nhưng thắng viền của ô liền kề khi bảng dùng
      // `border-collapse: collapse`, nhờ vậy lệnh Không viền xóa đúng đường kẻ.
      attrs[BORDER_ATTRIBUTE[side]] = preset === 'none' ? 'hidden' : borderValue
    }
    transaction.setNodeMarkup(position, undefined, attrs)
  }

  if (transaction.docChanged) editor.view.dispatch(transaction)
  editor.view.focus()
}

interface CellRect {
  top: number
  right: number
  bottom: number
  left: number
}

function borderSidesForCell(
  preset: TableBorderPreset,
  selected: CellRect,
  cell: CellRect,
): BorderSide[] {
  if (preset === 'all' || preset === 'none') return ['top', 'right', 'bottom', 'left']
  if (preset === 'top') return cell.top === selected.top ? ['top'] : []
  if (preset === 'right') return cell.right === selected.right ? ['right'] : []
  if (preset === 'bottom') return cell.bottom === selected.bottom ? ['bottom'] : []
  if (preset === 'left') return cell.left === selected.left ? ['left'] : []

  const sides: BorderSide[] = []
  if (preset === 'outside') {
    if (cell.top === selected.top) sides.push('top')
    if (cell.right === selected.right) sides.push('right')
    if (cell.bottom === selected.bottom) sides.push('bottom')
    if (cell.left === selected.left) sides.push('left')
  } else {
    if (cell.top > selected.top) sides.push('top')
    if (cell.right < selected.right) sides.push('right')
    if (cell.bottom < selected.bottom) sides.push('bottom')
    if (cell.left > selected.left) sides.push('left')
  }
  return sides
}
