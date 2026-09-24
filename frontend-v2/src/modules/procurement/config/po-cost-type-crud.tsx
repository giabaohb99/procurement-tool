/**
 * bao-CR-453 — cấu hình CRUD danh mục Loại chi phí thu mua.
 *
 * Tương ứng với entity backend `purchase_cost_type`; endpoint `/api/po-cost-types`.
 */
import { CircleCheck, CircleX } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { formatDateTime } from '@/shared/utils/format-date'

import type { PoCostType } from '../types/purchase-order-detail'

const GROUP_KIND_OPTIONS = [
  { value: '1', label: 'Thuế nộp ngân sách' },
  { value: '2', label: 'Dịch vụ' },
]

const ALLOC_METHOD_OPTIONS = [
  { value: '1', label: 'Theo trọng lượng' },
  { value: '2', label: 'Theo giá trị hàng' },
  { value: '3', label: 'Chia đều' },
  { value: '4', label: 'Thủ công' },
]

function groupKindLabel(v: number): string {
  return GROUP_KIND_OPTIONS.find((o) => o.value === String(v))?.label ?? `Nhóm ${v}`
}

function allocMethodLabel(v: number): string {
  return ALLOC_METHOD_OPTIONS.find((o) => o.value === String(v))?.label ?? `Phương án ${v}`
}

export const PO_COST_TYPE_CRUD_CONFIG: CrudConfig<PoCostType> = {
  entity: 'purchase_cost_type',
  title: 'Loại chi phí thu mua',
  unitLabel: 'loại chi phí',
  apiPath: '/api/po-cost-types',
  storageKey: 'procurement.po-cost-types',
  listRoute: appRoutes.procurement.poCostTypes,
  detailRoute: (id) => appRoutes.procurement.poCostTypeDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên hoặc mã loại…',
  quickFilters: [
    {
      key: 'group_kind',
      label: 'Nhóm',
      type: 'select',
      options: GROUP_KIND_OPTIONS,
    },
    {
      key: 'is_active',
      label: 'Trạng thái',
      type: 'select',
      options: [
        { value: 'true', label: 'Đang dùng' },
        { value: 'false', label: 'Ngừng dùng' },
      ],
    },
  ],
  getItemName: (t) => t.name,
  deleteWarning:
    'Loại chi phí đang được dùng trong chứng từ sẽ bị ảnh hưởng. Xem xét kỹ trước khi xóa.',
  chips: (t) => [
    {
      icon: t.is_active ? CircleCheck : CircleX,
      text: t.is_active ? 'Đang dùng' : 'Ngừng dùng',
      tone: t.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'code',
      header: 'Mã',
      width: 80,
      sortable: true,
      hideable: false,
      cell: (t) => <span className="font-semibold tabular-nums text-primary">{t.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên loại chi phí',
      width: 280,
      sortable: true,
      hideable: false,
      cell: (t) => <span className="font-medium">{t.name}</span>,
    },
    {
      key: 'group_kind',
      header: 'Nhóm',
      width: 180,
      sortable: true,
      cell: (t) => groupKindLabel(t.group_kind),
    },
    {
      key: 'creates_payable',
      header: 'Tạo công nợ',
      width: 120,
      cell: (t) =>
        t.creates_payable ? (
          <Badge variant="default">Có</Badge>
        ) : (
          <Badge variant="secondary">Không</Badge>
        ),
    },
    {
      key: 'default_allocation_method',
      header: 'Phân bổ mặc định',
      width: 170,
      cell: (t) => allocMethodLabel(t.default_allocation_method),
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 120,
      sortable: true,
      cell: (t) => (
        <Badge variant={t.is_active ? 'default' : 'secondary'}>
          {t.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
    {
      key: 'updated_at',
      header: 'Cập nhật',
      width: 150,
      sortable: true,
      sortDescFirst: true,
      cell: (t) => formatDateTime(t.updated_at) || '',
    },
  ],
  filterConfig: {
    fields: [
      { name: 'code', label: 'Mã loại', type: 'number' },
      { name: 'name', label: 'Tên loại chi phí', type: 'text' },
      {
        name: 'group_kind',
        label: 'Nhóm',
        type: 'select',
        options: GROUP_KIND_OPTIONS,
      },
      {
        name: 'is_active',
        label: 'Trạng thái',
        type: 'select',
        options: [
          { value: 'true', label: 'Đang dùng' },
          { value: 'false', label: 'Ngừng dùng' },
        ],
      },
    ],
  },
  formFields: [
    {
      name: 'code',
      label: 'Mã loại',
      type: 'number',
      required: true,
      readonlyOnEdit: true,
      hint: 'Số mã dùng trong tệp và khi tra cứu. Không sửa được sau khi tạo.',
    },
    {
      name: 'name',
      label: 'Tên loại chi phí',
      type: 'text',
      required: true,
      placeholder: 'VD: Phí vận chuyển nội địa, Thuế NK…',
    },
    {
      name: 'group_kind',
      label: 'Nhóm chi phí',
      type: 'select',
      required: true,
      options: GROUP_KIND_OPTIONS,
      hint: '«Thuế nộp ngân sách» để tính chi phí nhập khẩu; «Dịch vụ» cho phí cước và dịch vụ.',
    },
    {
      name: 'creates_payable',
      label: 'Tạo công nợ phải trả',
      type: 'switch',
      defaultValue: true,
      hint: 'Bật thì mỗi khi nhập khoản chi phí này hệ thống tự tạo công nợ cho NCC.',
    },
    {
      name: 'default_allocation_method',
      label: 'Phương pháp phân bổ mặc định',
      type: 'select',
      options: ALLOC_METHOD_OPTIONS,
      hint: 'Người dùng vẫn đổi được khi nhập chứng từ; đây chỉ là mặc định.',
    },
    {
      name: 'default_vat',
      label: 'Thuế suất mặc định (%)',
      type: 'percent',
      hint: 'Ví dụ: nhập 10 cho thuế suất 10%. Người dùng đổi được khi nhập chứng từ.',
    },
    {
      name: 'default_supplier_code',
      label: 'NCC mặc định',
      type: 'text',
      placeholder: 'Mã NCC, VD: NCC001',
      hint: 'Tự điền NCC khi thêm dòng chi phí loại này. Để trống nếu không có mặc định.',
    },
    {
      name: 'sort_order',
      label: 'Thứ tự hiển thị',
      type: 'number',
      defaultValue: 10,
      hint: 'Số nhỏ hơn hiện trước trong danh sách chọn.',
    },
    {
      name: 'is_active',
      label: 'Đang sử dụng',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn loại chi phí trên chứng từ; dữ liệu cũ giữ nguyên.',
    },
    {
      name: 'note',
      label: 'Ghi chú',
      type: 'textarea',
    },
  ],
}
