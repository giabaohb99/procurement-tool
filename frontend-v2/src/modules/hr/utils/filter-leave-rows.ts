import type { LeaveRequest } from '../types/leave'

/**
 * Lọc danh sách đơn nghỉ ở PHÍA MÀN HÌNH — phần thuần, không dính React.
 *
 * Dùng cho những màn đã nạp trọn danh sách trong một lượt gọi và không phân
 * trang: hai tab hộp việc duyệt và chế độ NGÀY của Lịch nghỉ. Hỏi lại backend
 * cho một bộ lọc ở đó là thừa một vòng mạng để lấy đúng thứ vừa có trong bộ nhớ.
 *
 * ⚠️ Màn nào CÓ phân trang (tab «Đơn của tôi») thì phải lọc ở BACKEND, không
 * dùng mấy hàm này: lọc trên trang hiện tại nghĩa là gõ một cái tên rồi chỉ tìm
 * trong hai mươi dòng đang mở, còn người đó nằm ở trang ba thì coi như không có.
 */

/** Giá trị của ô chọn khi không lọc gì. */
export const ALL_OPTION = 'all'

/**
 * Đơn có khớp từ khóa không — soi **tên người nghỉ, số đơn và lý do**.
 *
 * Ba trường đó là ba thứ người ta nhớ về một tờ đơn: nhớ ai xin, nhớ mã đọc
 * được trong thư báo, hoặc chỉ nhớ mang máng "cái đơn về quê".
 *
 * Không phân biệt hoa thường và bỏ khoảng trắng thừa hai đầu — không ai gõ đúng
 * hoa thường tên người khác.
 */
export function matchesKeyword(row: LeaveRequest, keyword: string): boolean {
  const needle = keyword.trim().toLowerCase()
  if (!needle) return true
  return (
    (row.employee_name ?? '').toLowerCase().includes(needle) ||
    row.code.toLowerCase().includes(needle) ||
    (row.reason ?? '').toLowerCase().includes(needle)
  )
}

/**
 * Các loại nghỉ CÓ MẶT trong danh sách, mỗi loại một lần.
 *
 * ⚠️ Chỉ lấy từ chính dữ liệu đang hiện, KHÔNG nạp cả danh mục: bày ra "Nghỉ
 * thai sản" trong khi hàng đợi không có tờ nào thuộc loại đó thì người dùng
 * chọn xong nhận về bảng rỗng — một lựa chọn chỉ dẫn tới ngõ cụt.
 */
export function leaveTypesIn(rows: LeaveRequest[]): { id: number; name: string }[] {
  const map = new Map<number, string>()
  for (const r of rows) {
    map.set(r.leave_type_id, r.leave_type_name || `#${r.leave_type_id}`)
  }
  //  Sắp theo tên để thứ tự ô chọn không đổi mỗi lần dữ liệu về khác thứ tự.
  return [...map]
    .map(([id, name]) => ({ id, name }))
    .sort((a, b) => a.name.localeCompare(b.name, 'vi'))
}

/** Lọc theo từ khóa + loại nghỉ. `typeId` là chuỗi vì nó đến từ ô chọn. */
export function filterLeaveRows<T extends LeaveRequest>(
  rows: T[],
  { keyword, typeId }: { keyword: string; typeId: string },
): T[] {
  return rows.filter((r) => {
    if (typeId !== ALL_OPTION && r.leave_type_id !== Number(typeId)) return false
    return matchesKeyword(r, keyword)
  })
}

/** Có đang lọc gì không — dùng để đổi câu khi bảng rỗng. */
export function isFiltering({ keyword, typeId }: { keyword: string; typeId: string }): boolean {
  return keyword.trim() !== '' || typeId !== ALL_OPTION
}
