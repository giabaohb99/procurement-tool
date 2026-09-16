/**
 * Danh mục LOẠI HỒ SƠ — dữ liệu THẬT, bảng `tab_dossier_type`.
 *
 * Trường phải khớp `DossierTypeResponse` ở
 * `backend/app/modules/dossier/type_schema.py`.
 *
 * Loại quyết định hai thứ ở màn hồ sơ: nhóm để lọc, và **hạn hiệu lực mặc định**
 * gợi ý khi lập hồ sơ mới.
 */
//  ⚠️ `type` chứ KHÔNG `interface`: khung CRUD khai báo ràng `T extends
//  CrudRecord` (`Record<string, unknown>`), mà TypeScript chỉ cấp "chỉ mục
//  ngầm" cho type alias — một `interface` y hệt sẽ báo không gán được. Cùng lý
//  do `JobPosition` và `MeetingRoom` cũng là `type`.
export type DossierType = {
  id: number
  /** Mã ngắn viết HOA, duy nhất — vd `HD`. Backend tự ép hoa; không sửa được sau khi tạo. */
  code: string
  name: string
  description: string
  /**
   * Hạn hiệu lực mặc định, tính bằng **tháng** kể từ ngày lập.
   * `0` = loại hồ sơ **vô thời hạn** — lựa chọn thật, không phải ô bỏ trống.
   */
  default_valid_months: number
  /**
   * Còn dùng hay đã ngừng. Ngừng thì không gán MỚI được nữa, nhưng hồ sơ đang
   * mang loại đó vẫn giữ nguyên — cùng luật với danh mục Chức vụ (CR-320).
   */
  is_active: boolean
  /**
   * Thứ tự bày trong danh sách và ô chọn.
   *
   * ⚠️ CỐ Ý không lên giao diện (bài học duoc-CR-321): «thứ tự» là khái niệm của
   * người dựng hệ thống, bày ra bảng thì người dùng thấy toàn 10·20·130 mà không
   * chỗ nào giải nghĩa. Vẫn phải gửi `sort_by=sort_order` khi gọi API, kẻo danh
   * mục tự đổi chỗ mỗi lần thêm một dòng.
   */
  sort_order: number
  /** Bộ sinh CRUD gắn thêm cho mọi danh mục (bao-CR-294). */
  updated_at?: string | null
}

/** Dữ liệu người dùng nhập ở hộp thoại Thêm / Sửa. */
export type DossierTypeInput = Omit<DossierType, 'id' | 'updated_at'>
