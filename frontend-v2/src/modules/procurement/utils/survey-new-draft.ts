// bao-CR-571 — nháp F5 của màn TẠO phiếu khảo sát, tách theo từng tài khoản.
//
// Trước bản này nháp nằm ở một khóa chung `survey_new_draft` cho MỌI tài khoản trên cùng
// trình duyệt, và đăng xuất không xóa nó. Người sau mở «Tạo phiếu» là nạp nguyên nháp của
// người trước — kể cả «NSPT phụ trách», ô bị khóa nên không ai sửa được (ca Quyên mở ra
// thấy tên chị Phương, 02/10/2026).

import type { AuthUser } from '@/core/auth/auth-types'

/** Khóa chung đời cũ — gặp là xóa, không bao giờ đọc lại. */
export const LEGACY_SURVEY_DRAFT_KEY = 'survey_new_draft'

/** Khóa nháp riêng của một tài khoản. */
export function getSurveyDraftKey(userId: number | undefined): string {
  return `${LEGACY_SURVEY_DRAFT_KEY}:${userId ?? 0}`
}

type DraftStorage = Pick<Storage, 'getItem' | 'removeItem'>

interface DraftOwnerFields {
  nspt: string
  created_by: number
}

/**
 * Đọc nháp của ĐÚNG tài khoản đang đăng nhập; không có hoặc hỏng thì `null`.
 *
 * Luôn ghi đè NSPT + người tạo bằng người đang đăng nhập — kể cả nháp của chính họ, vì
 * tên hiển thị có thể đã đổi từ lúc lưu nháp. Backend cũng tự gán lại lúc tạo phiếu.
 */
export function restoreSurveyDraft<T extends DraftOwnerFields>(
  storage: DraftStorage,
  user: Pick<AuthUser, 'id' | 'full_name'> | null | undefined,
): T | null {
  storage.removeItem(LEGACY_SURVEY_DRAFT_KEY)
  if (!user?.id) return null
  const raw = storage.getItem(getSurveyDraftKey(user.id))
  if (!raw) return null
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return null
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return null
  return { ...(parsed as T), nspt: user.full_name ?? '', created_by: user.id }
}
