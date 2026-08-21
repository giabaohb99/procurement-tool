import type { ApprovalFlow } from '../types/approval'

/** Giá trị "không lọc" của hai ô select trên thanh công cụ. */
export const ALL = 'all'

export interface ApprovalFlowFilter {
  /** Mã loại chứng từ, hoặc `ALL`. */
  entity: string
  /** `ALL` · `'active'` · `'inactive'`. */
  dung: string
  /** Từ khóa gõ ở ô tìm kiếm. Chưa chuẩn hóa — hàm tự cắt khoảng trắng và hạ chữ. */
  keyword: string
}

/**
 * Lọc danh sách LUỒNG DUYỆT tại trình duyệt.
 *
 * Lọc ở client chứ không gửi lên API vì cả hệ chỉ có vài chục luồng — một lần
 * gọi là xong, gõ tới đâu lọc tới đó không phải chờ mạng.
 *
 * Tách khỏi component để **kiểm được**: ba điều kiện chồng nhau, mà sai một cái
 * thì màn hình vẫn hiện một bảng trông rất hợp lý — chỉ thiếu vài dòng, và
 * không có gì báo.
 */
export function filterApprovalFlows(
  items: ApprovalFlow[],
  { entity, dung, keyword }: ApprovalFlowFilter,
): ApprovalFlow[] {
  const needle = keyword.trim().toLowerCase()

  return items.filter((row) => {
    if (entity !== ALL && row.entity !== entity) return false
    if (dung !== ALL && row.is_active !== (dung === 'active')) return false
    if (!needle) return true

    //  Tìm cả trong MÃ và MÔ TẢ, không chỉ tên: người khai luồng nhớ mã
    //  ("PO-STD") thường xuyên hơn nhớ tên đầy đủ.
    return [row.name, row.code, row.description, row.company_name].some((field) =>
      (field ?? '').toLowerCase().includes(needle),
    )
  })
}
