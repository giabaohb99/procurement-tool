import type { MyDecision, MyTask } from '@/modules/approval/types/approval'

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
 * MỘT DÒNG của hộp duyệt văn bản — gộp chung hai nguồn khác hẳn nhau:
 * việc đang chờ tôi bấm (`MyTask`) và quyết định tôi đã bấm (`MyDecision`).
 *
 * Cố ý **làm phẳng** thay vì để kiểu hợp (`MyTask | MyDecision`): một bảng thì
 * một bộ cột, mà mỗi ô lại phải tự đoán mình đang cầm loại nào rồi rẽ nhánh là
 * chỗ dễ sai nhất. Phẳng thì ô chỉ đọc đúng một trường; trường nào loại kia
 * không có thì rỗng, và cột tự vẽ dấu "—".
 */
export interface InboxRow {
  /** `pending-<id>` / `done-<id>` — id của hai bảng gốc trùng số nhau được. */
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
export function buildInboxRows(tasks: MyTask[], decisions: MyDecision[]): InboxRow[] {
  const cho: InboxRow[] = tasks.map((row) => ({
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

  const xong: InboxRow[] = decisions.map((row) => ({
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

  return [...cho, ...xong]
}
