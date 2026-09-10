import { Badge } from '@/shared/ui/badge'
import type { DataTableColumn } from '@/shared/data-table'
import { formatDateTime } from '@/shared/utils/format-date'
import { DEPARTMENT_KIND_LABELS, type Department } from '../types/department'

/**
 * Cột của bảng DANH MỤC PHÒNG BAN ở khổ rộng.
 *
 * Tách khỏi trang vì nó là HẰNG — không đọc state nào của màn — và bảy cột khai
 * tay đẩy phần logic thật (bộ lọc, phân trang, thẻ khổ hẹp) xuống dưới nếp gấp
 * của người đọc mã. Cùng cách `company-columns.tsx`.
 *
 * ⚠️ Ở khổ điện thoại bảng này KHÔNG dựng — `DataTable` đổi sang `mobileCard`
 * (khai ngay trong trang). Thêm cột ở đây thì cân nhắc luôn xem thẻ có cần nói
 * điều đó không.
 */
export const DEPARTMENT_COLUMNS: DataTableColumn<Department>[] = [
  { key: 'code', header: 'Mã', width: 150, sortable: true, cell: (d) => d.code },
  {
    key: 'issue_code',
    header: 'Mã số hiệu',
    width: 140,
    cell: (d) => d.issue_code || '—',
  },
  {
    key: 'name',
    header: 'Phòng ban',
    width: 300,
    sortable: true,
    hideable: false,
    cell: (d) => <span className="truncate">{d.name}</span>,
  },
  {
    key: 'kind',
    header: 'Loại đơn vị',
    width: 230,
    cell: (d) => DEPARTMENT_KIND_LABELS[d.kind],
  },
  {
    key: 'manager_name',
    header: 'Trưởng bộ phận',
    width: 260,
    cell: (d) => d.manager_name || '—',
  },
  {
    key: 'is_active',
    header: 'Trạng thái',
    width: 140,
    cell: (d) => (
      <Badge variant={d.is_active ? 'default' : 'secondary'}>
        {d.is_active ? 'Hoạt động' : 'Đã ẩn'}
      </Badge>
    ),
  },
  {
    // bao-CR-300 (ticket 21) — cột "Ngày cập nhật", bấm lần đầu ra mới nhất trước.
    key: 'updated_at',
    header: 'Ngày cập nhật',
    width: 150,
    sortable: true,
    sortDescFirst: true,
    cell: (d) => formatDateTime(d.updated_at) || '',
  },
]
