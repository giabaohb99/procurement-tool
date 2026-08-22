/**
 * MỨC MẬT và ĐỘ KHẨN — hai thang **cố định, khai trong mã**, không phải danh mục
 * sửa được trên giao diện.
 *
 * Vì sao không cho sửa: mức mật là số nguyên lưu thẳng trên `tab_document`
 * (`secrecy_level` 1–4, `urgency` 1–3) và mọi lớp kiểm quyền so sánh bằng con số
 * đó. Cho người dùng thêm "mức 5" hay đổi thứ bậc thì phần kiểm quyền hiểu một
 * đằng, danh mục nói một nẻo — mà sai ở đây nghĩa là lộ văn bản mật.
 *
 * Thang lấy theo `van-thu/04` mục 5.2. Tên hiển thị đang chờ chốt câu **B3**;
 * đổi tên thì sửa đúng bảng dưới đây, KHÔNG đổi số.
 */

export type SecurityLevelKind = 'confidential' | 'urgent'

export const SECURITY_LEVEL_KIND_LABELS: Record<SecurityLevelKind, string> = {
  confidential: 'Mức mật',
  urgent: 'Độ khẩn',
}

export interface SecurityLevel {
  /** Chính là giá trị lưu xuống DB (1–4 với mật, 1–3 với khẩn). */
  id: number
  code: string
  name: string
  kind: SecurityLevelKind
  /** Càng lớn càng nghiêm / càng gấp. Trùng `id` trong cùng một thang. */
  rank: number
  description: string
  /** Luôn `true` — giữ trường cho bảng dùng chung `CatalogTable` khỏi phải rẽ nhánh. */
  is_active: boolean
}

/**
 * Bốn mức mật. Chưa cấp gì cho một người thì người đó ở mức 2 Nội bộ.
 *
 * `description` viết từ góc nhìn **VĂN BẢN** — trả lời "đóng dấu mức này thì ai
 * đọc được, bị chặn cái gì". Đây là câu hiện làm dòng phụ trong ô chọn mức mật
 * lúc tạo văn bản, nên nó phải giúp người soạn CHỌN được; câu mô tả quyền của
 * người đọc thì không giúp gì cho việc đó.
 */
export const CONFIDENTIAL_LEVELS: SecurityLevel[] = [
  {
    id: 1,
    code: 'CONGKHAI',
    name: 'Công khai',
    kind: 'confidential',
    rank: 1,
    description: 'Ai trong tập đoàn cũng đọc được, gửi ra ngoài cũng không sao.',
    is_active: true,
  },
  {
    id: 2,
    code: 'NOIBO',
    name: 'Nội bộ',
    kind: 'confidential',
    rank: 2,
    description:
      'Người trong tập đoàn đọc được, không gửi ra ngoài. Cũng là mức mặc định của một người khi chưa được cấp mức nào khác.',
    is_active: true,
  },
  {
    id: 3,
    code: 'MAT',
    name: 'Mật',
    kind: 'confidential',
    rank: 3,
    description:
      'Chỉ người đã được cấp mức Mật mới đọc được, và mức cấp đó có thời hạn.',
    is_active: true,
  },
  {
    id: 4,
    code: 'TUYETMAT',
    name: 'Tuyệt mật',
    kind: 'confidential',
    rank: 4,
    description: 'Chỉ xem trên web, không cho tải tệp, có dấu chìm mang tên người xem.',
    is_active: true,
  },
]

/** Ba độ khẩn. **Độc lập hoàn toàn với mức mật** — thông báo hỏa tốc vẫn có thể công khai. */
export const URGENCY_LEVELS: SecurityLevel[] = [
  {
    id: 1,
    code: 'THUONG',
    name: 'Thường',
    kind: 'urgent',
    rank: 1,
    description: 'Xử lý theo thứ tự thông thường.',
    is_active: true,
  },
  {
    id: 2,
    code: 'KHAN',
    name: 'Khẩn',
    kind: 'urgent',
    rank: 2,
    description: 'Xử lý trong ngày.',
    is_active: true,
  },
  {
    id: 3,
    code: 'HOATOC',
    name: 'Hỏa tốc',
    kind: 'urgent',
    rank: 3,
    description: 'Chuyển và xử lý tức thì.',
    is_active: true,
  },
]

export const SECURITY_LEVELS: SecurityLevel[] = [...CONFIDENTIAL_LEVELS, ...URGENCY_LEVELS]

/** Tên mức mật theo số lưu trong DB; số lạ thì trả về chính con số đó. */
export function secrecyLabel(level: number): string {
  return CONFIDENTIAL_LEVELS.find((item) => item.id === level)?.name ?? String(level)
}

export function urgencyLabel(level: number): string {
  return URGENCY_LEVELS.find((item) => item.id === level)?.name ?? String(level)
}
