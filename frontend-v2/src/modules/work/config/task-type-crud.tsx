import type { CrudConfig } from '@/shared/crud'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import type { WorkTaskType } from '../types/work'

/**
 * Danh mục LOẠI VIỆC của Dự án (duoc-CR-656) — quản trị khai, gác `setting` (đọc/ghi).
 *
 * Mở hộp thoại khi bấm dòng (không có trang chi tiết): danh mục chỉ 5 ô. Loại đã có việc dùng thì «Xóa» chỉ NGỪNG DÙNG
 * (backend giữ lại để số liệu năng lực cũ còn đọc được tên) — câu cảnh báo bên dưới nói rõ điều đó.
 */
export const TASK_TYPE_CRUD_CONFIG: CrudConfig<WorkTaskType> = {
  entity: 'setting',
  title: 'Loại việc',
  description:
    'Danh mục loại việc của Dự án (báo giá, soạn hợp đồng, đối soát…). Chọn loại việc cho mỗi công việc để ' +
    'thống kê thời gian hoàn thành và số lần làm lại theo từng loại.',
  unitLabel: 'loại việc',
  apiPath: '/api/work/task-types',
  storageKey: 'work.task-types',
  listRoute: appRoutes.project.taskTypes,
  searchParam: 'q',
  searchPlaceholder: 'Tìm theo mã hoặc tên loại việc…',
  defaultSort: { by: 'sort_order', dir: 'asc' },
  openFormOnRowClick: true,
  deleteInForm: true,
  getItemName: (t) => t.name,
  deleteWarning:
    'Loại việc đã có công việc dùng sẽ chỉ bị NGỪNG DÙNG (ẩn khỏi ô chọn), không mất — số liệu cũ vẫn giữ tên loại.',
  quickFilters: [
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
  columns: [
    { key: 'code', header: 'Mã', width: 180, sortable: true, hideable: false, cell: (t) => <span className="font-mono text-xs">{t.code}</span> },
    { key: 'name', header: 'Tên loại việc', width: 300, sortable: true, hideable: false, cell: (t) => <span className="font-medium">{t.name}</span> },
    {
      key: 'default_estimate_hours',
      header: 'Ước lượng mặc định',
      width: 170,
      cell: (t) => (t.default_estimate_hours ? `${Number(t.default_estimate_hours)} giờ` : '—'),
    },
    { key: 'task_count', header: 'Số việc đang dùng', width: 150, cell: (t) => t.task_count },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (t) => <Badge variant={t.is_active ? 'default' : 'secondary'}>{t.is_active ? 'Đang dùng' : 'Ngừng'}</Badge>,
    },
  ],
  filterConfig: {
    fields: [
      { name: 'q', label: 'Mã hoặc tên', type: 'text' },
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
      label: 'Mã loại việc',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: BAO_GIA_NCC',
      hint: 'Tối đa 30 ký tự, không trùng trong cùng pháp nhân. Không đổi được sau khi tạo.',
    },
    {
      name: 'name',
      label: 'Tên loại việc',
      type: 'text',
      required: true,
      placeholder: 'VD: Báo giá nhà cung cấp',
      hint: 'Tên hiện trong ô chọn «Loại việc» của công việc (tối đa 120 ký tự).',
    },
    {
      name: 'company_id',
      label: 'Pháp nhân',
      type: 'select',
      source: { url: '/api/companies', valueKey: 'id', labelKey: 'name' },
      defaultValue: 0,
      hint: 'Bỏ trống = dùng chung mọi pháp nhân.',
    },
    {
      name: 'default_estimate_hours',
      label: 'Ước lượng mặc định (giờ)',
      type: 'number',
      hint: 'Chỉ để tham khảo khi giao việc; 0 hoặc bỏ trống = không có.',
    },
    { name: 'sort_order', label: 'Thứ tự hiển thị', type: 'number', defaultValue: 0 },
    {
      name: 'is_active',
      label: 'Đang dùng',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn; công việc cũ vẫn giữ nguyên loại.',
    },
  ],
}
