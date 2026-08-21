import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { afterEach, describe, expect, it } from 'vitest'

import { applyImportedContent, hasEditorContent } from './editor-import'

let editor: Editor | null = null

afterEach(() => {
  editor?.destroy()
  editor = null
})

function makeEditor(content: string) {
  editor = new Editor({ extensions: [StarterKit], content })
  return editor
}

describe('nhập nội dung vào trình soạn thảo', () => {
  it('chèn nội dung tại đúng vị trí con trỏ và giữ phần đã soạn', () => {
    const instance = makeEditor('<p>Trước sau</p>')
    instance.commands.setTextSelection(6)

    expect(applyImportedContent(instance, '<p>Nội dung nhập</p>', 'insert')).toBe(true)

    const text = instance.getText()
    expect(text).toContain('Trước')
    expect(text).toContain('Nội dung nhập')
    expect(text).toContain(' sau')
    expect(text.indexOf('Trước')).toBeLessThan(text.indexOf('Nội dung nhập'))
    expect(text.indexOf('Nội dung nhập')).toBeLessThan(text.indexOf(' sau'))
  })

  it('ghi đè toàn bộ nội dung cũ khi chọn thay thế', () => {
    const instance = makeEditor('<h2>Tiêu đề cũ</h2><p>Nội dung cũ</p>')

    expect(applyImportedContent(instance, '<h1>Tệp mới</h1><p>Dữ liệu mới</p>', 'replace')).toBe(
      true,
    )

    expect(instance.getHTML()).toContain('Tệp mới')
    expect(instance.getHTML()).toContain('Dữ liệu mới')
    expect(instance.getHTML()).not.toContain('Tiêu đề cũ')
    expect(instance.getHTML()).not.toContain('Nội dung cũ')
  })

  it('không tính đoạn rỗng mặc định là nội dung đã soạn', () => {
    expect(hasEditorContent(makeEditor('<p></p>'))).toBe(false)
    expect(hasEditorContent(makeEditor('<p>Đã có chữ</p>'))).toBe(true)
  })
})
