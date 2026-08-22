/**
 * MỨC MẬT và ĐỘ KHẨN — hai thang của phân hệ Văn thư.
 *
 * Từ 22/08/2026 đây là danh mục CRUD dưới DB (`tab_security_level`, API
 * `/api/security-levels`), không còn khai cứng trong mã. Nguồn chân lý là API,
 * đọc qua `useSecurityLevels()` / `useSecurityLevelOptions()` ở
 * `hooks/use-document-catalogs.ts`. Xem lý do và ràng buộc đầy đủ ở đầu
 * `backend/app/modules/doc_catalog/security_level_model.py`.
 *
 * ─────────────────────────────────────────────────────────────────────────
 * ⚠️ ĐIỀU DỄ SAI NHẤT: `id` KHÁC `value`.
 *
 * - `id` — khóa chính tự tăng của bảng. KHÔNG lưu ở đâu trên văn bản, KHÔNG
 *   mang ý nghĩa thứ bậc. Chỉ dùng để định danh một dòng (sửa/xóa/điều hướng).
 * - `value` — con số lưu xuống `tab_document.secrecy_level` / `.urgency`, và
 *   cũng là THỨ BẬC (càng lớn càng nghiêm / càng gấp). Chỉ duy nhất TRONG MỘT
 *   THANG: "Công khai" (mức mật) và "Thường" (độ khẩn) có thể cùng `value = 1`.
 *
 * Mọi nơi so sánh/lưu/lọc/hiện con số TRÊN VĂN BẢN (secrecy_level, urgency,
 * điều kiện luồng duyệt…) PHẢI dùng `value`. Dùng nhầm `id` là chọn ra một mức
 * mật khác hẳn — sai âm thầm, không lỗi cú pháp, không cảnh báo.
 */

/** 1 = Mức mật · 2 = Độ khẩn — khớp `KIND_CONFIDENTIAL` / `KIND_URGENCY` ở backend. */
export const SECURITY_LEVEL_KIND_CONFIDENTIAL = 1
export const SECURITY_LEVEL_KIND_URGENCY = 2

export type SecurityLevelKind =
  | typeof SECURITY_LEVEL_KIND_CONFIDENTIAL
  | typeof SECURITY_LEVEL_KIND_URGENCY

export const SECURITY_LEVEL_KIND_LABELS: Record<SecurityLevelKind, string> = {
  [SECURITY_LEVEL_KIND_CONFIDENTIAL]: 'Mức mật',
  [SECURITY_LEVEL_KIND_URGENCY]: 'Độ khẩn',
}

export interface SecurityLevel {
  /** Khóa chính. KHÔNG phải giá trị lưu trên văn bản — xem cảnh báo ở đầu tệp. */
  id: number
  kind: SecurityLevelKind
  /** Con số lưu xuống văn bản, đồng thời là thứ bậc. Không sửa được sau khi tạo. */
  value: number
  /** Chữ HOA, `[A-Z0-9_]`. */
  code: string
  name: string
  description: string
  is_active: boolean
}

/** Trường sửa được qua PATCH — backend cố ý KHÔNG cho sửa `kind` và `value`. */
export type SecurityLevelEditableFields = Pick<
  SecurityLevel,
  'code' | 'name' | 'description' | 'is_active'
>

/**
 * BẢN DỰ PHÒNG — bảy dòng gốc, dùng ĐÚNG dữ liệu seed ban đầu
 * (`backend/app/seed_data/document_phase1.py`).
 *
 * Chỉ dùng ở chỗ KHÔNG gọi được hook: module cấu hình nạp lúc import (bộ lọc,
 * điều kiện luồng duyệt) hoặc lúc dữ liệu thật CHƯA nạp xong. Đây KHÔNG phải
 * nguồn chân lý — quản trị sửa danh mục trên `/document/settings` thì các chỗ
 * dùng hằng số này không tự cập nhật theo. `id` dưới đây chỉ để khớp kiểu
 * `SecurityLevel`, KHÔNG phải khóa chính thật của DB — đừng gửi lên server.
 */
export const FALLBACK_CONFIDENTIAL_LEVELS: SecurityLevel[] = [
  {
    id: 1,
    kind: SECURITY_LEVEL_KIND_CONFIDENTIAL,
    value: 1,
    code: 'CONGKHAI',
    name: 'Công khai',
    description: 'Ai trong tập đoàn cũng đọc được, gửi ra ngoài cũng không sao.',
    is_active: true,
  },
  {
    id: 2,
    kind: SECURITY_LEVEL_KIND_CONFIDENTIAL,
    value: 2,
    code: 'NOIBO',
    name: 'Nội bộ',
    description:
      'Người trong tập đoàn đọc được, không gửi ra ngoài. Cũng là mức mặc định của một người khi chưa được cấp mức nào khác.',
    is_active: true,
  },
  {
    id: 3,
    kind: SECURITY_LEVEL_KIND_CONFIDENTIAL,
    value: 3,
    code: 'MAT',
    name: 'Mật',
    description: 'Chỉ người đã được cấp mức Mật mới đọc được, và mức cấp đó có thời hạn.',
    is_active: true,
  },
  {
    id: 4,
    kind: SECURITY_LEVEL_KIND_CONFIDENTIAL,
    value: 4,
    code: 'TUYETMAT',
    name: 'Tuyệt mật',
    description: 'Chỉ xem trên web, không cho tải tệp, có dấu chìm mang tên người xem.',
    is_active: true,
  },
]

export const FALLBACK_URGENCY_LEVELS: SecurityLevel[] = [
  {
    id: 5,
    kind: SECURITY_LEVEL_KIND_URGENCY,
    value: 1,
    code: 'THUONG',
    name: 'Thường',
    description: 'Xử lý theo thứ tự thông thường.',
    is_active: true,
  },
  {
    id: 6,
    kind: SECURITY_LEVEL_KIND_URGENCY,
    value: 2,
    code: 'KHAN',
    name: 'Khẩn',
    description: 'Xử lý trong ngày.',
    is_active: true,
  },
  {
    id: 7,
    kind: SECURITY_LEVEL_KIND_URGENCY,
    value: 3,
    code: 'HOATOC',
    name: 'Hỏa tốc',
    description: 'Chuyển và xử lý tức thì.',
    is_active: true,
  },
]

export const FALLBACK_SECURITY_LEVELS: SecurityLevel[] = [
  ...FALLBACK_CONFIDENTIAL_LEVELS,
  ...FALLBACK_URGENCY_LEVELS,
]

/**
 * Ngưỡng VALUE (không phải id) của mức mật "Mật" trở lên — từ đây mô tả có
 * HỨA hệ thống sẽ chặn người không đủ mức. `value` của "Mật" đứng yên theo
 * đúng ràng buộc ở đầu tệp nên hằng số này an toàn để khai cứng.
 */
export const CONFIDENTIAL_MAT_VALUE = 3
