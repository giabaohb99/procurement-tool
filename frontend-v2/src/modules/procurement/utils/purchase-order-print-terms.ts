import type { PurchaseOrderPrintTerms } from '../api/purchase-order-api'

/**
 * bao-CR-321 — điều khoản mục 2 và mục 5 "Thỏa thuận khác" của bản in Đơn đặt hàng.
 *
 * Backend đã gộp ba mức đơn -> NCC -> mặc định vào `print_terms`; bên này chỉ còn
 * lo hai chuyện: backend cũ chưa trả khóa đó, và từng ô rỗng/0 vẫn phải lùi về
 * mặc định để bản in không bao giờ in "trong vòng  ngày".
 */

/** Mặc định cũ của bản in — trước CR-321 ba giá trị này chốt cứng trong JSX. */
export const DEFAULT_PRINT_TERMS: PurchaseOrderPrintTerms = {
  inspection_days: 15,
  return_days: 7,
  inspection_days_label: '15',
  return_days_label: '07',
  invoice_deadline: 'Chậm nhất 24h kể từ khi nhận hàng',
}

export function resolvePrintTerms(data: {
  print_terms?: Partial<PurchaseOrderPrintTerms> | null
}): PurchaseOrderPrintTerms {
  const terms = data.print_terms
  if (!terms) return DEFAULT_PRINT_TERMS
  const inspection = positiveDays(terms.inspection_days) ?? DEFAULT_PRINT_TERMS.inspection_days
  const returnDays = positiveDays(terms.return_days) ?? DEFAULT_PRINT_TERMS.return_days
  return {
    inspection_days: inspection,
    return_days: returnDays,
    inspection_days_label: terms.inspection_days_label?.trim() || padDays(inspection),
    return_days_label: terms.return_days_label?.trim() || padDays(returnDays),
    invoice_deadline: terms.invoice_deadline?.trim() || DEFAULT_PRINT_TERMS.invoice_deadline,
  }
}

/** Số ngày hợp lệ là số nguyên dương; 0, âm, NaN đều nghĩa là "chưa khai". */
function positiveDays(value: number | undefined): number | undefined {
  const days = Math.trunc(Number(value))
  return Number.isFinite(days) && days > 0 ? days : undefined
}

/** "7" -> "07" như câu chữ bản in cũ. */
export function padDays(days: number): string {
  return String(days).padStart(2, '0')
}
