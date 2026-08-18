import type { DocumentType } from '../types/document-type'

/**
 * Loại văn bản này có nên nhắc "đã có bản cùng loại đang hiệu lực" không (B05).
 *
 * Nhiều văn bản cùng một loại là chuyện **bình thường**: một phòng ban ra hàng
 * chục công văn, thông báo, biên bản mỗi tháng. Nhắc ở những loại đó thì lần
 * tạo nào cũng thấy băng vàng, và người dùng học được đúng một điều — bỏ qua
 * nó. Lúc băng vàng thật sự quan trọng thì cũng bị bỏ qua nốt.
 *
 * Chỉ nhắc ở loại **văn bản quản trị**: quy chế, quy định, quy trình, chính
 * sách. Ở đó, bản thứ hai còn hiệu lực cho cùng một phòng gần như luôn là lỗi —
 * người soạn quên bãi bỏ hoặc thay thế bản cũ, và tổ chức có hai bộ luật cùng
 * chạy mà không ai biết cái nào thắng.
 *
 * Nhận diện bằng cờ `needs_decision` (phải ban hành kèm một Quyết định) chứ
 * không chép cứng danh sách mã loại: đúng nhóm văn bản quản trị theo định nghĩa
 * của chính danh mục, và người quản trị thêm loại mới cũng không phải sửa mã.
 */
export function shouldWarnDuplicate(type: DocumentType | undefined): boolean {
  return Boolean(type?.needs_decision)
}
