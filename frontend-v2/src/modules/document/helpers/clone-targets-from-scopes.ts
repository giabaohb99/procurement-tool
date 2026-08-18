import { SCOPE_DIM, SCOPE_MODE, type DocumentScopeInput } from '../types/document-scope'

/**
 * Pháp nhân nào sẽ nhận BẢN RIÊNG — suy thẳng từ các dòng PHẠM VI ÁP DỤNG.
 *
 * Trước đây màn tạo văn bản hỏi hai lần cùng một câu: chọn pháp nhân ở khối
 * phạm vi, rồi tick lại pháp nhân ở khối clone. Hai danh sách chắc chắn lệch
 * nhau theo thời gian, mà **không có gì trên màn hình nói cái nào đúng** — văn
 * bản áp cho mười pháp nhân nhưng chỉ tách bản riêng cho tám, hai nơi còn lại
 * im lặng dùng chung bản gốc.
 *
 * Ba luật lọc, mỗi luật một lý do:
 * - chỉ dòng **bao gồm**: dòng loại trừ nói nơi đó KHÔNG áp dụng, clone về đó
 *   là tạo văn bản cho nơi vừa bị loại ra;
 * - chỉ chiều **pháp nhân**: clone tách theo pháp nhân, dòng phòng ban hay nhân
 *   sự không nói được nên tách cho ai;
 * - bỏ **pháp nhân ban hành**: bản gốc đã nằm ở đó rồi.
 *
 * `include_children` cố ý KHÔNG bung ra thành các công ty con: danh sách con
 * còn đổi (mở thêm công ty sau này), mà clone thì đẻ ra văn bản thật mang số
 * hiệu vĩnh viễn — không thể sinh theo một danh sách đang trôi.
 */
export function cloneTargetsFromScopes(
  rows: DocumentScopeInput[],
  issuerCompanyId: number,
): number[] {
  const ids: number[] = []

  for (const row of rows) {
    if (row.mode !== SCOPE_MODE.include) continue
    if (row.dim !== SCOPE_DIM.company) continue

    const companyId = row.company_id
    if (!companyId || companyId === issuerCompanyId) continue
    if (ids.includes(companyId)) continue

    ids.push(companyId)
  }

  return ids
}
