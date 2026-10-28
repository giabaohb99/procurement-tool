import { CircleCheck, CircleX, Layers } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { CrudRecordCard, type CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { HR_COST_GROUP_API_PATH } from '../api/hr-cost-template-api'
import type { HrCostGroup } from '../types/hr-cost'

/**
 * NHÓM CHI PHÍ nhân sự (duoc-CR-690, tài liệu 06 §4.1) — danh mục do người dùng tự đặt (gợi ý sẵn:
 * Quỹ lương · Bắt buộc theo luật · Phúc lợi · Khác). Bảng tự tính của kế hoạch gộp khoản theo nhóm.
 *
 * Không chứa lương ai nên đọc theo `headcount_plan.read`, ghi theo `headcount_plan.write`. Ba ô nên
 * sửa bằng HỘP THOẠI ngay trên danh sách. Xóa nhóm đang có khoản dùng → backend chặn (400).
 */
export const HR_COST_GROUP_CRUD_CONFIG: CrudConfig<HrCostGroup> = {
  entity: 'headcount_plan',
  title: 'Nhóm chi phí',
  description: 'Nhóm để gộp các khoản chi phí nhân sự trên bảng tự tính của kế hoạch.',
  unitLabel: 'nhóm',
  apiPath: HR_COST_GROUP_API_PATH,
  storageKey: 'hr.hr-cost-groups',
  listRoute: appRoutes.hr.hrCostGroups,
  openFormOnRowClick: true,
  deleteInForm: true,
  dialogMaxWidth: 'sm:max-w-md',
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên nhóm…',
  defaultSort: { by: 'sort_order', dir: 'asc' },
  getItemName: (g) => g.name,
  deleteWarning: 'Nhóm đang có khoản chi phí (ở mẫu hoặc kế hoạch) thì không xóa được — chuyển khoản sang nhóm khác trước.',
  mobileCard: (g) => (
    <CrudRecordCard
      title={g.name}
      chips={[
        { icon: Layers, text: `Thứ tự ${g.sort_order}`, tone: 'muted' },
        {
          icon: g.is_active ? CircleCheck : CircleX,
          text: g.is_active ? 'Đang dùng' : 'Ngừng dùng',
          tone: g.is_active ? 'ok' : 'muted',
        },
      ]}
    />
  ),
  columns: [
    { key: 'name', header: 'Tên nhóm', width: 260, hideable: false, sortable: true, cell: (g) => <span className="font-medium">{g.name}</span> },
    { key: 'sort_order', header: 'Thứ tự', width: 100, align: 'right', sortable: true, cell: (g) => <span className="tabular-nums">{g.sort_order}</span> },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      cell: (g) => <Badge variant={g.is_active ? 'default' : 'outline'}>{g.is_active ? 'Đang dùng' : 'Ngừng dùng'}</Badge>,
    },
  ],
  formFields: [
    { name: 'name', label: 'Tên nhóm', type: 'text', required: true, fullWidth: true },
    {
      name: 'sort_order',
      label: 'Thứ tự trên bảng tự tính',
      type: 'number',
      defaultValue: 0,
      hint: 'Số nhỏ đứng trên.',
    },
    { name: 'is_active', label: 'Đang dùng', type: 'switch', defaultValue: true },
  ],
}
