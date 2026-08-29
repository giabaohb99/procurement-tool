import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/utils/cn'
import type { WorkLabelField, WorkSection, WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { dueTone, dueToneClass, formatDueLabel } from '../utils/due-date'
import { chipClass } from '../utils/work-colors'

interface TaskListViewProps {
  tasks: WorkTask[]
  sections: WorkSection[]
  labelFields: WorkLabelField[]
  canEdit: boolean
  isLoading?: boolean
  onOpenTask: (taskId: number) => void
  onToggleDone: (taskId: number, done: boolean) => void
}

/**
 * Khung nhìn DANH SÁCH (D-02) — bảng phẳng trên `DataTable` dùng chung.
 *
 * Ô tick tròn ở cột đầu đổi trạng thái ngay tại chỗ như Lark; bấm vào dòng thì
 * mở panel chi tiết. Việc con KHÔNG thành dòng riêng (C-05) — dữ liệu đưa vào
 * đây vốn đã chỉ có task cha.
 */
export function TaskListView({
  tasks,
  sections,
  labelFields,
  canEdit,
  isLoading,
  onOpenTask,
  onToggleDone,
}: TaskListViewProps) {
  const columns: DataTableColumn<WorkTask>[] = [
    {
      key: 'done',
      header: '',
      width: 44,
      align: 'center',
      hideable: false,
      cell: (row) => (
        <Checkbox
          checked={row.status === WORK_TASK_STATUS.DONE}
          disabled={!canEdit}
          //  Chặn nổi bọt: bấm ô tick mà mở luôn panel chi tiết thì mỗi lần
          //  đánh dấu xong lại phải đóng một panel.
          onClick={(e) => e.stopPropagation()}
          onCheckedChange={(checked) => onToggleDone(row.id, checked === true)}
        />
      ),
    },
    {
      key: 'title',
      header: 'Tên công việc',
      //  Có bề rộng hẳn hoi: các cột sau đều khai `width`, để cột này co giãn
      //  thì nó bị ép còn một mẩu và tiêu đề việc cắt cụt ngay từ chữ thứ tư.
      width: 360,
      hideable: false,
      cell: (row) => (
        <span className={cn(row.status === WORK_TASK_STATUS.DONE && 'text-muted-foreground line-through')}>
          {row.title}
        </span>
      ),
    },
    {
      key: 'section',
      header: 'Cột',
      width: 130,
      cell: (row) => sections.find((s) => s.id === row.section_id)?.name ?? '',
    },
    {
      key: 'assignees',
      header: 'Người phụ trách',
      width: 200,
      cell: (row) =>
        row.assignees
          .filter((a) => a.kind === 1)
          .map((a) => a.employee_name || `#${a.employee_id}`)
          .join(', '),
    },
    {
      key: 'due',
      header: 'Hạn chót',
      width: 110,
      cell: (row) => {
        if (!row.due_date) return ''
        const tone = dueTone(row.due_date, row.status === WORK_TASK_STATUS.DONE)
        return <span className={dueToneClass(tone)}>{formatDueLabel(row.due_date)}</span>
      },
    },
    {
      key: 'labels',
      header: 'Nhãn',
      width: 160,
      defaultHidden: true,
      cell: (row) => (
        <div className="flex flex-wrap gap-1">
          {row.labels.map((l) => {
            const option = labelFields
              .find((f) => f.id === l.field_id)
              ?.options.find((o) => o.id === l.option_id)
            if (!option) return null
            return (
              <span
                key={`${l.field_id}-${l.option_id}`}
                className={cn('rounded px-1.5 py-0.5 text-xs', chipClass(option.color))}
              >
                {option.name}
              </span>
            )
          })}
        </div>
      ),
    },
    {
      key: 'subtasks',
      header: 'Việc con',
      width: 90,
      align: 'center',
      cell: (row) => (row.subtask_total ? `${row.subtask_done}/${row.subtask_total}` : ''),
    },
  ]

  return (
    <DataTable
      columns={columns}
      rows={tasks}
      getRowId={(row) => row.id}
      isLoading={isLoading}
      emptyMessage="Không có công việc nào khớp bộ lọc đang chọn"
      onRowClick={(row) => onOpenTask(row.id)}
      storageKey="work-task-list"
    />
  )
}
