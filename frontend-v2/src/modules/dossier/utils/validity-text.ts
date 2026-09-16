import type { CrudOption } from '@/shared/crud'

/**
 * Các mốc HẠN HIỆU LỰC MẶC ĐỊNH của một loại hồ sơ, đơn vị **tháng**.
 *
 * Là ô CHỌN chứ không phải ô gõ số (16/09/2026). Ô gõ số buộc phải kèm một câu
 * chú thích dài giải nghĩa `0` và nói trần 1200 — mà câu đó chỉ hiện khi người
 * dùng đã nhìn xuống dưới ô, tức là thường sau khi đã gõ xong. Ô chọn nói thẳng
 * bằng chính danh sách: *«Vô thời hạn»* là một dòng bấm được, nên không còn gì
 * để giải nghĩa, và trần thì không cách nào vượt.
 *
 * `0` = **vô thời hạn** — một lựa chọn thật (giấy chứng nhận đăng ký doanh
 * nghiệp, quyết định bổ nhiệm), không phải ô chưa ai nhập.
 */
export const VALIDITY_MONTHS = [0, 3, 6, 12, 24, 36, 60, 120] as const

/**
 * Diễn giải số tháng thành câu người đọc được.
 *
 * ⚠️ **Nguồn DUY NHẤT** cho cả ba chỗ bày hạn hiệu lực: ô chọn trên biểu mẫu,
 * cột *Hạn mặc định* của bảng, và huy hiệu trên thẻ khổ điện thoại. Tách ra đây
 * vì trước đó ô chọn nói *«3 năm»* còn bảng nói *«36 tháng»* cho cùng một dòng —
 * người dùng đọc ra hai giá trị khác nhau và đi tìm xem mình sửa hụt chỗ nào.
 *
 * Bội của 12 nói bằng NĂM: «36 tháng» bắt người đọc tự chia, mà cột bảng chỉ
 * rộng 150px nên họ chia trong lúc đang lướt.
 */
export function formatValidity(months: number): string {
  if (!Number.isFinite(months) || months <= 0) return 'Vô thời hạn'
  return months % 12 === 0 ? `${months / 12} năm` : `${months} tháng`
}

/** Danh sách mục cho ô chọn — nhãn lấy đúng `formatValidity` để không lệch. */
export const VALIDITY_OPTIONS: CrudOption[] = VALIDITY_MONTHS.map((months) => ({
  value: months,
  label: formatValidity(months),
}))
