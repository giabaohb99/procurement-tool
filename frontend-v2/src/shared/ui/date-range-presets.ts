import { toDateInputValue } from '@/shared/utils/format-date'

export interface DateRangePreset {
  label: string
  /**
   * Trả `[từ, đến]` dạng `yyyy-mm-dd`.
   *
   * Là HÀM chứ không phải hai chuỗi cố định: trang danh sách hay mở từ tối hôm
   * trước sang sáng hôm sau, mà "Hôm nay" tính lúc nạp mô-đun thì sáng ra vẫn
   * còn trỏ vào ngày hôm qua.
   *
   * `today` truyền vào được để test khỏi phụ thuộc ngày chạy máy.
   */
  resolve: (today?: Date) => [string, string]
}

function at(year: number, month: number, day: number): string {
  return toDateInputValue(new Date(year, month, day))
}

/** Cộng/trừ ngày, giữ nguyên giờ địa phương (không đụng UTC). */
function shiftDays(from: Date, days: number): Date {
  const next = new Date(from)
  next.setDate(next.getDate() + days)
  return next
}

/**
 * Mấy khoảng bấm một cái là xong của ô chọn khoảng ngày.
 *
 * Cố ý KHÔNG có "Tất cả": xóa khoảng ngày đã có nút ✕ trên chính ô chọn, thêm
 * một mục nữa cùng nghĩa là hai đường dẫn tới một việc.
 */
export const DATE_RANGE_PRESETS: DateRangePreset[] = [
  {
    label: 'Hôm nay',
    resolve: (today = new Date()) => [toDateInputValue(today), toDateInputValue(today)],
  },
  {
    label: '7 ngày qua',
    resolve: (today = new Date()) => [
      toDateInputValue(shiftDays(today, -6)),
      toDateInputValue(today),
    ],
  },
  {
    label: '30 ngày qua',
    resolve: (today = new Date()) => [
      toDateInputValue(shiftDays(today, -29)),
      toDateInputValue(today),
    ],
  },
  {
    label: 'Tháng này',
    //  `new Date(y, m + 1, 0)` = ngày 0 của tháng sau = ngày cuối tháng này.
    //  Trình duyệt tự lo tháng 28/29/30/31 ngày, không phải tra bảng.
    resolve: (today = new Date()) => [
      at(today.getFullYear(), today.getMonth(), 1),
      at(today.getFullYear(), today.getMonth() + 1, 0),
    ],
  },
  {
    label: 'Quý này',
    resolve: (today = new Date()) => {
      const firstMonth = Math.floor(today.getMonth() / 3) * 3
      return [
        at(today.getFullYear(), firstMonth, 1),
        at(today.getFullYear(), firstMonth + 3, 0),
      ]
    },
  },
  {
    label: 'Năm nay',
    resolve: (today = new Date()) => [
      at(today.getFullYear(), 0, 1),
      at(today.getFullYear(), 11, 31),
    ],
  },
]
