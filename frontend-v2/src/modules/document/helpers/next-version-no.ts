import { CHANGE_KIND, type DocumentVersion } from '../types/document-record'

/**
 * Số bản mà «mở phiên bản mới» sẽ sinh ra.
 *
 * Phải khớp `backend/app/modules/document/version_service.py::open_new_version`:
 * sửa lớn `major + 1 . 0`, sửa nhỏ `major . minor + 1`, tính từ **SỐ CAO NHẤT ĐÃ
 * TỪNG DÙNG** của văn bản.
 *
 * ⚠️ Hộp thoại trước đây ghi cứng "lên bản 2.0" và "lên bản 1.1". Chỉ đúng đúng
 * một lần trong đời văn bản — lúc đang ở bản 1.0. Văn bản đã lên 2.1 mà hộp
 * thoại vẫn mời "lên bản 1.1" là mời người dùng đi lùi, mà chọn xong lại ra 2.2.
 *
 * ⚠️ Và cũng KHÔNG tính từ bản đang dùng (24/08/2026). Hai số đó bằng nhau ở
 * đường đi thường ngày, nhưng lệch khi có một bản **bị từ chối** nằm lại: bản
 * 1.0 đang có hiệu lực, bản 2.0 bị từ chối, thì backend sinh ra 3.0 còn hộp
 * thoại lại mời "lên bản 2.0" — người dùng bấm theo lời mời rồi nhận một số
 * khác. Số đã dùng thì cháy, kể cả của một bản không bao giờ được ban hành.
 *
 * Danh sách rỗng thì trả `null` — chỗ gọi tự bỏ phần "lên bản …" thay vì bịa ra
 * một con số.
 */
export function nextVersionNo(versions: DocumentVersion[], editLevel: number): string | null {
  const maxHeight = versions.reduce<DocumentVersion | null>((moc, version) => {
    if (!moc) return version
    if (version.major !== moc.major) return version.major > moc.major ? version : moc
    return version.minor > moc.minor ? version : moc
  }, null)

  if (!maxHeight) return null
  return editLevel === CHANGE_KIND.major
    ? `${maxHeight.major + 1}.0`
    : `${maxHeight.major}.${maxHeight.minor + 1}`
}
