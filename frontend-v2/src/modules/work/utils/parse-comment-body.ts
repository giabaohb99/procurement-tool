import type { TaskCommentMention } from '../types/task-support'

/**
 * Một mẩu của nội dung bình luận sau khi tách thẻ nhắc tên.
 *
 * Backend lưu người được nhắc bằng THẺ `@[12]` chứ không lưu chữ "@Nguyễn Văn A":
 * tên tiếng Việt trùng rất nhiều và người ta đổi tên được, nên lưu tên là bình
 * luận cũ vĩnh viễn nhắc sai người. Đổi lại, tầng hiển thị phải tự tra tên theo
 * ID mỗi lần vẽ — việc của hàm này.
 */
export type CommentSegment =
  | { kind: 'text'; text: string }
  | { kind: 'mention'; userId: number; name: string }

const MENTION_TAG = /@\[(\d+)\]/g

/**
 * Tách nội dung thành các mẩu chữ và mẩu NHẮC TÊN, giữ nguyên thứ tự.
 *
 * Hàm thuần, tách khỏi component để test được: đây là chỗ dễ sai âm thầm nhất
 * của khối bình luận — sai một nhịp con trỏ là nuốt mất chữ quanh thẻ mà nhìn
 * lướt vẫn thấy "có nội dung".
 */
export function parseCommentBody(
  body: string,
  mentions: TaskCommentMention[],
): CommentSegment[] {
  const text = body ?? ''
  if (!text.includes('@[')) return text ? [{ kind: 'text', text }] : []

  const names = new Map(mentions.map((m) => [m.user_id, m.name]))
  const out: CommentSegment[] = []
  let cursor = 0

  //  `matchAll` chứ không `exec` trong vòng `while`: `exec` dùng `lastIndex` của
  //  chính biểu thức, mà biểu thức khai ở tầng module nên hai lần gọi liên tiếp
  //  ăn chung con trỏ — bình luận thứ hai mất thẻ đầu tiên.
  for (const m of text.matchAll(MENTION_TAG)) {
    const at = m.index ?? 0
    if (at > cursor) out.push({ kind: 'text', text: text.slice(cursor, at) })
    out.push({
      kind: 'mention',
      userId: Number(m[1]),
      //  Người bị xóa tài khoản thì không tra ra tên. Vẫn phải vẽ ra chip chứ
      //  đừng bỏ thẻ đi: bỏ đi là câu "@ xem hộ mình" mất chủ ngữ.
      name: names.get(Number(m[1])) || 'không rõ',
    })
    cursor = at + m[0].length
  }

  if (cursor < text.length) out.push({ kind: 'text', text: text.slice(cursor) })
  return out
}
