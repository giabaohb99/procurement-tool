// Ba ô «Loại hình nghỉ» của mẫu đơn 2026 (ĐƠN XIN NGHỈ PHÉP / NGHỈ CHẾ ĐỘ, 06/10/2026):
//   [ ] Nghỉ phép năm (có lương) · [ ] Nghỉ việc riêng (không lương) · [ ] Nghỉ chế độ bảo hiểm.
//
// Đánh dấu theo TÊN loại nghỉ (đầu đơn + từng dòng) vì bản kê dòng không mang cờ `is_paid`.
// Một đơn khai nhiều loại (07/09/2026) thì được đánh nhiều ô cùng lúc.

export interface LeavePrintCategories {
  /** Nghỉ phép năm (có lương) — kể cả nghỉ có lương do công ty trả (cưới, tang, bù…). */
  paid: boolean
  /** Nghỉ việc riêng (không lương). */
  unpaid: boolean
  /** Nghỉ chế độ bảo hiểm — BHXH chi trả (ốm đau, thai sản, vợ sinh con…). */
  insurance: boolean
}

const INSURANCE_KEYWORDS = [
  'ốm',
  'thai sản',
  'sinh con',
  'khám thai',
  'sảy thai',
  'dưỡng sức',
  'bảo hiểm',
  'chế độ',
]

function isUnpaidName(name: string): boolean {
  return name.includes('không lương') || (name.includes('việc riêng') && !name.includes('có lương'))
}

function isInsuranceName(name: string): boolean {
  return INSURANCE_KEYWORDS.some((keyword) => name.includes(keyword))
}

/**
 * Tên loại nào không thuộc «không lương» hay «chế độ bảo hiểm» thì rơi vào ô «có lương»:
 * nghỉ cưới / tang / bù vẫn hưởng lương công ty, mẫu không có ô riêng cho chúng.
 * Đơn không có tên loại nào (dữ liệu cũ) mà có số ngày thì coi là phép năm — như bản in trước.
 */
export function classifyLeaveForPrint(
  names: readonly (string | null | undefined)[],
  totalDays: number,
): LeavePrintCategories {
  const normalized = names
    .map((name) => (name ?? '').trim().toLowerCase())
    .filter((name) => name !== '')

  if (normalized.length === 0) {
    return { paid: totalDays > 0, unpaid: false, insurance: false }
  }

  const result: LeavePrintCategories = { paid: false, unpaid: false, insurance: false }
  for (const name of normalized) {
    if (isUnpaidName(name)) result.unpaid = true
    else if (isInsuranceName(name)) result.insurance = true
    else result.paid = true
  }
  return result
}
