/**
 * Backend FastAPI bọc MỌI response trong một "phong bì" thống nhất:
 *   thành công: { success: true,  message, data }
 *   thất bại:   { success: false, error: { code, message, details } }
 * Kể cả HTTPException và lỗi validate cũng được global handler ép về dạng này.
 */

export interface SuccessEnvelope<T> {
  success: true
  message?: string
  data: T
}

export interface ErrorEnvelope {
  success: false
  error: { code?: string; message: string; details?: unknown }
}

export type ApiEnvelope<T> = SuccessEnvelope<T> | ErrorEnvelope

/** Thông điệp lỗi ưu tiên: error.message > message > message của axios > câu mặc định. */
export function extractErrorMessage(error: unknown): string {
  const fallback = 'Có lỗi xảy ra, vui lòng thử lại'
  if (!error || typeof error !== 'object') return fallback

  const err = error as {
    response?: { data?: Partial<ErrorEnvelope> & { message?: string } }
    message?: string
  }
  return (
    err.response?.data?.error?.message ||
    err.response?.data?.message ||
    err.message ||
    fallback
  )
}
