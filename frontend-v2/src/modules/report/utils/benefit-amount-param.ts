/** Trần số tiền mỗi suất quà — khớp `MAX_AMOUNT` của `benefit_report_inputs.py` (vượt là 422). */
export const BENEFIT_MAX_AMOUNT = 1_000_000_000

/**
 * Số tiền trên URL → số nguyên đồng trong [0, 1 tỷ]. URL do chính màn ghi nên chỉ nhận
 * chữ số trần (cho phép phần lẻ, cắt bỏ); link gõ tay `abc`, `-5`, `1e9` → 0 (ô trống),
 * vượt trần → kẹp về trần, không để ô nhập hiện một đằng mà backend ăn 422.
 */
export function parseAmountParam(raw: string | null | undefined): number {
  const s = (raw ?? '').trim()
  if (!/^\d+(\.\d+)?$/.test(s)) return 0
  return Math.min(Math.floor(Number(s)), BENEFIT_MAX_AMOUNT)
}

/** Số tiền → giá trị URL; 0 = «chưa nhập» → xóa khỏi URL (backend hiểu trống = 0). */
export function formatAmountParam(value: number): string {
  const n = Math.floor(Math.max(0, Math.min(value, BENEFIT_MAX_AMOUNT)))
  return n > 0 ? String(n) : ''
}
