import { GanttChartSquare, KanbanSquare, Settings2, Table2, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'

import { FilterProvider, useFilterContext } from '@/shared/conditional-filter'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { buildTaskFilterFields } from '../config/task-filter-fields'
import { GanttView } from '../components/gantt-view'
import { ListConfigDialog } from '../components/list-config-dialog'
import { ListMembersDialog } from '../components/list-members-dialog'
import { KanbanBoard } from '../components/kanban-board'
import { SectionEditDialog, type SectionDialogMode } from '../components/section-edit-dialog'
import { TaskDetailSheet } from '../components/task-detail-sheet'
import { TaskListView } from '../components/task-list-view'
import { WorkToolbar } from '../components/work-toolbar'
import { useCreateTask, useMoveTask, useUpdateTask, useWorkBoard } from '../hooks/use-work-board'
import { useWorkViewState } from '../hooks/use-view-state'
import { useMoveSection, useWorkLabelFields } from '../hooks/use-work-config'
import type { WorkSection } from '../types/work'
import { fieldHasOptions, WORK_ROLE, WORK_TASK_STATUS } from '../types/work'
import { prepareTasks } from '../utils/filter-tasks'
import { buildOptionRank, findPriorityField } from '../utils/priority-field'
import { applyTaskConditions } from '../utils/task-conditions'
import { ZOOM_LABELS, type GanttZoom } from '../utils/gantt-scale'
import {
  mergeCardFields,
  WORK_SORTS,
  WORK_VIEWS,
  type WorkSort,
  type WorkView,
} from '../types/view-options'

/** Icon của từng khung nhìn — để `WORK_VIEWS` giữ được nhãn thuần dữ liệu. */
const VIEW_ICONS = {
  kanban: KanbanSquare,
  list: Table2,
  gantt: GanttChartSquare,
} as const

/**
 * Màn chính của một danh sách công việc: đầu trang → tab khung nhìn → thanh
 * công cụ → một trong ba khung nhìn (bố cục §1 của `05-giao-dien.md`).
 *
 * Ba khung nhìn đúng như Lark: **Bảng (Kanban) · Danh sách · Gantt**. Lát cắt /
 * sắp xếp / trường hiện trên thẻ / mức phóng Gantt đều là trạng thái HIỂN THỊ,
 * nhớ theo từng danh sách ở `localStorage`.
 *
 * Tab **Dashboard** và **Activities** (D-06, D-09 — P1) cố ý CHƯA render: §2 cấm
 * để tab chết trên thanh.
 */
export function WorkListPage() {
  const params = useParams()
  const listId = Number(params.listId ?? 0)

  //  Trường tùy biến của dự án cũng là trường LỌC được (độ ưu tiên nay nằm
  //  trong số đó), nên phải nạp trước khi dựng cấu hình bộ lọc.
  const { data: labelFields = [] } = useWorkLabelFields(listId)

  //  `key` theo list: điều kiện đang lọc của dự án này (cột nào, nhãn nào) vô
  //  nghĩa ở dự án khác, mang sang là bảng trống mà không rõ vì sao.
  const config = useMemo(
    () => ({ fields: buildTaskFilterFields(listId, labelFields) }),
    [listId, labelFields],
  )

  return (
    <FilterProvider key={listId} config={config}>
      <WorkListContent listId={listId} />
    </FilterProvider>
  )
}

function WorkListContent({ listId }: { listId: number }) {
  const { appliedState } = useFilterContext()
  const { data: board, isLoading, isError } = useWorkBoard(listId)
  const { data: labelFields = [] } = useWorkLabelFields(listId)
  const createTask = useCreateTask(listId)
  const updateTask = useUpdateTask(listId)
  const moveTask = useMoveTask(listId)
  const moveSection = useMoveSection(listId)

  //  Khung nhìn / lát cắt / sắp xếp / trường trên thẻ được NHỚ theo từng danh
  //  sách (§1). Từ khóa tìm thì không nhớ — mở lại màn mà vẫn còn bộ lọc chữ cũ
  //  thì người dùng tưởng danh sách trống.
  const [viewState, setViewState] = useWorkViewState(listId)
  const { view, sort, fields, ganttZoom } = viewState
  const [keyword, setKeyword] = useState('')

  const [openTaskId, setOpenTaskId] = useState<number | null>(null)
  const [membersOpen, setMembersOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [sectionDialog, setSectionDialog] = useState<SectionDialogMode | null>(null)
  const [editingSection, setEditingSection] = useState<WorkSection | null>(null)

  const myRole = board?.list.my_role ?? null
  const canEdit = myRole !== null && myRole <= WORK_ROLE.MEMBER && !board?.list.is_archived
  const canManage = myRole !== null && myRole <= WORK_ROLE.ADMIN && !board?.list.is_archived

  //  Bộ nhãn tùy biến là của TỪNG dự án nên danh sách trường trên thẻ không cố
  //  định được: trộn thứ tự đã nhớ với bộ nhãn đang có (thêm nhãn mới, bỏ nhãn
  //  đã xóa) — xem `mergeCardFields`.
  const cardFields = useMemo(
    () => mergeCardFields(fields, labelFields.map((f) => f.id)),
    [fields, labelFields],
  )

  //  Sắp theo một TRƯỜNG TÙY BIẾN cần hạng của từng giá trị (xem `byLabel`).
  const optionRank = useMemo(() => buildOptionRank(labelFields), [labelFields])

  //  Bộ tiêu chí sắp xếp = tiêu chí dựng sẵn + MỖI TRƯỜNG TÙY BIẾN một dòng,
  //  đúng khuôn Lark. Độ ưu tiên xuất hiện ở đây với tư cách một trường như thế.
  const sortOptions = useMemo(
    () => [
      ...WORK_SORTS.map((s) => ({ value: s.value as WorkSort, label: s.label })),
      ...labelFields
        .filter((f) => fieldHasOptions(f.field_type))
        .map((f) => ({ value: `label:${f.id}` as WorkSort, label: f.name })),
    ],
    [labelFields],
  )

  const priorityField = useMemo(() => findPriorityField(labelFields), [labelFields])

  //  Ba lớp, đúng thứ tự: từ khóa → sắp xếp (`prepareTasks`) → BỘ LỌC ĐIỀU KIỆN
  //  của nút «Lọc».
  const tasks = useMemo(
    () =>
      applyTaskConditions(
        prepareTasks(board?.tasks ?? [], { sort, keyword, optionRank }),
        appliedState,
      ),
    [board?.tasks, sort, keyword, optionRank, appliedState],
  )

  if (isError) {
    return (
      <ErrorState
        title="Không mở được danh sách"
        description="Có thể bạn không còn là thành viên của danh sách này."
      />
    )
  }

  if (isLoading || !board) {
    return (
      <div className="space-y-3 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 p-4 lg:p-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-semibold tracking-tight text-navy">
            {board.list.name}
            {board.list.is_archived === 1 && (
              <span className="rounded bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">
                Đã lưu trữ
              </span>
            )}
          </h1>
          {board.list.description && (
            <p className="mt-1 text-sm text-muted-foreground">{board.list.description}</p>
          )}
        </div>

        {/*  MỘT nút cho cả thành viên lẫn thiết lập: hai việc này đều là "sửa
            chính dự án", mở ra rất thưa, mà chiếm mất góc phải của mọi màn.
            Người chỉ có quyền xem vẫn vào được — xem ai đang ở trong dự án
            không phải quyền quản trị (A-02), nên menu luôn có ít nhất một mục. */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <Settings2 className="size-4" />
              Quản lý dự án
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setMembersOpen(true)}>
              <Users className="size-4" />
              Thành viên
            </DropdownMenuItem>
            {canManage && (
              <DropdownMenuItem onClick={() => setSettingsOpen(true)}>
                <Settings2 className="size-4" />
                Thiết lập
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <Tabs value={view} onValueChange={(v) => setViewState({ view: v as WorkView })}>
          <TabsList>
            {WORK_VIEWS.map((v) => {
              const Icon = VIEW_ICONS[v.value]
              return (
                <TabsTrigger key={v.value} value={v.value}>
                  <Icon className="size-4" />
                  {v.label}
                </TabsTrigger>
              )
            })}
          </TabsList>
        </Tabs>

        {/*  Mức phóng chỉ có nghĩa với Gantt — hiện ở hai khung kia là một ô
            chọn không làm gì, người dùng bấm rồi tự hỏi tại sao không đổi. */}
        {view === 'gantt' && (
          <Select
            value={ganttZoom}
            onValueChange={(v) => setViewState({ ganttZoom: v as GanttZoom })}
          >
            <SelectTrigger size="sm" className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(ZOOM_LABELS) as GanttZoom[]).map((z) => (
                <SelectItem key={z} value={z}>
                  {ZOOM_LABELS[z]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      <WorkToolbar
        listId={listId}
        sort={sort}
        sortOptions={sortOptions}
        onSortChange={(value) => setViewState({ sort: value })}
        keyword={keyword}
        onKeywordChange={setKeyword}
        fields={cardFields}
        onFieldsChange={(value) => setViewState({ fields: value })}
        labelFields={labelFields}
        onAddField={canManage ? () => setSettingsOpen(true) : undefined}
        canEdit={canEdit}
        canManage={canManage}
        onNewTask={() => {
          const firstSection = board.sections[0]
          if (!firstSection) {
            setEditingSection(null)
            setSectionDialog('create')
            return
          }
          createTask.mutate({ list_id: listId, title: 'Việc mới', section_id: firstSection.id })
        }}
        onAddSection={
          canManage
            ? () => {
                setEditingSection(null)
                setSectionDialog('create')
              }
            : undefined
        }
      />

      <div className={cn('flex min-h-0 flex-1 flex-col', view === 'kanban' && 'overflow-hidden')}>
        {view === 'kanban' && (
          <KanbanBoard
            sections={board.sections}
            tasks={tasks}
            labelFields={labelFields}
            fields={cardFields}
            canEdit={canEdit}
            canManage={canManage}
            sortLocked={sort !== 'manual'}
            onOpenTask={setOpenTaskId}
            onCreateTask={(sectionId, title) =>
              createTask.mutate({ list_id: listId, title, section_id: sectionId })
            }
            onMoveTask={(taskId, place) => moveTask.mutate({ taskId, place })}
            onMoveSection={(sectionId, beforeSectionId) =>
              moveSection.mutate({ sectionId, beforeSectionId })
            }
            onAddSection={() => {
              setEditingSection(null)
              setSectionDialog('create')
            }}
            onRenameSection={(section) => {
              setEditingSection(section)
              setSectionDialog('edit')
            }}
            onDeleteSection={(section) => {
              setEditingSection(section)
              setSectionDialog('delete')
            }}
          />
        )}

        {view === 'list' && (
          <TaskListView
            tasks={tasks}
            sections={board.sections}
            labelFields={labelFields}
            canEdit={canEdit}
            onOpenTask={setOpenTaskId}
            onToggleDone={(taskId, done) =>
              updateTask.mutate({
                id: taskId,
                values: { status: done ? WORK_TASK_STATUS.DONE : WORK_TASK_STATUS.OPEN },
              })
            }
          />
        )}

        {view === 'gantt' && (
          <GanttView
            tasks={tasks}
            priorityField={priorityField}
            zoom={ganttZoom}
            canEdit={canEdit}
            onOpenTask={setOpenTaskId}
            onMoveDates={(taskId, values) => updateTask.mutate({ id: taskId, values })}
          />
        )}
      </div>

      <TaskDetailSheet
        taskId={openTaskId}
        listId={listId}
        sections={board.sections}
        canEdit={canEdit}
        onClose={() => setOpenTaskId(null)}
      />

      <ListMembersDialog
        open={membersOpen}
        listId={listId}
        myRole={myRole}
        onClose={() => setMembersOpen(false)}
      />

      <ListConfigDialog
        open={settingsOpen}
        listId={listId}
        onClose={() => setSettingsOpen(false)}
      />

      <SectionEditDialog
        mode={sectionDialog}
        listId={listId}
        section={editingSection}
        sections={board.sections}
        onClose={() => setSectionDialog(null)}
      />
    </div>
  )
}
