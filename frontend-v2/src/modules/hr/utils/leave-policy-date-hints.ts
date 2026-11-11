/**
 * Câu giải thích hai ô ngày của Phân bổ chính sách nghỉ phép (nút `?` cạnh nhãn), dùng chung cho hộp
 * phân bổ một người và trang Phân bổ hàng loạt. Phải khớp luật ở
 * `backend/app/modules/leave/policy_allocation_math.py`: tháng nào phân bổ còn hiệu lực vào NGÀY 15 thì
 * tháng đó theo gói; phân bổ bắt đầu trong / trước tháng vào làm thì phủ cả năm vào làm.
 */
export const LEAVE_POLICY_FROM_DATE_HINT =
  'Ngày chính sách bắt đầu áp cho người này. Quỹ phép vẫn tính theo năm dương lịch và chia theo tháng: ' +
  'tháng nào chính sách còn hiệu lực vào ngày 15 thì tháng đó theo số ngày của chính sách (bắt đầu từ ngày 16 ' +
  'trở đi thì tính từ tháng sau). Bắt đầu từ ngày vào làm thì năm vào làm tính trọn theo chính sách. ' +
  'Nút Từ ngày vào làm điền sẵn ngày vào làm trong hồ sơ.'

export const LEAVE_POLICY_TO_DATE_HINT =
  'Ngày chính sách thôi áp. Để trống là không thời hạn: áp cho tới khi có phân bổ khác thay. ' +
  'Các tháng sau ngày này quay về hạn mức theo luật của từng loại nghỉ. ' +
  'Một người không được có hai phân bổ chồng ngày nhau.'
