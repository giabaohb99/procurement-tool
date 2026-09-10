import { Badge } from '@/shared/ui/badge'
import type { DataTableColumn } from '@/shared/data-table'
import { formatDateTime } from '@/shared/utils/format-date'
import { CompanyLogoMark } from '../components/company-card'
import { COMPANY_LEVEL_LABELS, type Company } from '../types/company'

/**
 * Cột của bảng DANH MỤC PHÁP NHÂN ở khổ rộng.
 *
 * Tách khỏi trang vì nó là HẰNG — không đọc state nào của màn — và vì mười cột
 * khai tay chiếm hơn một phần ba tệp trang, đẩy phần logic thật (bộ lọc, phân
 * trang, thẻ khổ hẹp) xuống dưới nếp gấp của người đọc mã.
 *
 * ⚠️ Ở khổ điện thoại bảng này KHÔNG dựng — `DataTable` đổi sang `mobileCard`
 * (xem `CompanyCard`). Thêm cột ở đây thì cân nhắc luôn xem thẻ có cần nói
 * điều đó không; hai bên cố ý không giống nhau, nhưng lệch thì phải là lệch có
 * chủ ý.
 */
export const COMPANY_COLUMNS: DataTableColumn<Company>[] = [
  {
    key: 'name',
    header: 'Tên pháp nhân',
    width: 340,
    sortable: true,
    hideable: false,
    cell: (company) => (
      <span className="flex min-w-0 items-center gap-2.5">
        {/* Logo đi kèm trong ô Tên, không tách cột riêng. */}
        <CompanyLogoMark company={company} />
        <span className="truncate">{company.name}</span>
      </span>
    ),
  },
  { key: 'code', header: 'Mã', width: 140, sortable: true, cell: (c) => c.code },
  {
    key: 'level',
    header: 'Cấp',
    width: 180,
    cell: (c) => COMPANY_LEVEL_LABELS[c.level] ?? '—',
  },
  {
    key: 'issue_code',
    header: 'Mã số hiệu',
    width: 140,
    cell: (c) => c.issue_code || '—',
  },
  {
    key: 'short_name',
    header: 'Tên viết tắt',
    width: 180,
    defaultHidden: true,
    cell: (c) => c.short_name || '—',
  },
  { key: 'tax_code', header: 'Mã số thuế', width: 170, cell: (c) => c.tax_code || '—' },
  {
    key: 'legal_rep_name',
    header: 'Người đại diện',
    width: 220,
    cell: (c) => c.legal_rep_name || '—',
  },
  {
    key: 'invoice_email',
    header: 'Email hóa đơn',
    width: 220,
    // Ít khi cần liếc trong danh sách — mặc định ẩn, ai cần thì bật ở menu Cột.
    defaultHidden: true,
    cell: (c) => c.invoice_email || '—',
  },
  {
    key: 'is_active',
    header: 'Trạng thái',
    width: 140,
    cell: (c) => (
      <Badge variant={c.is_active ? 'default' : 'secondary'}>
        {c.is_active ? 'Đang dùng' : 'Ngừng'}
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
    cell: (c) => formatDateTime(c.updated_at) || '',
  },
]
