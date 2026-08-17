import { SCOPE_DIM } from '../types/document-scope'

interface ScopeNames {
  company?: string
  department?: string
  employee?: string
}

/**
 * Một dòng phạm vi đọc thành câu ngắn: "Phòng Kế toán — Công ty A".
 *
 * Dùng cho các dòng CHƯA lưu ở form tạo văn bản: chúng chưa qua máy chủ nên
 * chưa có tên do backend trả về, mà bày ra một dãy số id thì người khai không
 * kiểm lại được mình vừa chọn đúng chưa.
 *
 * Chiều phòng ban luôn kèm pháp nhân, y như `DocumentScopeRow` — một phòng ban
 * có mặt ở nhiều pháp nhân nên đọc trơ trọi "Phòng Kế toán" là câu chưa đủ nghĩa.
 */
export function scopeLabel(dim: number, names: ScopeNames): string {
  if (dim === SCOPE_DIM.employee) return names.employee ?? ''
  if (dim === SCOPE_DIM.department) {
    return [names.department, names.company].filter(Boolean).join(' — ')
  }
  return names.company ?? ''
}
