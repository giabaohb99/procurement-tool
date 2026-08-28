import { GanttChartSquare, KanbanSquare, Settings2, Table2, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { Button } from '@/shared/ui/button'
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
import { useWorkLabelFields, useWorkTags } from '../hooks/use-work-config'
import type { WorkSection } from '../types/work'
import { WORK_ROLE, WORK_TASK_STATUS } from '../types/work'
import { prepareTasks } from '../utils/filter-tasks'
import { ZOOM_LABELS, type GanttZoom } from '../utils/gantt-scale'
import { WORK_VIEWS, type WorkView } from '../types/view-options'

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
  const { user } = useAuth()
  const myEmployeeId = user?.employee_id ?? 0

  const { data: board, isLoading, isError } = useWorkBoard(listId)
  const { data: tags = [] } = useWorkTags(listId)
  const { data: labelFields = [] } = useWorkLabelFields(listId)
  const createTask = useCreateTask(listId)
  const updateTask = useUpdateTask(listId)
  const moveTask = useMoveTask(listId)

  //  Khung nhìn / lát cắt / sắp xếp / trường trên thẻ được NHỚ theo từng danh
  //  sách (§1). Từ khóa tìm thì không nhớ — mở lại màn mà vẫn còn bộ lọc chữ cũ
  //  thì người dùng tưởng danh sách trống.
  const [viewState, setViewState] = useWorkViewState(listId)
  const { view, scope, sort, fields, ganttZoom } = viewState
  const [keyword, setKeyword] = useState('')

  const [openTaskId, setOpenTaskId] = useState<number | null>(null)
  const [membersOpen, setMembersOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [sectionDialog, setSectionDialog] = useState<SectionDialogMode | null>(null)
  const [editingSection, setEditingSection] = useState<WorkSection | null>(null)

  const myRole = board?.list.my_role ?? null
  const canEdit = myRole !== null && myRole <= WORK_ROLE.MEMBER && !board?.list.is_archived
  const canManage = myRole !== null && myRole <= WORK_ROLE.ADMIN && !board?.list.is_archived

  const tasks = useMemo(
    () => prepareTasks(board?.tasks ?? [], { scope, sort, keyword, myEmployeeId }),
    [board?.tasks, scope, sort, keyword, myEmployeeId],
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

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setMembersOpen(true)}>
            <Users className="size-4" />
            Thành viên
          </Button>
          {canManage && (
            <Button variant="outline" size="sm" onClick={() => setSettingsOpen(true)}>
              <Settings2 className="size-4" />
              Thiết lập
            </Button>
          )}
        </div>
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
        scope={scope}
        onScopeChange={(value) => setViewState({ scope: value })}
        sort={sort}
        onSortChange={(value) => setViewState({ sort: value })}
        keyword={keyword}
        onKeywordChange={setKeyword}
        fields={fields}
        onFieldsChange={(value) => setViewState({ fields: value })}
        canEdit={canEdit}
        onNewTask={() => {
          const firstSection = board.sections[0]
          if (!firstSection) {
            setEditingSection(null)
            setSectionDialog('create')
            return
          }
          createTask.mutate({ list_id: listId, title: 'Việc mới', section_id: firstSection.id })
        }}
      />

      <div className={cn('flex min-h-0 flex-1 flex-col', view === 'kanban' && 'overflow-hidden')}>
        {view === 'kanban' && (
          <KanbanBoard
            sections={board.sections}
            tasks={tasks}
            tags={tags}
            labelFields={labelFields}
            fields={fields}
            canEdit={canEdit}
            canManage={canManage}
            sortLocked={sort !== 'manual'}
            onOpenTask={setOpenTaskId}
            onCreateTask={(sectionId, title) =>
              createTask.mutate({ list_id: listId, title, section_id: sectionId })
            }
            onMoveTask={(taskId, place) => moveTask.mutate({ taskId, place })}
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
            tags={tags}
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
