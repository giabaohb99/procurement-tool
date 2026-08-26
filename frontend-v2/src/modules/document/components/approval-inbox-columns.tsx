import { ACTION_TONE } from '@/modules/approval/helpers/decision-tone'
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { InboxRow } from './approval-inbox-row'

/**
 * Ô rỗng của loại dòng không có trường đó — vẽ "—" chứ không để trắng.
 *
 * Là một PHẦN TỬ hằng, không phải component: nội dung không đổi theo dòng nào
 * cả, mà khai thành component trong tệp chỉ xuất dữ liệu thì hỏng luôn hot
 * reload của Vite (`react-refresh/only-export-components`).
 */
const EMPTY = <span className="text-muted-foreground">—</span>

/**
 * CỘT của hộp duyệt văn bản (bảng gộp chờ-duyệt + đã-duyệt).
 *
 * Hằng số ở tầng module, không dựng lại mỗi lần render: bộ cột này không phụ
 * thuộc state nào, gói vào `useMemo` chỉ tốn thêm một mảng phụ thuộc để quên.
 *
 * Cột CUỐI là huy hiệu phân biệt hai loại dòng. Để cuối vì mắt đọc bảng đi từ
 * số hiệu và tên văn bản — cái người ta tìm — còn tình trạng là thứ xác nhận
 * lại sau khi đã tìm thấy dòng. Cùng với số hiệu, đây là cột không ẩn được:
 * bảng gộp mà giấu mất chỗ nói dòng này *chờ* hay *đã xong* thì người đọc không
 * còn cách nào biết.
 */
export const approvalInboxColumns: DataTableColumn<InboxRow>[] = [
  {
    key: 'code',
    header: 'Số hiệu',
    width: 170,
    hideable: false,
    cell: (row) => (
      <span className="truncate font-medium text-navy">
        {/* Chưa duyệt thì thường chưa có số — nói rõ chứ đừng để ô trống. */}
        {row.code || <span className="text-muted-foreground">Chưa cấp số</span>}
      </span>
    ),
  },
  {
    key: 'title',
    header: 'Tên văn bản',
    width: 340,
    //  Bảng chạy `table-fixed` nên ô không tự nong ra — chữ dài phải tự cắt.
    cell: (row) => <span className="truncate">{row.title}</span>,
  },
  {
    key: 'nodeName',
    header: 'Bước',
    width: 200,
    cell: (row) => <span className="truncate">{row.nodeName}</span>,
  },
  {
    key: 'startedByName',
    header: 'Người trình',
    width: 160,
    cell: (row) => row.startedByName || EMPTY,
  },
  {
    key: 'dueAt',
    header: 'Hạn duyệt',
    width: 150,
    cell: (row) =>
      row.dueAt ? (
        <span className={row.isOverdue ? 'font-medium text-destructive' : undefined}>
          {formatDate(row.dueAt)}
        </span>
      ) : (
        EMPTY
      ),
  },
  {
    key: 'decidedAt',
    header: 'Tôi bấm lúc',
    width: 150,
    cell: (row) =>
      row.decidedAt ? (
        <span className="tabular-nums">{formatDateTime(row.decidedAt)}</span>
      ) : (
        EMPTY
      ),
  },
  {
    key: 'instanceStatusLabel',
    header: 'Phiếu bây giờ',
    width: 150,
    //  "Tôi đã ký bước của mình" khác "phiếu đã xong" — hai chuyện dễ đọc nhầm
    //  nên để riêng một cột, chỉ có nghĩa với dòng đã bấm.
    cell: (row) =>
      row.instanceStatusLabel ? (
        <span className="truncate text-muted-foreground">{row.instanceStatusLabel}</span>
      ) : (
        EMPTY
      ),
  },
  {
    key: 'comment',
    header: 'Ý kiến',
    width: 280,
    defaultHidden: true,
    cell: (row) => <span className="truncate">{row.comment || EMPTY}</span>,
  },
  {
    key: 'onBehalfOfName',
    header: 'Bấm thay',
    width: 160,
    defaultHidden: true,
    //  Ký thay người khác là việc khác hẳn ký cho mình, và nhật ký ghi cả hai tên.
    cell: (row) => row.onBehalfOfName || EMPTY,
  },
  {
    key: 'kind',
    header: 'Tình trạng',
    width: 130,
    hideable: false,
    //  GHIM bên phải: bảng này rộng hơn màn hình khi bật hết cột, mà cuộn ngang
    //  một cái là mất luôn chỗ nói dòng đang chờ hay đã xong — thứ duy nhất
    //  phân biệt hai nửa của bảng gộp. Ghim thì nó luôn nằm ở mép phải.
    stickyRight: true,
    cell: (row) =>
      row.kind === 'pending' ? (
        //  Quá hạn tô đỏ ngay ở huy hiệu: cột «Hạn duyệt» ẩn được, còn cột này
        //  thì không — mức gấp gáp không được biến mất theo một cú ẩn cột.
        <Badge variant={row.isOverdue ? 'destructive' : 'default'}>
          {row.isOverdue ? 'Quá hạn' : 'Cần duyệt'}
        </Badge>
      ) : (
        <Badge variant={ACTION_TONE[row.action ?? 0] ?? 'outline'}>{row.actionLabel}</Badge>
      ),
  },
]
