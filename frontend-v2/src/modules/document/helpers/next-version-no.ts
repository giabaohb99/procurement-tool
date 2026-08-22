import { CHANGE_KIND, type DocumentVersion } from '../types/document-record'

/**
 * Số bản mà «mở phiên bản mới» sẽ sinh ra, tính từ bản ĐANG DÙNG.
 *
 * Phải khớp `backend/app/modules/document/version_service.py::open_version`:
 * sửa lớn `major + 1 . 0`, sửa nhỏ `major . minor + 1`.
 *
 * ⚠️ Hộp thoại trước đây ghi cứng "lên bản 2.0" và "lên bản 1.1". Chỉ đúng đúng
 * một lần trong đời văn bản — lúc đang ở bản 1.0. Văn bản đã lên 2.1 mà hộp
 * thoại vẫn mời "lên bản 1.1" là mời người dùng đi lùi, mà chọn xong lại ra 2.2.
 *
 * Chưa có bản nào đang dùng thì trả `null` — chỗ gọi tự bỏ phần "lên bản …"
 * thay vì bịa ra một con số.
 */
export function soBanKeTiep(
  hienTai: DocumentVersion | undefined,
  mucSua: number,
): string | null {
  if (!hienTai) return null
  return mucSua === CHANGE_KIND.major
    ? `${hienTai.major + 1}.0`
    : `${hienTai.major}.${hienTai.minor + 1}`
}
