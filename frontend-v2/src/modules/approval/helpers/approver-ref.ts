/**
 * Ô `approver_ref` lưu dạng CHUỖI vì backend dùng chung một cột cho cả sáu cách
 * chọn người duyệt: khi là "người cụ thể" thì đó là danh sách mã nhân sự ngăn
 * bằng dấu phẩy, khi là "theo vai trò" thì là mã vai trò, khi là "lên N cấp"
 * thì là một con số.
 *
 * Hai hàm dưới đây chỉ lo trường hợp đầu.
 */

/** `"12,15"` → `[12, 15]`. Bỏ qua phần rác để một dấu phẩy thừa không làm hỏng cả ô. */
export function danhSachId(raw?: string): number[] {
  return (raw ?? '')
    .split(',')
    .map((phan) => Number(phan.trim()))
    .filter((id) => Number.isFinite(id) && id > 0)
}

/** `[12, 15]` → `"12,15"`. */
export function ghepId(ids: number[]): string {
  return ids.join(',')
}
