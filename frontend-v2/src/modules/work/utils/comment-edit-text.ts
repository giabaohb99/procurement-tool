import type { TaskCommentMention } from '../types/task-support'

/**
 * Chuyển nội dung bình luận (thẻ `@[12]`) sang CHỮ ĐỌC ĐƯỢC để sửa trong ô văn bản
 * thường, và ngược lại (E-05).
 *
 * Ô sửa là `<textarea>` chứ không phải ô nhắc tên `contenteditable`, nên người nhắc
 * hiện thành `@Tên` thuần. Lưu lại thì `@Tên` được đổi ngược thành thẻ — nhờ vậy sửa
 * chính tả không làm mất người đã được nhắc. Muốn nhắc thêm người mới thì viết bình
 * luận mới (ô sửa không có bảng gợi ý).
 */

const MENTION_TAG = /@\[(\d+)\]/g

/** `Chào @[12]` -> `Chào @Nguyễn Văn A`. Thẻ không tra ra tên thì giữ nguyên thẻ. */
export function bodyToEditableText(body: string, mentions: TaskCommentMention[]): string {
  const names = new Map(mentions.map((m) => [m.user_id, m.name]))
  return (body ?? '').replace(MENTION_TAG, (tag, id: string) => {
    const name = names.get(Number(id))
    return name ? `@${name}` : tag
  })
}

/** Ngược lại với {@link bodyToEditableText}. Tên dài khớp trước để "Lan" không nuốt "Lan Anh". */
export function editableTextToBody(text: string, mentions: TaskCommentMention[]): string {
  let out = text ?? ''
  const byLength = [...mentions].filter((m) => m.name).sort((a, b) => b.name.length - a.name.length)
  for (const m of byLength) {
    out = out.split(`@${m.name}`).join(`@[${m.user_id}]`)
  }
  return out.trim()
}
