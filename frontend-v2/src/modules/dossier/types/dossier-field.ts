/**
 * BỘ TRƯỜNG TÙY BIẾN của một loại hồ sơ — phần «metadata».
 *
 * Mỗi loại hồ sơ tự khai danh sách ô nhập riêng, và màn lập hồ sơ dựng biểu mẫu
 * **theo loại đang chọn**: giấy phép con hỏi *Số giấy phép · Cơ quan cấp*, hợp
 * đồng hỏi *Đối tác · Giá trị*. Không loại nào phải chờ lập trình viên thêm cột.
 *
 * ⚠️ Kiểu ở đây phải khớp `DossierFieldDef` tại
 * `backend/app/modules/dossier/field_schema.py`. Lệch một chữ thì người dùng
 * khai ô xong bấm Lưu và nhận 422 mà câu lỗi nói về một tên trường họ chưa từng
 * gõ.
 */

/**
 * Kiểu ô nhập mà biểu mẫu hồ sơ dựng được.
 *
 * ⚠️ Tập ĐÓNG, và cố ý là **tập con** của `CrudFormField['type']`: mỗi mục ở đây
 * phải có một ô tương ứng mà khung CRUD biết vẽ. Thêm một kiểu chỉ có ở một
 * phía là người dùng khai được ô mà màn hình không hiện, hoặc ngược lại.
 *
 * KHÔNG có `percent`: ô phần trăm quy đổi giữa 8 và 0.08 ở tầng giao diện, mà
 * quy đổi ấy chỉ đúng khi nơi nhận biết trường nào là phần trăm — ô JSON thì
 * không ai biết. Cần tỷ lệ thì khai `number` và ghi đơn vị vào nhãn.
 */
export const DOSSIER_FIELD_TYPES = [
  'text',
  'textarea',
  'number',
  'date',
  'select',
  'switch',
] as const

export type DossierFieldType = (typeof DOSSIER_FIELD_TYPES)[number]

/** Nhãn tiếng Việt của từng kiểu ô — dùng cho ô chọn trong trình khai bộ trường. */
export const DOSSIER_FIELD_TYPE_LABEL: Record<DossierFieldType, string> = {
  text: 'Chữ (một dòng)',
  textarea: 'Chữ (nhiều dòng)',
  number: 'Số',
  date: 'Ngày',
  select: 'Chọn từ danh sách',
  switch: 'Có / Không',
}

/** Khai báo MỘT ô nhập tùy biến. */
export interface DossierFieldDef {
  /**
   * Khóa trong `Dossier.extra_fields` — chữ thường không dấu, số và gạch dưới.
   *
   * ⚠️ Đây là thứ **dữ liệu đã lưu bám vào**. Đổi `key` của một ô đang có dữ
   * liệu không phải là đổi tên: nó tạo ra một ô MỚI rỗng, còn giá trị cũ ở lại
   * dưới khóa cũ. Muốn đổi cách gọi thì sửa `label`.
   */
  key: string
  label: string
  type: DossierFieldType
  required: boolean
  /** Chỉ có nghĩa với `type: 'select'`. */
  options: string[]
  hint: string
}

/** Trần khai ở backend (`field_schema.py`) — nhắc lại để giao diện chặn sớm. */
export const MAX_DOSSIER_FIELDS = 20
export const MAX_DOSSIER_FIELD_OPTIONS = 30

/** Một ô mới toanh cho trình khai bộ trường. */
export function emptyDossierField(): DossierFieldDef {
  return { key: '', label: '', type: 'text', required: false, options: [], hint: '' }
}

/**
 * Chuẩn hoá nhãn thành mã trường — cùng luật với `_key_is_slug` ở backend.
 *
 * Gợi ý mã từ nhãn để người dùng không phải nghĩ ra hai thứ cho một ô; họ vẫn
 * sửa tay được. Bỏ dấu tiếng Việt trước khi cắt, kẻo «Số giấy phép» ra `s_gi_ph`.
 */
export function slugifyFieldKey(raw: string): string {
  const noAccent = (raw || '')
    .normalize('NFD')
    //  Dải dấu thanh + dấu phụ của Unicode, viết bằng mã chứ không gõ thẳng ký
    //  tự tổ hợp (gõ thẳng thì trình soạn thảo nào cũng hiện ra một ô trống và
    //  người sửa sau không biết đang xóa gì).
    .replace(/[\u0300-\u036f]/g, '')
    //  `đ/Đ` KHÔNG nằm trong dải trên — nó là một chữ cái riêng, không phải `d`
    //  cộng dấu. Thiếu dòng này thì «Đơn vị» ra `n_v`.
    .replace(/[đĐ]/g, 'd')

  const key = noAccent
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')

  //  Backend bắt ký tự đầu là CHỮ CÁI: một mã bắt đầu bằng số không dùng làm
  //  tên biến ở bất kỳ đâu về sau (xuất Excel, gõ vào truy vấn).
  return /^[a-z]/.test(key) ? key : key && `f_${key}`
}
