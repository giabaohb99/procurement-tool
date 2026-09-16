/**
 * Kiểu dữ liệu của phân hệ HỒ SƠ.
 *
 * ⚠️ Bản MẪU: chưa có bảng nào dưới MySQL, chưa có khóa phân quyền. Các trường ở
 * đây đặt theo khuôn chung của mọi loại hồ sơ (mã · tên · loại · nơi giữ · hạn
 * hiệu lực) để chốt giao diện trước; chốt xong loại hồ sơ thật thì sửa ở đây rồi
 * mới dựng model backend.
 */

/**
 * Trạng thái hồ sơ — mã **SỐ** theo luật R2 (QĐ-11): kho lưu số, tiếng Việt chỉ
 * sống ở tầng hiển thị. Đừng đổi số của mã đã phát hành, thêm thì nối vào cuối.
 */
export const DOSSIER_STATUS = {
  /** Mới lập, chưa nộp vào kho hồ sơ. */
  DRAFT: 1,
  /** Đang còn hiệu lực. */
  ACTIVE: 2,
  /** Còn hiệu lực nhưng sắp tới hạn — cần gia hạn. */
  EXPIRING: 3,
  /** Đã quá hạn hiệu lực. */
  EXPIRED: 4,
  /** Hết vòng đời, chuyển kho lưu trữ. */
  ARCHIVED: 5,
} as const

export type DossierStatus = (typeof DOSSIER_STATUS)[keyof typeof DOSSIER_STATUS]

export const DOSSIER_STATUS_LABEL: Record<DossierStatus, string> = {
  [DOSSIER_STATUS.DRAFT]: 'Nháp',
  [DOSSIER_STATUS.ACTIVE]: 'Còn hiệu lực',
  [DOSSIER_STATUS.EXPIRING]: 'Sắp hết hạn',
  [DOSSIER_STATUS.EXPIRED]: 'Hết hạn',
  [DOSSIER_STATUS.ARCHIVED]: 'Đã lưu trữ',
}

export interface Dossier {
  id: number
  /** Mã hồ sơ do người dùng đặt, duy nhất — vd `HS-2026-014`. */
  code: string
  name: string
  /**
   * Loại hồ sơ. Để **chuỗi tự do** ở bản mẫu vì danh mục loại chưa chốt; khi có
   * danh mục thật thì đổi thành `type_id` + nhãn chép (xem cách làm của Chức vụ).
   */
  type_name: string
  /** Bộ phận đang giữ bản gốc. */
  department_name: string
  /** Người chịu trách nhiệm theo dõi hồ sơ. */
  owner_name: string
  /** Ngày lập / ngày ký — dạng ISO `yyyy-mm-dd`. */
  issued_date: string
  /** Hạn hiệu lực. **Rỗng = vô thời hạn**, không phải thiếu dữ liệu. */
  expiry_date: string
  status: DossierStatus
  /** Số tệp đã đính kèm. */
  attachment_count: number
  /** Nơi giữ bản giấy — vd `Tủ A2 · P. Hành chính`. */
  storage_location: string
}

/** Một trang kết quả — cùng khuôn với phong bì phân trang của backend. */
export interface DossierListResult {
  items: Dossier[]
  total: number
}
