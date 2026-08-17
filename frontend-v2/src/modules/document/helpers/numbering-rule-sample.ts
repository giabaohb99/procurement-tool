/**
 * Dựng MỘT số hiệu minh họa từ mẫu, để người khai thấy ngay mẫu mình gõ ra hình
 * thù gì. Đây là chuỗi giả — số thật do backend cấp trong cùng giao dịch ghi
 * văn bản (khóa dòng bộ đếm), client không có đường nào tự đánh số.
 */

/** Giá trị mẫu cho từng token. Ngày/tháng cố định để xem trước không nhảy theo hôm nay. */
const SAMPLE_VALUES: Record<string, string> = {
  Ngay: '15',
  Thang: '08',
  LoaiVB: 'TB',
  PhongBan: 'HCNS',
  PhapNhan: 'DEGO',
  SoVB: 'CV',
}

export function numberingRuleSample(pattern: string, startNo: number, year: number): string {
  const values: Record<string, string> = {
    ...SAMPLE_VALUES,
    STT: String(startNo).padStart(2, '0'),
    Nam: String(year),
  }
  return Object.entries(values).reduce(
    (result, [token, value]) => result.replaceAll(`{${token}}`, value),
    pattern,
  )
}
