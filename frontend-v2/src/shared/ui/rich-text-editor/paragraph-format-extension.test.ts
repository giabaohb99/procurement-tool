import { Editor } from '@tiptap/core'
import { TextAlign } from '@tiptap/extension-text-align'
import { TextStyleKit } from '@tiptap/extension-text-style'
import { TableKit } from '@tiptap/extension-table'
import StarterKit from '@tiptap/starter-kit'
import { describe, expect, it } from 'vitest'

import { ParagraphFormat } from './paragraph-format-extension'

function dungEditor(content: string) {
  return new Editor({
    extensions: [
      StarterKit,
      TextStyleKit,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      ParagraphFormat,
    ],
    content,
  })
}

/**
 * Giãn dòng của từng đoạn CÓ CHỮ — thứ người dùng nhìn thấy.
 *
 * Bỏ đoạn rỗng: Tiptap tự chèn một đoạn trắng sau bảng để con trỏ còn chỗ đứng,
 * đếm cả nó vào thì bài kiểm đọc như có thừa một đoạn.
 */
function gianDong(editor: Editor): string[] {
  const root = document.createElement('div')
  root.innerHTML = editor.getHTML()
  return Array.from(root.querySelectorAll('p, h1, h2, h3'))
    .filter((el) => (el.textContent || '').trim() !== '')
    .map((el) => (el as HTMLElement).style.lineHeight || '')
}

describe('setLineHeight', () => {
  it('đổi được giãn dòng của đoạn đang đứng', () => {
    const editor = dungEditor('<p>Một đoạn.</p>')

    editor.commands.selectAll()
    editor.commands.setLineHeight('2')

    expect(gianDong(editor)).toEqual(['2'])
  })

  it('bôi đen NHIỀU đoạn thì đổi hết, không chỉ đoạn đầu', () => {
    const editor = dungEditor('<p>Đoạn một.</p><p>Đoạn hai.</p><p>Đoạn ba.</p>')

    editor.commands.selectAll()
    editor.commands.setLineHeight('2')

    expect(gianDong(editor)).toEqual(['2', '2', '2'])
  })

  it('ĐÈ ĐƯỢC giãn dòng có sẵn của tệp Word vừa nhập', () => {
    //  LỖI NGƯỜI DÙNG BÁO (20/08/2026): nhập một tệp .doc lên rồi bôi đen đổi
    //  giãn dòng thì không ăn. Bộ chuyển của backend ghi `line-height` thẳng vào
    //  `style` của từng `<p>` (xem `docx_html.py`), nên đây là ca phải chạy đúng.
    const editor = dungEditor(
      '<p style="line-height: 1.725; margin-bottom: 8px">Đoạn từ Word.</p>' +
        '<p style="line-height: 1.725">Đoạn nữa từ Word.</p>',
    )

    editor.commands.selectAll()
    editor.commands.setLineHeight('1')

    expect(gianDong(editor)).toEqual(['1', '1'])
  })

  it('đổi giãn dòng KHÔNG làm mất các định dạng khác của đoạn', () => {
    const editor = dungEditor(
      '<p style="line-height: 1.725; margin-bottom: 8px; text-indent: 12px">Đoạn.</p>',
    )

    editor.commands.selectAll()
    editor.commands.setLineHeight('2')

    const root = document.createElement('div')
    root.innerHTML = editor.getHTML()
    const p = root.querySelector('p')
    expect(p?.style.lineHeight).toBe('2')
    expect(p?.style.marginBottom).toBe('8px')
    expect(p?.style.textIndent).toBe('12px')
  })

  it('trả về mặc định của trang khi truyền null', () => {
    const editor = dungEditor('<p style="line-height: 2">Đoạn.</p>')

    editor.commands.selectAll()
    editor.commands.setLineHeight(null)

    expect(gianDong(editor)).toEqual([''])
  })

  it('bôi đen lẫn TIÊU ĐỀ và đoạn văn thì cả hai cùng đổi', () => {
    const editor = dungEditor('<h2>Tiêu đề</h2><p>Đoạn.</p>')

    editor.commands.selectAll()
    editor.commands.setLineHeight('2')

    expect(gianDong(editor)).toEqual(['2', '2'])
  })
})

// ── Bộ extension THẬT của editor: bảng + căn lề + chỉ số trên dưới ───────────
//  Bộ tối giản ở trên có thể giấu lỗi do các extension khác gây ra, nên phần này
//  dựng lại đúng những thứ mà nội dung nhập từ Word hay chạm tới.
describe('setLineHeight với bảng — mẫu hành chính nào cũng có bảng', () => {
  function dungEditorCoBang(content: string) {
    return new Editor({
      extensions: [
        StarterKit,
        TextStyleKit,
        TextAlign.configure({ types: ['heading', 'paragraph'] }),
        ParagraphFormat,
        TableKit.configure({ table: { resizable: false } }),
      ],
      content,
    })
  }

  it('đổi được giãn dòng của đoạn nằm TRONG ô bảng', () => {
    //  Khối đầu văn bản (quốc hiệu / số hiệu) của mọi mẫu hành chính là một
    //  bảng hai cột, nên đây là ca thường gặp nhất sau khi nhập tệp Word.
    const editor = dungEditorCoBang(
      '<table><tbody><tr>' +
        '<td><p style="line-height: 1.725">CÔNG TY TNHH DEGO</p></td>' +
        '<td><p style="line-height: 1.725">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</p></td>' +
        '</tr></tbody></table>',
    )

    editor.commands.selectAll()
    editor.commands.setLineHeight('1')

    expect(gianDong(editor)).toEqual(['1', '1'])
  })

  it('bôi đen VẮT QUA cả bảng lẫn đoạn văn thường thì đổi hết', () => {
    const editor = dungEditorCoBang(
      '<table><tbody><tr><td><p>Trong ô.</p></td></tr></tbody></table><p>Ngoài bảng.</p>',
    )

    editor.commands.selectAll()
    editor.commands.setLineHeight('2')

    expect(gianDong(editor)).toEqual(['2', '2'])
  })
})
