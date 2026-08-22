import { SCOPE_MODE } from '../types/document-scope'

/**
 * Khai TOÀN dòng loại trừ, không có lấy một dòng bao gồm — văn bản không tới ai.
 *
 * Luật phạm vi ở backend (`scope_service.applies_to`): chưa khai dòng nào thì
 * mặc định áp cho toàn bộ pháp nhân ban hành, nhưng **khai bất kỳ dòng nào là
 * mặc định đó TẮT**. Nên nếu tất cả dòng đều là loại trừ thì không ai có dòng
 * BAO GỒM nào trúng mình → ban hành xong văn bản không tới một người nào, kể cả
 * những người chẳng liên quan gì tới dòng loại trừ đó.
 *
 * Người dùng gần như luôn rơi vào đây theo cùng một lối: chỉ muốn "trừ anh B ra"
 * nên bấm đúng một dòng loại trừ, không nghĩ là phải khai thêm "bao gồm công ty
 * mình". Backend không chặn (dữ liệu vẫn hợp lệ), nên chỗ duy nhất nói được
 * điều này cho người dùng là giao diện.
 */
export function chiToanDongLoaiTru(modes: number[]): boolean {
  return modes.length > 0 && modes.every((mode) => mode === SCOPE_MODE.exclude)
}
