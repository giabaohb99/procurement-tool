import { Extension } from '@tiptap/core'
import { Plugin } from '@tiptap/pm/state'

import { containsHtmlTable, tabSeparatedTextToTableHtml } from './spreadsheet-clipboard'

/**
 * DÁN BẢNG TỪ EXCEL / GOOGLE SHEETS.
 *
 * Có HTML `<table>` thì không tự chạm vào: plugin `tableEditing` của
 * ProseMirror sẽ rải đúng từng ô vào vùng bảng đang bôi đen. Chỉ khi clipboard
 * còn mỗi TSV mới dựng lại một bảng HTML rồi đưa qua CHÍNH đường paste đó.
 */
export const SpreadsheetPaste = Extension.create({
  name: 'spreadsheetPaste',

  // Chạy trước plugin ảnh. Dù thứ tự extension bị đổi về sau, dữ liệu TSV vẫn
  // phải được nhận ra trước file ảnh xem trước mà Excel đính kèm.
  priority: 1_000,

  addProseMirrorPlugins() {
    return [
      new Plugin({
        props: {
          handlePaste: (view, event) => {
            const data = event.clipboardData
            if (!data) return false

            // HTML đã có bảng: để pipeline mặc định parse Slice và tableEditing
            // xử lý. Plugin ảnh cũng được dặn nhường ca này ở extension ảnh.
            if (containsHtmlTable(data.getData('text/html'))) return false

            const html = tabSeparatedTextToTableHtml(data.getData('text/plain'))
            if (!html) return false

            event.preventDefault()
            // Không truyền lại event gốc: nếu truyền, plugin này đọc lại TSV và
            // tự gọi chính nó mãi. Event rỗng chỉ mang vai trò ngữ cảnh paste.
            return view.pasteHTML(html, new Event('paste') as ClipboardEvent)
          },
        },
      }),
    ]
  },
})
