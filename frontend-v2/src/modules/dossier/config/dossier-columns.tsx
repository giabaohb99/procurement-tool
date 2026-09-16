import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'
import { DossierStatusBadge } from '../components/dossier-status-badge'
import type { Dossier } from '../types/dossier'

/**
 * Cột của bảng Hồ sơ.
 *
 * Hằng số tầng module (không phụ thuộc state) nên truyền thẳng vào `DataTable`
 * được, khỏi `useMemo` ở trang — identity đã ổn định sẵn.
 *
 * ⚠️ Bề rộng đặt sao cho **tổng các cột hiện sẵn vừa khung ở màn 1600px** (đo
 * 16/09/2026: vùng bảng ≈ 1265px sau khi trừ thanh bên và phần đệm). Cột
 * *Trạng thái* mà rơi ra ngoài mép phải thì người dùng phải cuộn ngang mới biết
 * hồ sơ nào sắp hết hạn — đúng thứ họ mở màn này để tìm. Thêm cột mới thì hoặc
 * bớt bề rộng chỗ khác, hoặc cho cột mới `defaultHidden`.
 */
export const DOSSIER_COLUMNS: DataTableColumn<Dossier>[] = [
  {
    key: 'code',
    header: 'Mã hồ sơ',
    width: 130,
    hideable: false,
    defaultPinned: true,
    cell: (row) => <span className="font-mono text-sm">{row.code}</span>,
  },
  {
    key: 'name',
    header: 'Tên hồ sơ',
    width: 280,
    hideable: false,
    wrap: true,
    cell: (row) => <span className="font-medium">{row.name}</span>,
  },
  { key: 'type_name', header: 'Loại hồ sơ', width: 150, cell: (row) => row.type_name },
  {
    key: 'department_name',
    header: 'Bộ phận giữ',
    width: 140,
    cell: (row) => row.department_name,
  },
  { key: 'owner_name', header: 'Người phụ trách', width: 150, cell: (row) => row.owner_name },
  {
    key: 'issued_date',
    header: 'Ngày lập',
    width: 110,
    cell: (row) => formatDate(row.issued_date),
  },
  {
    key: 'expiry_date',
    header: 'Hạn hiệu lực',
    width: 125,
    //  Ô rỗng nghĩa là VÔ THỜI HẠN, không phải thiếu dữ liệu — để trống thì người
    //  đọc tưởng hồ sơ chưa ai nhập hạn và đi tìm cho đủ.
    cell: (row) =>
      row.expiry_date ? (
        formatDate(row.expiry_date)
      ) : (
        <span className="text-muted-foreground">Vô thời hạn</span>
      ),
  },
  {
    key: 'status',
    header: 'Trạng thái',
    width: 135,
    cell: (row) => <DossierStatusBadge status={row.status} />,
  },
  {
    key: 'attachment_count',
    header: 'Số tệp',
    width: 90,
    align: 'right',
    //  Ẩn sẵn cùng nhóm với *Nơi lưu bản gốc*: thông tin tra khi đã mở đúng hồ
    //  sơ, không phải thứ dùng để quét cả danh sách.
    defaultHidden: true,
    cell: (row) => (
      <span className={row.attachment_count ? 'tabular-nums' : 'text-muted-foreground'}>
        {row.attachment_count}
      </span>
    ),
  },
  {
    key: 'storage_location',
    header: 'Nơi lưu bản gốc',
    width: 200,
    defaultHidden: true,
    cell: (row) =>
      row.storage_location || <span className="text-muted-foreground">Chưa nhập</span>,
  },
]
