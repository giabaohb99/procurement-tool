import { Editor } from '@tiptap/core'
import { TableKit } from '@tiptap/extension-table'
import StarterKit from '@tiptap/starter-kit'
import { afterEach, describe, expect, it } from 'vitest'

import { ImageWithSize } from './image-size-extension'
import { clipboardHasSpreadsheetTable, tabSeparatedTextToTableHtml } from './spreadsheet-clipboard'
import { SpreadsheetPaste } from './spreadsheet-paste-extension'

const editors: Editor[] = []

afterEach(() => {
  for (const editor of editors.splice(0)) editor.destroy()
})

function buildEditor(content: string) {
  const editor = new Editor({
    extensions: [
      StarterKit,
      SpreadsheetPaste,
      ImageWithSize.configure({ inline: false, allowBase64: true }),
      TableKit.configure({ table: { resizable: false } }),
    ],
    content,
  })
  editors.push(editor)
  return editor
}

function selectAllCells(editor: Editor) {
  const positions: number[] = []
  editor.state.doc.descendants((node, position) => {
    if (node.type.spec.tableRole === 'cell' || node.type.spec.tableRole === 'header_cell') {
      positions.push(position)
    }
  })
  expect(positions.length).toBeGreaterThan(1)
  editor.commands.setCellSelection({
    anchorCell: positions[0],
    headCell: positions[positions.length - 1],
  })
}

function dan(
  editor: Editor,
  { html = '', text = '', files = [] }: { html?: string; text?: string; files?: File[] },
) {
  const event = new Event('paste', { bubbles: true, cancelable: true })
  Object.defineProperty(event, 'clipboardData', {
    value: {
      files,
      types: [html && 'text/html', text && 'text/plain', files.length && 'Files'].filter(Boolean),
      getData: (type: string) => (type === 'text/html' ? html : type === 'text/plain' ? text : ''),
    },
  })
  editor.view.dom.dispatchEvent(event)
}

const TRANSLATION_MAP =
  '<table><tbody>' +
  '<tr><td><p>cũ 1</p></td><td><p>cũ 2</p></td></tr>' +
  '<tr><td><p>cũ 3</p></td><td><p>cũ 4</p></td></tr>' +
  '</tbody></table>'

describe('dán bảng từ Excel vào bảng đang bôi đen', () => {
  it('ưu tiên bảng HTML thay vì ảnh xem trước mà Excel đính kèm', () => {
    const editor = buildEditor(TRANSLATION_MAP)
    selectAllCells(editor)

    dan(editor, {
      html:
        '<html><body><table><tbody>' +
        '<tr><td>Excel A1</td><td>Excel B1</td></tr>' +
        '<tr><td>Excel A2</td><td>Excel B2</td></tr>' +
        '</tbody></table></body></html>',
      text: 'Excel A1\tExcel B1\nExcel A2\tExcel B2',
      //  Đây chính là thứ làm bản cũ dán thành hình: Excel đặt thêm một PNG
      //  cùng vùng ô trong `clipboardData.files`.
      files: [new File(['preview'], 'excel-preview.png', { type: 'image/png' })],
    })

    const html = editor.getHTML()
    expect(html).toContain('Excel A1')
    expect(html).toContain('Excel B2')
    expect(html).not.toContain('cũ 1')
    expect(html).not.toContain('<figure')
    expect(html.match(/<td/g)).toHaveLength(4)
  })

  it('clipboard chỉ còn TSV thì vẫn rải đúng từng ô, không dồn vào một ô', () => {
    const editor = buildEditor(TRANSLATION_MAP)
    selectAllCells(editor)

    dan(editor, {
      text: 'A & B\t<Hai>\nBa\tBốn',
      files: [new File(['preview'], 'excel-preview.png', { type: 'image/png' })],
    })

    const html = editor.getHTML()
    expect(html).toContain('A &amp; B')
    expect(html).toContain('&lt;Hai&gt;')
    expect(html).toContain('Ba')
    expect(html).toContain('Bốn')
    expect(html).not.toContain('cũ 1')
    expect(html).not.toContain('<figure')
  })
})

describe('nhận diện clipboard bảng', () => {
  it('ảnh thông thường không bị nhận nhầm thành bảng', () => {
    const data = {
      getData: (type: string) =>
        type === 'text/html' ? '<img src="https://example.test/image.png">' : '',
    }

    expect(clipboardHasSpreadsheetTable(data)).toBe(false)
  })

  it('TSV được đổi thành HTML an toàn, không cho chữ trong ô chui thành thẻ', () => {
    expect(tabSeparatedTextToTableHtml('<b>1</b>\tA & B')).toBe(
      '<table><tbody><tr><td><p>&lt;b&gt;1&lt;/b&gt;</p></td><td><p>A &amp; B</p></td></tr></tbody></table>',
    )
  })
})
