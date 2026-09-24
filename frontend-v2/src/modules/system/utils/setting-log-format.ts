/**
 * Đọc câu nhật ký của màn *Cấu hình hệ thống* (bao-CR-461 ở bản cũ, bao-CR-462 ở bản này).
 *
 * Backend ghi `message` thành nhiều dòng: dòng đầu là câu tóm tắt, mỗi ô đã đổi
 * một dòng dạng «Nhãn: trước -> sau» (xem `backend/app/modules/setting/service.py`).
 * Hai hàm ở đây chỉ TÁCH lại câu đó ra để bày cho gọn — không tự dựng thêm chữ
 * nghĩa nào, vì câu gốc còn phải đọc được nguyên văn ở màn Nhật ký hệ thống.
 */

/** Dấu ngăn giữa giá trị cũ và giá trị mới, đúng như backend ghi. */
const ARROW = ' -> '
/** Dấu ngăn giữa nhãn ô và giá trị. */
const LABEL_SEP = ': '

export interface SettingLogMessage {
  /** Câu tóm tắt — dòng đầu tiên. */
  title: string
  /** Mỗi ô đã đổi một dòng. Rỗng với bản ghi cũ (chỉ có câu tóm tắt). */
  details: string[]
}

/**
 * Tách `message` thành câu tóm tắt + các dòng chi tiết.
 *
 * Bản ghi ghi TRƯỚC bao-CR-461 chỉ có đúng một dòng, nên `details` rỗng là
 * chuyện bình thường chứ không phải dữ liệu hỏng.
 */
export function splitSettingLogMessage(message?: string | null): SettingLogMessage {
  const lines = String(message ?? '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line !== '')
  const [title = '', ...details] = lines
  return { title, details }
}

export interface SettingChangeLine {
  label: string
  before: string
  after: string
}

/**
 * Tách một dòng chi tiết thành ba phần để bày thành cột.
 *
 * Trả `null` khi dòng không có dạng đó — dòng của khóa bí mật («… đã đặt giá trị
 * mới») là một ca như vậy, và nó phải hiện nguyên văn chứ không được nuốt mất.
 */
export function parseSettingChangeLine(line: string): SettingChangeLine | null {
  const arrowAt = line.indexOf(ARROW)
  if (arrowAt < 0) return null

  const head = line.slice(0, arrowAt)
  const after = line.slice(arrowAt + ARROW.length).trim()

  //  Nhãn lấy tới dấu hai chấm CUỐI CÙNG của vế trái. Nhãn thật có chứa dấu hai
  //  chấm — «Yêu cầu mua hàng: bắt buộc thu mua duyệt lần 2» — nên cắt ở dấu đầu
  //  tiên là nhãn cụt và nửa sau của nhãn nhảy sang chỗ dành cho giá trị cũ.
  const sepAt = head.lastIndexOf(LABEL_SEP)
  if (sepAt < 0) return null

  const label = head.slice(0, sepAt).trim()
  const before = head.slice(sepAt + LABEL_SEP.length).trim()
  if (!label || !before || !after) return null

  return { label, before, after }
}
