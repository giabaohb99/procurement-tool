import { useMemo, useRef, useState } from 'react'

import { Skeleton } from '@/shared/ui/skeleton'
import { useCollapsedGroups } from '../hooks/use-collapsed-groups'
import { columnWidthVar, useListColumnWidths } from '../hooks/use-list-column-widths'
import type { CardFields } from '../types/view-options'
import type { WorkLabelField, WorkMember, WorkSection, WorkTask } from '../types/work'
import { groupTasksBySection } from '../utils/group-tasks'
import { TITLE_COLUMN, buildListColumns } from '../utils/list-columns'
import type { KanbanDropPlace } from '../utils/kanban-drop'
import { COLUMN_GAP, LEAD_WIDTH, ROW_PAD_LEFT } from '../utils/list-metrics'
import { ListColumnResizer } from './list-column-resizer'
import type { NewTaskDraft } from './task-draft-row'
import { TaskGroupsBoard } from './task-groups-board'
import type { TaskRowActions } from './task-list-row'

interface TaskListViewProps extends TaskRowActions {
  listId: number
  tasks: WorkTask[]
  sections: WorkSection[]
  labelFields: WorkLabelField[]
  members: WorkMember[]
  fields: CardFields
  canEdit: boolean
  /** Quản trị dự án — chỉ họ mới xếp lại được CỘT (cột là cấu hình của dự án). */
  canManage: boolean
  isLoading?: boolean
  /** Nhân sự đang đăng nhập — dòng nháp gán sẵn làm người phụ trách. */
  defaultPicId?: number
  /**
   * Cho kéo xếp lại không. Trang truyền `sort === 'manual'`: đang sắp theo hạn
   * chót hay độ ưu tiên mà vẫn cho kéo thì thả xong danh sách tự xếp lại chỗ cũ,
   * nhìn hệt như thao tác bị nuốt (§3.4, đúng luật của kanban).
   */
  dragEnabled: boolean
  onMoveTask: (taskId: number, place: KanbanDropPlace) => void
  onMoveSubtask: (parentId: number, subtaskId: number, beforeTaskId: number | null) => void
  onMoveSection: (sectionId: number, beforeSectionId: number | null) => void
  onAddTask: (sectionId: number | null, draft: NewTaskDraft) => void
}

/**
 * Khung nhìn DANH SÁCH (D-02) — bảng gom nhóm theo cột, kiểu Lark.
 *
 * **Cố ý KHÔNG dùng `DataTable` dùng chung** dù luật chung của repo bảo phải
 * dùng: bảng ấy không có gom nhóm, mà thêm vào thì đụng ~35 màn đang chạy nhờ
 * nó; và dáng của nó (kẻ dọc, sọc chan hòa, phân trang, ghim cột) ngược hẳn với
 * dáng Lark mà màn này bám theo — một vạch ngang mảnh, ô sửa được tại chỗ. Đi
 * theo tiền lệ `LinesTable`: bảng thứ hai cho một hình dạng khác hẳn, không
 * phải một bảng tự ghép ở tầng trang.
 *
 * Cột hiện gì và theo thứ tự nào lấy từ chính bộ «Tùy chỉnh» của thẻ kanban
 * (`fields`), nên tắt một trường là nó biến mất ở cả ba khung nhìn. Bề rộng thì
 * kéo giãn được và nhớ riêng theo từng dự án.
 *
 * Màn này giờ chỉ còn lo **hàng tiêu đề + bề rộng cột**; phần nhóm và ba tầng
 * kéo thả nằm ở `TaskGroupsBoard` — dùng chung với lưới trái của Gantt.
 */
export function TaskListView({
  listId,
  tasks,
  sections,
  labelFields,
  members,
  fields,
  canEdit,
  canManage,
  isLoading,
  defaultPicId,
  dragEnabled,
  onMoveTask,
  onMoveSubtask,
  onMoveSection,
  onAddTask,
  ...rowActions
}: TaskListViewProps) {
  const { isCollapsed, toggle } = useCollapsedGroups(listId)
  const gridRef = useRef<HTMLDivElement>(null)
  //  Chỉ bung MỘT việc con một lúc — bung năm bảy cụm rồi cuộn tìm nhau thì
  //  bảng dài ra gấp đôi mà chẳng ai đọc nổi.
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null)

  const groups = useMemo(() => groupTasksBySection(tasks, sections), [tasks, sections])
  const columns = useMemo(() => buildListColumns(fields, labelFields), [fields, labelFields])
  //  Cột TÊN đi cùng các cột dữ liệu trong bộ bề rộng — nó cũng kéo giãn và nhớ
  //  được — nhưng KHÔNG nằm trong `columns`: nó có bố cục riêng (mũi tên bung, ô
  //  tick, huy hiệu) chứ không phải một ô dữ liệu vẽ bằng `TaskListCell`.
  const widthColumns = useMemo(() => [TITLE_COLUMN, ...columns], [columns])
  const { resize, styleVars, totalWidth } = useListColumnWidths(listId, widthColumns)

  /*  Bề rộng tối thiểu TÍNH RA chứ không gõ cứng: hẹp hơn tổng các cột là cột
      nào đó bị bóp lại và chữ trong nó cụt còn dăm ba chữ cái — thà cho cuộn
      ngang. Số cột lẫn bề rộng đều đổi được lúc chạy nên một hằng số không thể
      đúng mãi. Cộng cả lề trái của dòng: nó nằm ngoài mọi cột.  */
  const minWidth = ROW_PAD_LEFT + totalWidth + widthColumns.length * COLUMN_GAP

  if (isLoading) {
    return (
      <div className="space-y-2 p-2">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </div>
    )
  }

  if (!groups.length) {
    return (
      <p className="p-6 text-center text-sm text-muted-foreground">
        Chưa có cột nào. Thêm một cột ở khung nhìn Bảng để bắt đầu.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <div ref={gridRef} style={{ ...styleVars, minWidth }}>
        <div
          role="row"
          /*  Cùng `paddingLeft` với dòng việc (không phải `px-2` như trước):
              có thế mép TRÁI của ô tiêu đề mới trùng mép trái ô tên bên dưới,
              mà hai ô nay rộng bằng nhau nên mép PHẢI — chỗ đặt tay cầm kéo —
              cũng trùng nốt. `py-2.5` cho hàng tiêu đề thở hơn phần thân.  */
          style={{ paddingLeft: ROW_PAD_LEFT, gap: COLUMN_GAP }}
          className="group/head flex items-center border-b bg-muted/30 py-2.5 pr-2 text-xs font-medium text-muted-foreground"
        >
          <span
            className="relative shrink-0"
            style={{
              width: `var(${columnWidthVar(TITLE_COLUMN.key)})`,
              paddingLeft: LEAD_WIDTH,
            }}
          >
            <span className="block truncate">{TITLE_COLUMN.label}</span>
            <ListColumnResizer
              columnKey={TITLE_COLUMN.key}
              gridRef={gridRef}
              minWidth={TITLE_COLUMN.minWidth}
              onResize={(width) => resize(TITLE_COLUMN.key, width)}
            />
          </span>

          {/*  Khoảng đệm nuốt phần dư của khung: các cột dữ liệu vẫn dính mép
               phải như trước, còn cột tên thì có bề rộng thật để mà kéo. */}
          <span className="min-w-0 flex-1" aria-hidden />

          {columns.map((col) => (
            //  KHÔNG đặt `truncate` ở đây: nó kèm `overflow-hidden`, mà tay cầm
            //  kéo giãn nằm ở `-right-1.5` — tức NGOÀI hộp — nên bị cắt mất,
            //  nhìn như bảng không kéo giãn được. Cắt chữ để cho lớp con.
            <span
              key={col.key}
              className="relative shrink-0"
              style={{ width: `var(${columnWidthVar(col.key)})` }}
            >
              <span className="block truncate">{col.label}</span>
              <ListColumnResizer
                columnKey={col.key}
                gridRef={gridRef}
                onResize={(width) => resize(col.key, width)}
              />
            </span>
          ))}
        </div>

        <TaskGroupsBoard
          groups={groups}
          sections={sections}
          columns={columns}
          fields={fields}
          labelFields={labelFields}
          members={members}
          canEdit={canEdit}
          canManage={canManage}
          defaultPicId={defaultPicId}
          dragEnabled={dragEnabled}
          isCollapsed={isCollapsed}
          onToggleCollapse={toggle}
          expandedTaskId={expandedTaskId}
          onToggleExpand={(taskId) =>
            setExpandedTaskId((prev) => (prev === taskId ? null : taskId))
          }
          onMoveTask={onMoveTask}
          onMoveSubtask={onMoveSubtask}
          onMoveSection={onMoveSection}
          onAddTask={onAddTask}
          {...rowActions}
        />
      </div>
    </div>
  )
}
