// Cột của bảng mục «Thuốc BVTV» (Tra cứu thị trường, 29/09/2026).
//
// ⚠️ Đổi thứ tự / thêm bớt cột thì đổi luôn `PESTICIDE_TABLE_STORAGE_KEY`: bảng nhớ bố cục
// theo khóa đó và bản lưu cũ THẮNG toàn bộ (docs/ui/table.md §4).
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

import { CustomsPesticideStatusBadge } from '../components/customs/customs-pesticide-status-badge'
import type { CustomsPesticide } from '../types/customs-pesticide'

//  v2 (29/09/2026): thêm cột «Hoạt chất cấm».
export const PESTICIDE_TABLE_STORAGE_KEY = 'procurement.customs-pesticides-v2'

export const CUSTOMS_PESTICIDE_COLUMNS: DataTableColumn<CustomsPesticide>[] = [
  {
    key: 'trade_name',
    header: 'Tên thuốc',
    width: 200,
    defaultPinned: true,
    cell: (row) => (
      <span className="font-medium">
        {row.trade_name}
        {/*  Thuốc thêm tay trên màn — nạp lại danh mục giữ nó (duoc-CR-490). */}
        {row.is_manual && (
          <Badge variant="outline" className="ml-1.5 align-middle text-[10px] font-normal">
            Tự thêm
          </Badge>
        )}
      </span>
    ),
  },
  { key: 'active_ingredient', header: 'Hoạt chất', width: 260, cell: (row) => row.active_ingredient },
  //  Đối chiếu với danh sách cấm TT 75/2025 ở mục «Pháp lý» — khớp theo tên, thường trống vì
  //  nguồn đã bỏ thuốc cấm. Có chữ ở cột này là danh mục vừa lọt một thuốc cần xem lại.
  {
    key: 'banned',
    header: 'Hoạt chất cấm',
    width: 180,
    wrap: true,
    cell: (row) =>
      row.banned.length > 0 ? (
        <span className="flex flex-wrap gap-1">
          {row.banned.map((item) => (
            <Badge key={item.id} className={cn('whitespace-normal', TONE_CLASS.danger)}>
              {item.name}
            </Badge>
          ))}
        </span>
      ) : null,
  },
  { key: 'concentration', header: 'Hàm lượng', width: 120, cell: (row) => row.concentration },
  { key: 'pest_group', header: 'Phân nhóm', width: 170, cell: (row) => row.pest_group },
  { key: 'registrant', header: 'Công ty đăng ký', width: 240, cell: (row) => row.registrant },
  { key: 'registration_no', header: 'Số đăng ký', width: 160, cell: (row) => row.registration_no },
  {
    key: 'expires_on',
    header: 'Hết hạn đăng ký',
    width: 140,
    cell: (row) => <span className="tabular-nums">{formatDate(row.expires_on)}</span>,
  },
  {
    key: 'status',
    header: 'Tình trạng',
    width: 140,
    cell: (row) => <CustomsPesticideStatusBadge status={row.status} label={row.status_label} />,
  },
  {
    key: 'use_count',
    header: 'Phạm vi sử dụng',
    width: 140,
    align: 'right',
    cell: (row) => <span className="tabular-nums">{row.use_count || ''}</span>,
  },
  { key: 'sector', header: 'Lĩnh vực', width: 240, defaultHidden: true, cell: (row) => row.sector },
]
