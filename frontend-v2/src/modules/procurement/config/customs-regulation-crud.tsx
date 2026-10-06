// bao-CR-470 (HQ6 P-01) — cấu hình CRUD danh mục HÓA CHẤT THEO VĂN BẢN.
//
// Entity backend `customs_regulation`, đường API `/api/customs-regulations` (make_crud_router,
// lọc được theo list_code · seq_no · name · name_vi · cas_no · formula · category · is_active). Danh mục SỬA
// ĐƯỢC: nghị định đổi thì người phụ trách cập nhật ngưỡng. Cảnh báo trên màn Tra cứu giá hải
// quan chỉ lấy từ ba danh sách: hoạt chất cấm, NĐ 24 Phụ lục IV (có ngưỡng) và danh sách phải
// công bố. `list_code` là SỐ (1–4 = NĐ 24/2026 Phụ lục I–IV, 10 = TT 75/2025, 11 = TT 01/2026).
import { BookOpen, CircleCheck, CircleX, Hash } from 'lucide-react'

import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { formatQuantity } from '@/shared/utils/format-money'

import type { CustomsRegulation } from '../types/customs'
import { formatRegulationListLabel, REGULATION_LIST_OPTIONS } from '../utils/customs'

const LIST_FILTER_OPTIONS = REGULATION_LIST_OPTIONS.map((item) => ({
  value: String(item.value),
  label: item.label,
}))

const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Đang dùng' },
  { value: 'false', label: 'Ngừng dùng' },
]

export const CUSTOMS_REGULATION_CRUD_CONFIG: CrudConfig<CustomsRegulation> = {
  entity: 'customs_regulation',
  title: 'Danh mục hóa chất theo văn bản',
  description:
    'Hóa chất trong NĐ 24/2026, TT 75/2025, TT 01/2026 — nguồn của cảnh báo pháp lý trên màn Tra cứu thị trường.',
  unitLabel: 'hóa chất',
  apiPath: '/api/customs-regulations',
  //  -v2 (duoc-CR-598): thêm cột STT + Công thức — bản lưu bố cục cũ thắng cột mới (table.md §4).
  storageKey: 'procurement.customs-regulations-v2',
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên hóa chất…',
  quickFilters: [
    { key: 'list_code', label: 'Danh sách', type: 'select', options: LIST_FILTER_OPTIONS },
    { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
  ],
  getItemName: (row) => row.name,
  deleteWarning:
    'Xóa khỏi danh mục thì màn Tra cứu thị trường thôi cảnh báo cho hóa chất này. Muốn tạm tắt thì chuyển sang «Ngừng dùng».',
  chips: (row) => [
    { icon: BookOpen, text: formatRegulationListLabel(row.list_code) },
    ...(row.cas_no ? [{ icon: Hash, text: `CAS ${row.cas_no}`, tone: 'code' as const }] : []),
    {
      icon: row.is_active ? CircleCheck : CircleX,
      text: row.is_active ? 'Đang dùng' : 'Ngừng dùng',
      tone: row.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'list_code',
      header: 'Danh sách',
      width: 230,
      sortable: true,
      wrap: true,
      cell: (row) => formatRegulationListLabel(row.list_code),
    },
    { key: 'seq_no', header: 'STT', width: 70, align: 'right', cell: (row) => row.seq_no },
    {
      key: 'name',
      header: 'Tên khoa học',
      width: 280,
      sortable: true,
      hideable: false,
      wrap: true,
      cell: (row) => <span className="font-medium">{row.name}</span>,
    },
    { key: 'name_vi', header: 'Tên chất', width: 240, wrap: true, cell: (row) => row.name_vi },
    { key: 'cas_no', header: 'Số CAS', width: 120, sortable: true, cell: (row) => row.cas_no },
    { key: 'formula', header: 'Công thức hóa học', width: 140, wrap: true, cell: (row) => row.formula },
    { key: 'category', header: 'Phân loại', width: 160, wrap: true, cell: (row) => row.category },
    {
      key: 'threshold_kg',
      header: 'Ngưỡng (kg)',
      width: 120,
      align: 'right',
      cell: (row) => (
        <span className="tabular-nums">
          {row.threshold_kg === null ? '' : formatQuantity(row.threshold_kg)}
        </span>
      ),
    },
    {
      key: 'mixture_pct',
      header: 'Ngưỡng hỗn hợp (%)',
      width: 130,
      align: 'right',
      cell: (row) => <span className="tabular-nums">{row.mixture_pct === null ? '' : `> ${row.mixture_pct}%`}</span>,
    },
    {
      key: 'banned_year',
      header: 'Năm cấm',
      width: 100,
      align: 'right',
      cell: (row) => row.banned_year || '',
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 120,
      sortable: true,
      cell: (row) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'list_code', label: 'Danh sách', type: 'select', options: LIST_FILTER_OPTIONS },
      { name: 'seq_no', label: 'STT', type: 'text' },
      { name: 'name', label: 'Tên khoa học', type: 'text' },
      { name: 'name_vi', label: 'Tên chất', type: 'text' },
      { name: 'cas_no', label: 'Số CAS', type: 'text' },
      { name: 'formula', label: 'Công thức hóa học', type: 'text' },
      { name: 'category', label: 'Phân loại', type: 'text' },
      { name: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    preserveParams: ['list_code', 'is_active'],
  },
  formFields: [
    {
      name: 'list_code',
      label: 'Danh sách',
      type: 'select',
      required: true,
      section: 'Định danh',
      options: REGULATION_LIST_OPTIONS.map((item) => ({ value: item.value, label: item.label })),
      hint: 'Văn bản và phụ lục chứa hóa chất này. Cảnh báo trên màn tra cứu chỉ lấy từ ba danh sách: hoạt chất cấm, NĐ 24 Phụ lục IV (có ngưỡng) và danh sách phải công bố.',
    },
    {
      name: 'seq_no',
      label: 'STT trong phụ lục',
      type: 'text',
      section: 'Định danh',
      hint: 'Số thứ tự in trong văn bản (vd 59). Để trống nếu văn bản không đánh số.',
    },
    {
      name: 'name',
      label: 'Tên khoa học (danh pháp IUPAC)',
      type: 'text',
      required: true,
      fullWidth: true,
      section: 'Định danh',
    },
    { name: 'name_vi', label: 'Tên chất', type: 'text', fullWidth: true, section: 'Định danh' },
    {
      name: 'cas_no',
      label: 'Số CAS',
      type: 'text',
      section: 'Định danh',
      hint: 'Tra cứu theo công thức (H2SO4…) đổi ra số CAS rồi so đúng ô này.',
    },
    { name: 'formula', label: 'Công thức hóa học', type: 'text', section: 'Định danh' },
    { name: 'category', label: 'Phân loại', type: 'text', section: 'Định danh' },
    {
      name: 'threshold_kg',
      label: 'Ngưỡng khối lượng (kg)',
      type: 'number',
      section: 'Ràng buộc',
      //  `null` chứ không `0`: ngưỡng 0 kg nghĩa là "nhập gam nào cũng vượt" — khác hẳn
      //  "văn bản không nêu ngưỡng". Backend khai `Decimal | None`.
      defaultValue: null,
      nullWhenEmpty: true,
      hint: 'Chỉ NĐ 24/2026 Phụ lục IV có ngưỡng. Để trống nếu văn bản không nêu.',
    },
    {
      name: 'mixture_pct',
      label: 'Ngưỡng hàm lượng hỗn hợp (%)',
      type: 'number',
      section: 'Ràng buộc',
      //  `null` = văn bản không nêu; khác `0` (hỗn hợp chứa bất kỳ lượng nào cũng tính).
      defaultValue: null,
      nullWhenEmpty: true,
      hint: 'Hỗn hợp chứa chất này VƯỢT mức này (theo khối lượng) cũng thuộc danh mục. NĐ 24: Phụ lục II 5%; Phụ lục III nhóm 1 1%, nhóm 2 tiền chất công nghiệp 5%, còn lại 1%.',
    },
    {
      name: 'banned_year',
      label: 'Năm bắt đầu cấm',
      type: 'number',
      section: 'Ràng buộc',
      //  Backend chặn năm ngoài 1900–2100, nên để trống phải gửi `null` chứ không `0`.
      defaultValue: null,
      nullWhenEmpty: true,
      hint: 'Chỉ danh sách hoạt chất cấm (TT 75/2025) có năm cấm. Để trống nếu không có.',
    },
    { name: 'legal_basis', label: 'Căn cứ', type: 'text', fullWidth: true, section: 'Ràng buộc' },
    { name: 'note', label: 'Ghi chú', type: 'textarea', section: 'Khác' },
    {
      name: 'is_active',
      label: 'Đang sử dụng',
      type: 'switch',
      defaultValue: true,
      section: 'Khác',
      hint: 'Ngừng dùng thì không còn hiện trong tra cứu và cảnh báo.',
    },
  ],
}
