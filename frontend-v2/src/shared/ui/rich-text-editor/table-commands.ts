import type { Editor } from '@tiptap/react'

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
