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

/**
 * Giá trị `approver_ref` ngay khi đổi CÁCH CHỌN người duyệt. Mọi cách xóa trắng (mã nhân sự của
 * cách cũ đọc thành mã vai trò của cách mới là giao nhầm người), riêng "Người có quyền duyệt"
 * điền sẵn loại chứng từ của luồng — chính là khóa quyền được soi (duoc-CR-680).
 */
export function refAfterKindChange(kind: number, permissionKind: number, entity: string): string {
  return kind === permissionKind ? entity : ''
}

/**
 * Những cách chọn bày ra cho luồng này. "Người có quyền duyệt" chỉ hiện ở loại chứng từ backend mở
 * (`permission_approver_entities`) — lưu ở loại khác backend trả 422. Bước ĐÃ khai cách đó thì vẫn giữ
 * lựa chọn, kẻo ô chọn hiện trống và người sửa không biết bước đang khai gì.
 */
export function visibleApproverKinds<T extends { value: number }>(
  kinds: readonly T[],
  permissionKind: number,
  entity: string,
  supportedEntities: readonly string[] | undefined,
  currentKind: number | undefined,
): T[] {
  const allowed = (supportedEntities ?? []).includes(entity) || currentKind === permissionKind
  return kinds.filter((item) => item.value !== permissionKind || allowed)
}
