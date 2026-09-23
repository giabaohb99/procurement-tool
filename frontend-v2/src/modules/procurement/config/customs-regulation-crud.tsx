// bao-CR-470 (HQ6 P-01) — cấu hình CRUD danh mục HÓA CHẤT THEO VĂN BẢN.
//
// Entity backend `customs_regulation`, đường API `/api/customs-regulations` (make_crud_router,
// lọc được theo list_code · name · name_vi · cas_no · category · is_active). Danh mục SỬA
// ĐƯỢC: nghị định đổi thì người phụ trách cập nhật ngưỡng. Cảnh báo trên màn Tra cứu giá hải
// quan chỉ lấy từ ba danh sách: hoạt chất cấm, NĐ 24 Phụ lục IV (có ngưỡng) và danh sách phải
// công bố. `list_code` là SỐ (1–4 = NĐ 24/2026 Phụ lục I–IV, 10 = TT 75/2025, 11 = TT 01/2026).
import { BookOpen, CircleCheck, CircleX, Hash } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
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
    'Hóa chất trong NĐ 24/2026, TT 75/2025, TT 01/2026 — nguồn của cảnh báo pháp lý trên màn Tra cứu giá hải quan.',
  unitLabel: 'hóa chất',
  apiPath: '/api/customs-regulations',
  storageKey: 'procurement.customs-regulations',
  listRoute: appRoutes.procurement.customsRegulations,
  detailRoute: (id) => appRoutes.procurement.customsRegulationDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên hóa chất…',
  quickFilters: [
    { key: 'list_code', label: 'Danh sách', type: 'select', options: LIST_FILTER_OPTIONS },
    { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
  ],
  getItemName: (row) => row.name,
  deleteWarning:
    'Xóa khỏi danh mục thì màn Tra cứu giá hải quan thôi cảnh báo cho hóa chất này. Muốn tạm tắt thì chuyển sang «Ngừng dùng».',
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
    {
      key: 'name',
      header: 'Tên',
      width: 280,
      sortable: true,
      hideable: false,
      wrap: true,
      cell: (row) => <span className="font-medium">{row.name}</span>,
    },
    { key: 'name_vi', header: 'Tên tiếng Việt', width: 240, wrap: true, cell: (row) => row.name_vi },
    { key: 'cas_no', header: 'Số CAS', width: 120, sortable: true, cell: (row) => row.cas_no },
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
      { name: 'name', label: 'Tên', type: 'text' },
      { name: 'name_vi', label: 'Tên tiếng Việt', type: 'text' },
      { name: 'cas_no', label: 'Số CAS', type: 'text' },
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
    { name: 'name', label: 'Tên (theo văn bản)', type: 'text', required: true, fullWidth: true, section: 'Định danh' },
    { name: 'name_vi', label: 'Tên tiếng Việt', type: 'text', fullWidth: true, section: 'Định danh' },
    {
      name: 'cas_no',
      label: 'Số CAS',
      type: 'text',
      section: 'Định danh',
      hint: 'Tra cứu theo công thức (H2SO4…) đổi ra số CAS rồi so đúng ô này.',
    },
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
