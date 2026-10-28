import { CircleCheck, CircleX, ListChecks } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { CrudRecordCard, type CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { HR_COST_TEMPLATE_API_PATH } from '../api/hr-cost-template-api'
import type { HrCostTemplate } from '../types/hr-cost'

/**
 * MẪU KHOẢN CHI PHÍ (duoc-CR-690, tài liệu 06 §4.1): mỗi mẫu là một bộ khoản («Mẫu văn phòng»,
 * «Mẫu nhà máy»…). Tạo kế hoạch thì hệ thống CHÉP bộ khoản của mẫu vào kế hoạch; sửa mẫu về sau
 * không làm trôi con số của kế hoạch đã lập. Thêm / mở là TRANG RIÊNG vì có bảng khoản sửa tại chỗ.
 */
export const HR_COST_TEMPLATE_CRUD_CONFIG: CrudConfig<HrCostTemplate> = {
  entity: 'headcount_plan',
  title: 'Mẫu khoản chi phí',
  description: 'Bộ khoản chi phí nhân sự để chép vào kế hoạch lúc lập. Sửa mẫu không làm đổi kế hoạch đã lập.',
  unitLabel: 'mẫu',
  apiPath: HR_COST_TEMPLATE_API_PATH,
  storageKey: 'hr.hr-cost-templates',
  listRoute: appRoutes.hr.hrCostTemplates,
  createRoute: appRoutes.hr.hrCostTemplateNew,
  detailRoute: (id) => appRoutes.hr.hrCostTemplateDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên mẫu…',
  getItemName: (t) => t.name,
  deleteWarning: 'Kế hoạch đã lập từ mẫu này vẫn giữ nguyên bộ khoản đã chép.',
  mobileCard: (t) => (
    <CrudRecordCard
      title={t.name}
      subtitle={t.note}
      chips={[
        ...(t.item_count != null ? [{ icon: ListChecks, text: `${t.item_count} khoản`, tone: 'code' as const }] : []),
        {
          icon: t.is_active ? CircleCheck : CircleX,
          text: t.is_active ? 'Đang dùng' : 'Ngừng dùng',
          tone: t.is_active ? ('ok' as const) : ('muted' as const),
        },
      ]}
    />
  ),
  columns: [
    { key: 'name', header: 'Tên mẫu', width: 260, hideable: false, sortable: true, cell: (t) => <span className="font-medium">{t.name}</span> },
    {
      key: 'item_count',
      header: 'Số khoản',
      width: 100,
      align: 'right',
      cell: (t) => <span className="tabular-nums">{t.item_count ?? t.items?.length ?? ''}</span>,
    },
    { key: 'note', header: 'Ghi chú', width: 320, wrap: true, cell: (t) => t.note || '' },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      cell: (t) => <Badge variant={t.is_active ? 'default' : 'outline'}>{t.is_active ? 'Đang dùng' : 'Ngừng dùng'}</Badge>,
    },
  ],
  //  Thêm / sửa ở trang riêng (`hr-cost-template-detail-page.tsx`).
  formFields: [],
}
