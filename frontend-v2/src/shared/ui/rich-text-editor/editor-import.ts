import type { Editor } from '@tiptap/core'

export type DocumentImportMode = 'insert' | 'replace'

/** Editor có nội dung thật; đoạn rỗng mặc định của ProseMirror không được tính. */
export function hasEditorContent(editor: Editor) {
  return !editor.isEmpty
}

/** Áp nội dung đã chuyển đổi theo lựa chọn của người dùng. */
export function applyImportedContent(editor: Editor, html: string, mode: DocumentImportMode) {
  if (mode === 'replace') {
    return editor.chain().focus().setContent(html).run()
  }
  return editor.chain().focus().insertContent(html).run()
}
