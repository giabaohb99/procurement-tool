import { DOMSerializer } from '@tiptap/pm/model'
import type { Editor } from '@tiptap/react'
import { toast } from 'sonner'

/**
 * Cắt / sao chép / dán cho MENU CHUỘT PHẢI.
 *
 * Không dùng `document.execCommand('copy')`: lệnh đó chỉ chạy đúng khi vùng
 * chọn còn nằm trong DOM và trình soạn thảo còn giữ con trỏ — mà mở menu ra là
 * con trỏ đã nhảy sang menu. Ở đây tự dựng nội dung từ vùng chọn của trình soạn
 * thảo rồi ghi thẳng vào khay nhớ tạm, nên bấm ở đâu cũng ra đúng phần đã bôi.
 *
 * Chép cả `text/html` lẫn `text/plain`: dán ngược vào trang này (hoặc vào Word)
 * thì giữ được định dạng, dán sang ô nhập chữ thuần thì vẫn có chữ.
 */

/** Vùng đang chọn, dựng lại thành HTML đúng như trình soạn thảo đang hiển thị. */
function selectionAsHtml(editor: Editor): string {
  const slice = editor.state.selection.content()
  const fragment = DOMSerializer.fromSchema(editor.schema).serializeFragment(slice.content)
  const holder = document.createElement('div')
  holder.append(fragment)
  return holder.innerHTML
}

function selectionAsText(editor: Editor): string {
  const { from, to } = editor.state.selection
  return editor.state.doc.textBetween(from, to, '\n', ' ')
}

export async function copySelection(editor: Editor) {
  const text = selectionAsText(editor)
  const html = selectionAsHtml(editor)
  if (!text && !html) return

  try {
    await navigator.clipboard.write([
      new ClipboardItem({
        'text/html': new Blob([html], { type: 'text/html' }),
        'text/plain': new Blob([text], { type: 'text/plain' }),
      }),
    ])
  } catch {
    // Trình duyệt cũ không có `ClipboardItem` thì đành chịu mất định dạng.
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      toast.error('Trình duyệt chặn sao chép — bấm Ctrl+C để chép')
    }
  }
}

export async function cutSelection(editor: Editor) {
  await copySelection(editor)
  editor.chain().focus().deleteSelection().run()
}

/**
 * Dán từ khay nhớ tạm.
 *
 * `plain`: bỏ hết định dạng, chỉ lấy chữ — dán nội dung từ web vào công văn mà
 * kéo theo phông, màu của trang gốc là hỏng cả thể thức văn bản.
 */
export async function pasteFromClipboard(editor: Editor, { plain = false } = {}) {
  try {
    if (!plain && navigator.clipboard.read) {
      for (const item of await navigator.clipboard.read()) {
        if (!item.types.includes('text/html')) continue
        const html = await (await item.getType('text/html')).text()
        editor.chain().focus().insertContent(html).run()
        return
      }
    }

    const text = await navigator.clipboard.readText()
    if (text) editor.chain().focus().insertContent(text).run()
  } catch {
    // Chrome hỏi quyền đọc khay nhớ tạm, người dùng từ chối là rơi vào đây.
    toast.error('Trình duyệt chặn dán từ menu — bấm Ctrl+V để dán')
  }
}
