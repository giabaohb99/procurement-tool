import type { CardFields } from '../types/view-options'
import { labelFieldId } from '../types/view-options'
import type { WorkLabelField } from '../types/work'

/** Một cột của khung nhìn Danh sách — kể cả cột TÊN, xem {@link TITLE_COLUMN}. */
export interface TaskListColumn {
  key: string
  label: string
  /** Bề rộng mặc định (px), người dùng kéo giãn được và nhớ theo từng dự án. */
  width: number
  /** Chặn dưới riêng khi kéo giãn; bỏ trống thì dùng `MIN_COLUMN_WIDTH` chung. */
  minWidth?: number
  /** Có với cột nhãn tùy biến; trường dựng sẵn thì `undefined`. */
  field?: WorkLabelField
}

/**
 * Cột TÊN CÔNG VIỆC — khai ở đây để nó cũng có bề rộng nhớ được và kéo giãn
 * được như mọi cột khác.
 *
 * Trước đây cột này là `flex-1`: nó nuốt hết phần dư của khung nên không có bề
 * rộng nào để kéo, người dùng rê vào mép phải của nó là không thấy tay cầm đâu.
 * Nay nó rộng cố định, còn phần dư dồn vào một KHOẢNG ĐỆM co giãn nằm ngay sau
 * nó — nhờ vậy các cột dữ liệu vẫn dính mép phải như cũ, mà mép phải của cột tên
 * thì kéo được.
 *
 * Chặn dưới lớn hơn hẳn các cột khác: 90px vừa đủ cho một cái chip, nhưng với
 * tên việc thì cụt còn dăm ba chữ cái, coi như mất cột.
 */
export const TITLE_COLUMN: TaskListColumn = {
  key: 'title',
  label: 'Tên công việc',
  width: 360,
  minWidth: 260,
}

const BUILTIN_WIDTH: Record<string, { label: string; width: number }> = {
  assignees: { label: 'Phụ trách', width: 180 },
  status: { label: 'Trạng thái', width: 140 },
  start: { label: 'Ngày bắt đầu', width: 130 },
  due: { label: 'Hạn chót', width: 130 },
}

/**
 * Dịch bộ «Tùy chỉnh» (§3.6) thành các CỘT của khung nhìn Danh sách.
 *
 * Dùng chung đúng một nguồn với thẻ kanban thay vì khai một danh sách cột thứ
 * hai: tắt một trường ở menu «Tùy chỉnh» thì nó biến mất ở CẢ hai khung nhìn,
 * đúng như Lark. Thứ tự cột cũng chính là thứ tự người dùng kéo trong menu đó.
 *
 * Hai khóa `subtasks` và `comments` KHÔNG thành cột — bên Lark chúng là huy hiệu
 * nhỏ nằm ngay sau tên việc, và tách ra thành cột riêng thì hai cột ấy rỗng ở
 * hầu hết các dòng. Bộ lọc `visible` của chúng vẫn được tôn trọng, chỉ là do
 * `TaskListRow` đọc thẳng chứ không đi qua đây.
 */
export function buildListColumns(
  fields: CardFields,
  labelFields: WorkLabelField[],
): TaskListColumn[] {
  const columns: TaskListColumn[] = []
  for (const f of fields) {
    if (!f.visible) continue

    const builtin = BUILTIN_WIDTH[f.key]
    if (builtin) {
      columns.push({ key: f.key, label: builtin.label, width: builtin.width })
      continue
    }

    const id = labelFieldId(f.key)
    if (id === null) continue // `subtasks` / `comments` — huy hiệu cạnh tên, không phải cột
    const field = labelFields.find((lf) => lf.id === id)
    //  Trường vừa bị xóa ở màn Thiết lập mà bản lưu localStorage còn nhắc tới:
    //  bỏ qua, đừng vẽ một cột không có tiêu đề lẫn dữ liệu.
    if (field) columns.push({ key: f.key, label: field.name, width: 150, field })
  }
  return columns
}

/** Trường dựng sẵn có đang bật không — dùng cho hai huy hiệu cạnh tên việc. */
export function isFieldVisible(fields: CardFields, key: string): boolean {
  return fields.some((f) => f.key === key && f.visible)
}
