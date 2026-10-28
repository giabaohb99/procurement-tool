import { normalizeCostCode } from './hr-cost-item-rules'

/** Mã dự phòng khi tên không cho ra ký tự nào dùng được (tên rỗng, toàn ký hiệu). */
const FALLBACK_CODE = 'KHOAN'
const MAX_CODE_LENGTH = 30

/**
 * MÃ TỰ SINH cho khoản MỚI, lấy từ tên: bỏ dấu tiếng Việt, IN HOA, khoảng trắng / ký hiệu thành `_`,
 * tối đa 30 ký tự (cột `String(30)`). Trùng mã đã có thì thêm đuôi `_2`, `_3`… — cắt bớt thân mã để đuôi
 * vẫn nằm trong 30 ký tự, không thì hai khoản tên dài giống nhau ở 30 ký tự đầu ra cùng một mã.
 *
 * Chỉ dùng cho khoản mới: mã của khoản đã có là tên cột số tiền ở bảng Định biên và trong tệp
 * CSV / Excel, tự đổi theo tên là cột nhập dở mất chủ.
 */
export function suggestCostCode(name: string, takenCodes: Iterable<string>): string {
  const taken = new Set(takenCodes)
  const base = normalizeCostCode(name) || FALLBACK_CODE
  if (!taken.has(base)) return base
  for (let n = 2; ; n += 1) {
    const suffix = `_${n}`
    const stem = base.slice(0, MAX_CODE_LENGTH - suffix.length).replace(/_+$/, '') || FALLBACK_CODE
    const candidate = `${stem}${suffix}`
    if (!taken.has(candidate)) return candidate
  }
}
