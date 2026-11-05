/**
 * Số ngày của hộp Đối chiếu kết sổ phép: tối đa 2 số lẻ, bỏ đuôi `0` — `8` chứ không `8.00`.
 * Bảng (khổ rộng) và thẻ (khổ điện thoại) dùng chung một hàm để hai lối bày ra cùng một con số.
 */
export function formatCloseYearDays(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/0$/, '')
}
