/** Lớp áo của một chip `@Tên` bên trong vùng soạn thảo. */
export const MENTION_CHIP_CLASS =
  'rounded bg-primary/10 px-1.5 py-0.5 font-medium text-primary whitespace-nowrap'

export interface MentionPerson {
  user_id: number
  name: string
  code?: string
  avatar?: string
  /** Có liên quan sẵn tới chứng từ — hiện nhãn "trong phiếu". */
  related?: boolean
}

/** Dựng chip bằng DOM thuần vì nó nằm trong vùng `contenteditable`, không do React vẽ. */
export function createMentionChip(person: MentionPerson): HTMLSpanElement {
  const chip = document.createElement('span')
  chip.dataset.uid = String(person.user_id)
  // Khóa cứng: xóa là mất nguyên cụm, không còn cảnh "@Nguyễn Văn" cụt đuôi mà
  // hệ thống vẫn tưởng đang nhắc ai đó.
  chip.contentEditable = 'false'
  chip.textContent = `@${person.name}`
  chip.className = MENTION_CHIP_CLASS
  return chip
}

/**
 * Đọc ngược vùng soạn thảo ra chữ thuần kèm thẻ `@[<user_id>]` — đúng dạng
 * backend lưu và tự tách ra để gửi thông báo.
 */
export function serializeMentionBody(root: HTMLElement): string {
  let out = ''

  const walk = (node: Node) => {
    node.childNodes.forEach((child) => {
      if (child.nodeType === Node.TEXT_NODE) {
        out += child.textContent || ''
        return
      }
      if (!(child instanceof HTMLElement)) return

      if (child.dataset.uid) {
        out += `@[${child.dataset.uid}]`
      } else if (child.tagName === 'BR') {
        out += '\n'
      } else {
        // Trình duyệt bọc mỗi dòng mới thành <div>/<p> — quy về ký tự xuống dòng.
        if (out && !out.endsWith('\n')) out += '\n'
        walk(child)
      }
    })
  }

  walk(root)
  // Khoảng trắng cứng (U+00A0) do contenteditable tự chèn → về khoảng trắng thường.
  return out.replace(/ /g, ' ').trim()
}

/** Chữ viết tắt cho avatar: tên người Việt lấy chữ cái của TÊN (từ cuối). */
export function nameInitial(name: string): string {
  const parts = (name || '')
    .trim()
    .split(/\s+/)
    .filter((word) => /^\p{L}/u.test(word))
  if (!parts.length) return '?'
  return parts[parts.length - 1][0].toUpperCase()
}
