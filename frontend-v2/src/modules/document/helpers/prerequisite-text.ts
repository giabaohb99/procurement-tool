import type { DocPrerequisite } from '../types/document-link-rule'

/**
 * Câu mô tả TÌNH TRẠNG của một quan hệ tiên quyết còn thiếu.
 *
 * Chỉ nói phần "thiếu bao nhiêu" — tên loại văn bản và tên quan hệ do màn hình
 * bày riêng, vì đó mới là thứ người đọc quét mắt tìm. Nhồi cả bốn thông tin vào
 * một dòng chữ thì dòng nào cũng dài bằng nhau và không có điểm bám.
 *
 * Hai câu cho hai tình huống khác nhau — gộp làm một là nói sai một trong hai:
 *
 * - **Chưa có gì cả**: người soạn phải đi làm văn bản đó trước, hoặc nhờ người
 *   khác làm.
 * - **Có nhưng chưa đủ số lượng**: quy tắc đòi 2 mà kho mới có 1 — trường hợp
 *   hiếm, nhưng nếu cũng nói "chưa có" thì người dùng mở danh sách ra thấy có,
 *   và từ đó không tin cảnh báo nữa.
 */
export function prerequisiteText(item: DocPrerequisite): string {
  if (item.available === 0) return 'Chưa có văn bản nào còn hiệu lực'
  return `Cần ${item.need} văn bản, hiện mới có ${item.available} còn hiệu lực`
}
