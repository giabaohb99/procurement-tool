import type { ForumAudience } from '../types/forum-post'

const STORAGE_KEY = 'forum.last-audience'

/** Mặc định khi chưa từng đăng: Toàn tập đoàn — lựa an toàn nhất về hiển thị. */
const DEFAULT_AUDIENCE: ForumAudience = 3

/**
 * Đọc đối tượng xem của lần đăng TRƯỚC (doc `erp/dien-dan/02` mục F3 — hộp
 * đăng bài nhớ lựa chọn). Giá trị rác trong localStorage thì về mặc định.
 */
export function readLastAudience(storage: Pick<Storage, 'getItem'> = localStorage): ForumAudience {
  const raw = storage.getItem(STORAGE_KEY)
  const value = Number(raw)
  return value === 1 || value === 2 || value === 3 ? value : DEFAULT_AUDIENCE
}

export function saveLastAudience(
  audience: ForumAudience,
  storage: Pick<Storage, 'setItem'> = localStorage,
): void {
  storage.setItem(STORAGE_KEY, String(audience))
}
