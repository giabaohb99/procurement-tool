/** `0,5` / `1` — số ngày nghỉ bù theo dấu phẩy thập phân kiểu Việt. */
export function formatCompDays(days: number): string {
  return String(days).replace('.', ',')
}
