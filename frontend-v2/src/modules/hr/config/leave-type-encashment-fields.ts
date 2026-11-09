import type { CrudFormField } from '@/shared/crud'

/**
 * Nhóm ô THANH TOÁN NGHỈ PHÉP của danh mục Loại nghỉ (duoc-CR-719) — tách khỏi `leave-type-crud.tsx` (đã ~500 dòng).
 *
 * Ba cột backend: `allow_encashment` · `max_encashable_days` (trần THEO NĂM, 0 = không trần) · `non_encashable_days`
 * (số ngày phải giữ lại, chỉ áp cho lý do cuối năm). Backend chặn `allow_encashment` khi loại nghỉ không trừ quỹ (422).
 *
 * ⚠️ Công tắc LUÔN hiện, cố ý không gắn `showWhen`: khung CRUD vẫn gửi giá trị của ô bị ẩn, nên ẩn công tắc khi tắt
 * "Trừ vào quỹ phép năm" thì giá trị `true` cũ vẫn đi lên và ăn 422 — người dùng không còn ô nào để gạt về tắt.
 * Hai ô số thì ẩn được (giá trị cũ không làm hỏng gì) — chỉ hiện khi cả hai công tắc cùng bật.
 */
export const ENCASHMENT_SECTION = 'Thanh toán nghỉ phép'

export const ENCASHMENT_SECTION_DESCRIPTION =
  'Cho đổi ngày phép chưa nghỉ ra tiền khi cuối năm còn dư hoặc khi nghỉ việc. Phiếu thanh toán chỉ ghi số ngày; ' +
  'số tiền do kế toán nhập ở yêu cầu thanh toán.'

const countsBalance = (values: Record<string, unknown>) => Boolean(values.counts_balance)
const encashmentOn = (values: Record<string, unknown>) =>
  countsBalance(values) && Boolean(values.allow_encashment)

export const LEAVE_TYPE_ENCASHMENT_FIELDS: CrudFormField[] = [
  {
    name: 'allow_encashment',
    label: 'Cho phép thanh toán nghỉ phép',
    type: 'switch',
    defaultValue: false,
    section: ENCASHMENT_SECTION,
    hint: 'Chỉ dùng được khi "Trừ vào quỹ phép năm" đang bật. Tắt ô đó thì tắt cả nút này, không thì lưu sẽ báo lỗi.',
  },
  {
    name: 'max_encashable_days',
    label: 'Tối đa mỗi năm (ngày)',
    type: 'number',
    defaultValue: 0,
    section: ENCASHMENT_SECTION,
    showWhen: encashmentOn,
    hint: '0 = không giới hạn. Cộng dồn mọi phiếu đã duyệt trong cùng năm quỹ. Phiếu lý do nghỉ việc không bị giới hạn.',
  },
  {
    name: 'non_encashable_days',
    label: 'Số ngày phải giữ lại',
    type: 'number',
    defaultValue: 0,
    section: ENCASHMENT_SECTION,
    showWhen: encashmentOn,
    hint: 'Số ngày không được đổi ra tiền khi thanh toán cuối năm. VD còn dư 10 ngày, giữ lại 4 thì được thanh toán 6. Phần mang sang từ năm trước không tính.',
  },
]
