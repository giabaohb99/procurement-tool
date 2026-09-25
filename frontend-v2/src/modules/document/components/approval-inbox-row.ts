import type { MyDecision, MyTask } from '@/modules/approval/types/approval'
import type { LegacyDecision, LegacyPendingDocument } from '../types/legacy-pending-approval'

/**
 * Bốn tập con của hộp duyệt — `overdue` là tập con của `pending`.
 *
 * Khai ở tệp dữ liệu chứ không ở tệp dãy nút (`inbox-scope-filter.tsx`): tệp có
 * component mà xuất kèm hằng số thì hỏng hot reload của Vite
 * (`react-refresh/only-export-components`).
 */
export const INBOX_SCOPE = {
  all: 'all',
  pending: 'pending',
  overdue: 'overdue',
  done: 'done',
} as const

export type InboxScope = (typeof INBOX_SCOPE)[keyof typeof INBOX_SCOPE]

/**
 * Câu cho bảng RỖNG — nói theo TAB đang đứng, chỉ nhắc «điều kiện đang lọc»
 * khi người dùng thật sự đang gõ tìm / đặt bộ lọc.
 *
 * Từ 25/09/2026 màn mở sẵn ở «Cần duyệt». Câu cũ chỉ phân biệt «có dòng nào
 * không», nên tab mặc định trống mà còn việc đã duyệt thì màn báo «không khớp
 * điều kiện đang lọc» — người dùng chưa lọc gì, đọc ra như lọc nhầm; trong khi
 * đó là tin tốt: hết việc.
 */
export function describeInboxEmpty(scope: string, isFiltering: boolean): string {
  if (isFiltering) return 'Không có văn bản nào khớp điều kiện đang lọc.'
  if (scope === INBOX_SCOPE.overdue) return 'Không có văn bản nào quá hạn duyệt.'
  if (scope === INBOX_SCOPE.done) return 'Bạn chưa duyệt văn bản nào trong khoảng thời gian này.'
  return 'Không có văn bản nào đang chờ bạn duyệt.'
}

/**
 * MỘT DÒNG của hộp duyệt văn bản — gộp chung hai nguồn khác hẳn nhau:
 * việc đang chờ tôi bấm (`MyTask`) và quyết định tôi đã bấm (`MyDecision`).
 *
 * Cố ý **làm phẳng** thay vì để kiểu hợp (`MyTask | MyDecision`): một bảng thì
 * một bộ cột, mà mỗi ô lại phải tự đoán mình đang cầm loại nào rồi rẽ nhánh là
 * chỗ dễ sai nhất. Phẳng thì ô chỉ đọc đúng một trường; trường nào loại kia
 * không có thì rỗng, và cột tự vẽ dấu "—".
 */
export interface InboxRow {
  /** `pending-<id>` / `done-<id>` / `legacy-<id văn bản>` — id của các bảng gốc trùng số nhau được. */
  id: string
  kind: 'pending' | 'done'
  entityId: number
  code: string
  title: string
  nodeName: string
  /** Chỉ dòng đang chờ mới có — dấu vết không ghi ai trình. */
  startedByName: string
  dueAt: string | null
  isOverdue: boolean
  decidedAt: string | null
  /** Mã việc đã bấm (duyệt / trả lại / từ chối) — dùng để chọn màu huy hiệu. */
  action: number | null
  actionLabel: string
  instanceStatusLabel: string
  comment: string
  onBehalfOfName: string
}

/**
 * Xếp việc CHƯA LÀM lên trên, việc ĐÃ LÀM xuống dưới — trong cùng một bảng.
 *
 * Thứ tự trong từng nhóm giữ nguyên như backend trả (việc chờ theo hạn, quyết
 * định theo thời điểm bấm giảm dần), không sắp lại ở đây.
 *
 * Một văn bản có thể ra HAI dòng: tôi đã ký bước 1 và nay lại tới lượt tôi ở
 * bước 4. Đó là hai việc thật, không gộp — id khác nhau nên bảng vẫn đúng.
 */
export function buildInboxRows(
  tasks: MyTask[],
  decisions: MyDecision[],
  legacy: LegacyPendingDocument[] = [],
  legacyDone: LegacyDecision[] = [],
): InboxRow[] {
  const pendingRows: InboxRow[] = tasks.map((row) => ({
    id: `pending-${row.id}`,
    kind: 'pending',
    entityId: row.entity_id,
    code: row.entity_code,
    title: row.entity_title,
    nodeName: row.node_name || `Bước ${row.node_seq}`,
    startedByName: row.started_by_name,
    dueAt: row.due_at,
    isOverdue: row.is_overdue,
    decidedAt: null,
    action: null,
    actionLabel: '',
    instanceStatusLabel: '',
    comment: '',
    onBehalfOfName: row.on_behalf_of_name,
  }))

  const doneRows: InboxRow[] = decisions.map((row) => ({
    id: `done-${row.id}`,
    kind: 'done',
    entityId: row.entity_id,
    code: row.entity_code,
    title: row.entity_title,
    nodeName: row.node_name || `Bước ${row.node_seq}`,
    startedByName: '',
    dueAt: null,
    isOverdue: false,
    decidedAt: row.decided_at,
    action: row.action,
    actionLabel: row.action_label,
    instanceStatusLabel: row.instance_status_label,
    comment: row.comment,
    onBehalfOfName: row.on_behalf_of_name,
  }))

  //  DUYỆT MỘT BƯỚC (25/09/2026) — văn bản không khớp luồng nào nên không có
  //  việc trong bộ máy duyệt; vẫn là việc CHỜ TÔI, nên xếp chung nhóm chờ. Không
  //  có hạn, không có bước — ô bước ghi thẳng tên đường duyệt cho người đọc hiểu
  //  vì sao dòng này không có hạn xử lý.
  const legacyRows: InboxRow[] = legacy.map((row) => ({
    id: `legacy-${row.document_id}`,
    kind: 'pending',
    entityId: row.document_id,
    code: row.code,
    title: row.title,
    nodeName: 'Duyệt một bước',
    startedByName: row.submitted_by_name,
    dueAt: null,
    isOverdue: false,
    decidedAt: null,
    action: null,
    actionLabel: '',
    instanceStatusLabel: '',
    comment: '',
    onBehalfOfName: '',
  }))

  //  ĐÃ DUYỆT theo đường một bước — đọc từ nhật ký văn bản. Xếp CHUNG nhóm đã
  //  làm rồi sắp lại theo thời điểm bấm, không để thành một cụm riêng cuối bảng:
  //  người dùng đọc «tuần này tôi ký gì» theo thời gian, không theo đường duyệt.
  const legacyDoneRows: InboxRow[] = legacyDone.map((row) => ({
    id: `legacy-done-${row.id}`,
    kind: 'done',
    entityId: row.document_id,
    code: row.code,
    title: row.title,
    nodeName: 'Duyệt một bước',
    startedByName: '',
    dueAt: null,
    isOverdue: false,
    decidedAt: row.decided_at,
    action: row.action,
    actionLabel: row.action_label,
    instanceStatusLabel: row.status_label,
    comment: row.comment,
    onBehalfOfName: '',
  }))
  const allDone = [...doneRows, ...legacyDoneRows].sort((a, b) =>
    (b.decidedAt ?? '').localeCompare(a.decidedAt ?? ''),
  )

  return [...pendingRows, ...legacyRows, ...allDone]
}
