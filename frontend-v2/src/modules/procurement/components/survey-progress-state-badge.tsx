/**
 * Tiến độ MỘT DÒNG yêu cầu báo giá — bảng màu và huy hiệu.
 *
 * ⚠️ **Khóa ở đây là CHỮ TIẾNG VIỆT, không phải mã.** `survey_progress` của
 * backend dựng chuỗi này từ `STATE_*` trong `survey_request/line_state.py` —
 * nhóm hằng số được CLAUDE.md nêu đích danh là ngoại lệ còn lại của R2/QĐ-11
 * (giá trị suy ra, không bao giờ lưu xuống cột). Đừng "sửa cho đúng chuẩn" bằng
 * cách đổi sang mã số ở riêng tầng này: chuỗi phải khớp từng ký tự với backend,
 * lệch một dấu là huy hiệu rơi về màu xám mặc định mà không có gì báo lỗi.
 *
 * Tách khỏi `survey-progress-page` để bảng (khổ rộng) và thẻ (khổ hẹp) dùng
 * CHUNG một bản — để trong trang thì thẻ phải import ngược lại trang, thành
 * vòng import.
 */
export const SURVEY_PROGRESS_COLORS: Record<string, string> = {
  'Chưa tiếp nhận': '#94a3b8',
  'Đã tiếp nhận': '#64748b',
  'Đang khảo sát': '#d97706',
  'Đã trả kết quả': '#00AEEF',
  'Chốt rỗng': '#a855f7',
  'Đã chọn phương án': '#0d9488',
  'Cần khảo sát lại': '#dc2626',
  'Đã tạo YCMH': '#7c3aed',
  'Hoàn thành': '#16a34a',
}

/**
 * ⚠️ Màu đặt bằng `style` chứ không bằng lớp Tailwind là CỐ Ý: chín màu này là
 * dữ liệu tra theo khóa lúc chạy, mà Tailwind quét mã nguồn ở bước dựng nên lớp
 * ghép chuỗi (`bg-[${color}]`) không bao giờ được sinh ra. Đây đúng ca "giá trị
 * động" mà `styling.md` chừa cho `style`.
 */
export function SurveyProgressStateBadge({ state }: { state: string }) {
  if (!state) return null
  const color = SURVEY_PROGRESS_COLORS[state] || '#64748b'
  return (
    <span
      className="inline-block whitespace-nowrap rounded px-2 py-0.5 text-xs font-medium"
      style={{ backgroundColor: `${color}22`, color }}
    >
      {state}
    </span>
  )
}
