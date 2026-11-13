/**
 * Câu trả lời của hộp đổi pháp nhân chính, gửi kèm PATCH hồ sơ — khớp `EmployeeUpdate.keep_old_company_concurrent`
 * của backend (duoc-CR-756). `true` = thêm MỘT dòng kiêm nhiệm loại Công ty ở công ty CŨ từ hôm nay (qua chốt L2 loại
 * Công ty); `false` = không giữ gì. Dòng loại Phòng ban ở công ty cũ luôn kết thúc, không chọn từng dòng như CR-755.
 */
export interface CompanyChangeConcurrentChoice {
  keep_old_company_concurrent: boolean
}

export function buildCompanyChangeChoice(keepOldCompany: boolean): CompanyChangeConcurrentChoice {
  return { keep_old_company_concurrent: keepOldCompany }
}
