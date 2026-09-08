import { GanttChartSquare, History, KanbanSquare, Settings2, Table2, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { logger } from '@/core/telemetry/logger'
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
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { buildTaskFilterFields } from '../config/task-filter-fields'
import { ActivityFeed } from '../components/activity-feed'
import { GanttView } from '../components/gantt-view'
import { ListConfigDialog } from '../components/list-config-dialog'
import { ListManageDialog } from '../components/list-manage-dialog'
import { KanbanBoard } from '../components/kanban-board'
import { ProjectHeaderInlineEdit } from '../components/project-header-inline-edit'
import { SectionEditDialog, type SectionDialogMode } from '../components/section-edit-dialog'
import { TaskDetailSheet } from '../components/task-detail-sheet'
import type { NewTaskDraft } from '../components/task-draft-row'
import { TaskListView } from '../components/task-list-view'
import { WorkSidebarPeekButton } from '../components/work-sidebar-peek-button'
import { WorkToolbar } from '../components/work-toolbar'
import {
  useCreateTask,
  useMoveSubtask,
  useMoveTask,
  useSetAssignees,
  useSetTaskLabel,
  useToggleSubtask,
  useUpdateTask,
  useWorkBoard,
} from '../hooks/use-work-board'
import { useCreateTaskLink, useDeleteTaskLink, useUpdateTaskLink } from '../hooks/use-task-links'
import { useWorkViewState } from '../hooks/use-view-state'
import { useMoveSection, useWorkLabelFields, useWorkMembers } from '../hooks/use-work-config'
import { useUpdateWorkList } from '../hooks/use-work-lists'
import type { WorkSection } from '../types/work'
import { fieldHasOptions, WORK_ROLE, WORK_TASK_KIND, WORK_TASK_STATUS } from '../types/work'
import { today } from '../utils/due-date'
import { prepareTasks } from '../utils/filter-tasks'
import { buildOptionRank, findPriorityField } from '../utils/priority-field'
import { applyTaskConditions } from '../utils/task-conditions'
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
  activities: History,
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
  //  Sửa TÊN / MÔ TẢ ngay trên tiêu đề. Cùng hook với thẻ Thông tin trong hộp
  //  Quản lý dự án — hai lối vào, một đường ghi.
  const updateList = useUpdateWorkList()
  const moveTask = useMoveTask(listId)
  const moveSection = useMoveSection(listId)
  //  Nguồn cho ô «Phụ trách» và trường tùy biến kiểu NGƯỜI sửa ngay trên dòng
  //  danh sách — panel chi tiết cũng nạp đúng query này nên không tốn thêm lượt.
  const { data: members = [] } = useWorkMembers(listId)
  const setAssignees = useSetAssignees(listId)
  const setLabel = useSetTaskLabel(listId)
  const toggleSubtask = useToggleSubtask(listId)
  const moveSubtask = useMoveSubtask(listId)
  //  Mũi tên phụ thuộc của Gantt (B-15) — dữ liệu nằm sẵn trong payload bảng
  //  nên chỉ cần hai mutation, không có hook đọc riêng.
  const createLink = useCreateTaskLink(listId)
  const updateLink = useUpdateTaskLink(listId)
  const deleteLink = useDeleteTaskLink(listId)

  /*  Việc tự thêm gần như luôn là việc của chính mình, nên dòng nháp gán sẵn
      người đang đăng nhập. Chỉ gán khi họ THỰC SỰ là thành viên dự án: gán một
      người ngoài thì họ không mở nổi việc để biết mình bị gán (`membership_service`
      chặn), mà máy chủ nhận rồi nên nhìn như đã giao xong.  */
  const { user } = useAuth()
  const defaultPicId = useMemo(() => {
    const employeeId = user?.employee_id
    if (!employeeId) return undefined
    return members.some((m) => m.employee_id === employeeId) ? employeeId : undefined
  }, [user?.employee_id, members])

  /**
   * Tạo việc từ DÒNG NHÁP của khung nhìn Danh sách — gán sẵn người/hạn/nhãn.
   *
   * Phải đi hai nhịp vì API tạo task không nhận nhãn tùy biến: nhịp một tạo
   * task (tên · cột · hạn · người phụ trách), nhịp hai mới gắn được nhãn vì
   * chúng cần `task_id`. Chỉ gửi nhãn NÀO người dùng thực sự đụng tới — lặp cả
   * bộ trường thì mỗi việc mới đẻ ra một tràng lượt gọi ghi giá trị rỗng.
   */
  async function addTaskFromDraft(sectionId: number | null, draft: NewTaskDraft) {
    //  Dòng nháp gọi hàm này mà KHÔNG await (nó ở lại để gõ việc kế), nên lỗi
    //  phải nuốt ngay tại đây — để lọt ra ngoài là một unhandled rejection đỏ
    //  console mà người dùng chẳng thấy gì. Toast lỗi do tầng `@/core/api` lo.
    try {
      const created = await createTask.mutateAsync({
        list_id: listId,
        title: draft.title,
        section_id: sectionId,
        start_date: draft.startDate || undefined,
        due_date: draft.dueDate || undefined,
        assignee_ids: draft.picIds.length ? draft.picIds : undefined,
      })
      for (const [fieldId, value] of Object.entries(draft.labels)) {
        if (value === null || value === undefined || value === '') continue
        setLabel.mutate({ taskId: created.id, fieldId: Number(fieldId), value })
      }
    } catch (error) {
      logger.warn('Không tạo được công việc từ dòng nháp', error)
    }
  }

  //  Khung nhìn / lát cắt / sắp xếp / trường trên thẻ được NHỚ theo từng danh
  //  sách (§1). Từ khóa tìm thì không nhớ — mở lại màn mà vẫn còn bộ lọc chữ cũ
  //  thì người dùng tưởng danh sách trống.
  const [viewState, setViewState] = useWorkViewState(listId)
  const { view, sort, fields, ganttZoom } = viewState
  const [keyword, setKeyword] = useState('')

  /*  Việc đang mở panel. Nhận mồi từ `?task=` để link CHUÔNG mở thẳng được một
      việc: chuông trỏ tới `/project/tasks/{id}`, trang đó tra dự án rồi dẫn về
      đây kèm tham số này (xem `TaskRedirectPage`).

      Đóng panel thì XÓA tham số khỏi URL, không thì bấm Đóng xong nó mở lại
      ngay ở nhịp render kế — và người dùng tưởng nút Đóng hỏng.  */
  const [searchParams, setSearchParams] = useSearchParams()
  const taskFromUrl = Number(searchParams.get('task') ?? 0) || null
  const [openTaskId, setOpenTaskId] = useState<number | null>(taskFromUrl)

  function closeTaskPanel() {
    setOpenTaskId(null)
    if (searchParams.has('task')) {
      const next = new URLSearchParams(searchParams)
      next.delete('task')
      setSearchParams(next, { replace: true })
    }
  }
  const [manageOpen, setManageOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [sectionDialog, setSectionDialog] = useState<SectionDialogMode | null>(null)
  const [editingSection, setEditingSection] = useState<WorkSection | null>(null)

  const myRole = board?.list.my_role ?? null
  const canEdit = myRole !== null && myRole <= WORK_ROLE.MEMBER && !board?.list.is_archived
  const canManage = myRole !== null && myRole <= WORK_ROLE.ADMIN && !board?.list.is_archived
  //  Đổi tên / mô tả / màu / lưu trữ dự án: backend gác `update_list` bằng
  //  `CAN_OWN`, KHÔNG phải `CAN_MANAGE`. Mở ô nhập cho Quản trị là họ gõ xong
  //  bấm Lưu rồi ăn 403.
  const canOwn = myRole === WORK_ROLE.OWNER && !board?.list.is_archived

  //  Bộ nhãn tùy biến là của TỪNG dự án nên danh sách trường trên thẻ không cố
  //  định được: trộn thứ tự đã nhớ với bộ nhãn đang có (thêm nhãn mới, bỏ nhãn
  //  đã xóa) — xem `mergeCardFields`.
  const cardFields = useMemo(
    () =>
      mergeCardFields(
        fields,
        labelFields.map((f) => f.id),
      ),
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
    <div
      className={cn(
        'flex min-h-0 flex-1 flex-col gap-3 p-4 lg:p-6',
        //  Gantt chạy SÁT ĐÁY cửa sổ, không chừa đệm dưới — đúng lối Lark (khách
        //  đối chiếu 03/09/2026). Lưới ngày của nó kẻ suốt tới đáy, mà dưới cùng
        //  lại hở một dải trắng 24px thì cả biểu đồ đọc ra như một cái khối nổi
        //  giữa trang thay vì một mặt phẳng liền. Ba khung nhìn kia là thẻ/bảng
        //  có mép thật nên vẫn cần đệm.
        //  Phải khai CẢ HAI nấc: `tailwind-merge` không gộp được hai lớp khác
        //  biến thể, nên `pb-0` trần đứng cạnh `lg:p-6` là thua — biến thể
        //  responsive xếp sau trong tệp CSS nên nó thắng, và đệm 24px vẫn còn.
        view === 'gantt' && 'pb-0 lg:pb-0',
      )}
    >
      <header className="flex flex-wrap items-start justify-between gap-3">
        {/*  Nút mở lại cây dự án đứng NGANG tiêu đề (chỉ hiện khi cây đang ẩn),
             chứ không phải một cột nút riêng bên trái — xem `WorkSidebarPeekButton`. */}
        <div className="flex min-w-0 items-start gap-2">
          <WorkSidebarPeekButton />
          {/*  Tên và mô tả sửa NGAY TẠI ĐÂY — bấm vào chữ là thành ô nhập. Hộp
               thoại «Sửa dự án» trong menu bên phải vẫn còn vì nó giữ thêm ô MÀU;
               cả hai đường đều đi qua `useUpdateWorkList` nên không có hai luật. */}
          <ProjectHeaderInlineEdit
            list={board.list}
            canEdit={canOwn}
            pending={updateList.isPending}
            onSave={(values) => updateList.mutate({ id: listId, values })}
          />
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
            {/*  Thành viên + thông tin dự án gom vào MỘT hộp hai thẻ: cả hai
                 đều là "sửa chính cái dự án này", tách ra thì người dùng phải
                 đoán tên nào chứa cái mình cần. */}
            <DropdownMenuItem onClick={() => setManageOpen(true)}>
              <Users className="size-4" />
              Thành viên & thông tin
            </DropdownMenuItem>
            {canManage && (
              <DropdownMenuItem onClick={() => setSettingsOpen(true)}>
                <Settings2 className="size-4" />
                Trường của dự án
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

        {/*  Mức phóng KHÔNG còn ở đây: nó chỉ nói về trục thời gian nên đã dời
            vào cụm điều khiển ngay trên biểu đồ (`GanttTimelineControls`), đúng
            chỗ Lark đặt. Ở cạnh ba tab khung nhìn thì nó nhìn như tab thứ tư. */}
      </div>

      {/*  Thanh công cụ là của BA khung nhìn việc: «Việc mới», lọc điều kiện,
          sắp xếp, trường hiện trên thẻ — không cái nào có nghĩa trên một cuốn
          nhật ký. Tab «Hoạt động» mang bộ lọc riêng của nó (`ActivityFilterBar`). */}
      {view !== 'activities' && (
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
          /*  Cột mốc tạo ra là có NGÀY ngay (hôm nay): mốc không ngày thì không
            có hình thoi nào trên biểu đồ, người dùng bấm xong tưởng hụt. Đổi
            ngày sau bằng cách kéo hình thoi hoặc sửa ở panel chi tiết. */
          onNewMilestone={
            canEdit
              ? () =>
                  createTask.mutate({
                    list_id: listId,
                    title: 'Cột mốc mới',
                    section_id: board.sections[0]?.id ?? null,
                    kind: WORK_TASK_KIND.MILESTONE,
                    due_date: today(),
                  })
              : undefined
          }
          onAddSection={
            canManage
              ? () => {
                  setEditingSection(null)
                  setSectionDialog('create')
                }
              : undefined
          }
        />
      )}

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
            //  ĐÚNG một đường lật trạng thái cho cả ba khung nhìn: kanban,
            //  Danh sách và Gantt cùng gọi `updateTask` với `status`, nên tick
            //  ở đâu cũng làm mới cùng một khóa và ba khung không lệch nhau.
            onToggleDone={(taskId, done) =>
              updateTask.mutate({
                id: taskId,
                values: { status: done ? WORK_TASK_STATUS.DONE : WORK_TASK_STATUS.OPEN },
              })
            }
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
            listId={listId}
            tasks={tasks}
            sections={board.sections}
            labelFields={labelFields}
            members={members}
            fields={cardFields}
            canEdit={canEdit}
            canManage={canManage}
            onOpenTask={setOpenTaskId}
            onToggleDone={(taskId, done) =>
              updateTask.mutate({
                id: taskId,
                values: { status: done ? WORK_TASK_STATUS.DONE : WORK_TASK_STATUS.OPEN },
              })
            }
            onToggleSubtaskDone={(parentId, subtaskId, done) =>
              toggleSubtask.mutate({ parentId, subtaskId, done })
            }
            onRename={(taskId, title) => updateTask.mutate({ id: taskId, values: { title } })}
            onSetAssignees={(taskId, picIds) => setAssignees.mutate({ taskId, picIds })}
            onSetDue={(taskId, dueDate) =>
              updateTask.mutate({ id: taskId, values: { due_date: dueDate } })
            }
            onSetStart={(taskId, startDate) =>
              updateTask.mutate({ id: taskId, values: { start_date: startDate } })
            }
            onSetStatus={(taskId, status) => updateTask.mutate({ id: taskId, values: { status } })}
            onSetLabel={(taskId, fieldId, value) => setLabel.mutate({ taskId, fieldId, value })}
            defaultPicId={defaultPicId}
            //  Cùng luật với kanban (§3.4): đang sắp theo tiêu chí thì KHÓA kéo,
            //  vì thả xong danh sách tự xếp lại chỗ cũ, nhìn như thao tác bị nuốt.
            dragEnabled={sort === 'manual'}
            onMoveTask={(taskId, place) => moveTask.mutate({ taskId, place })}
            onMoveSubtask={(parentId, subtaskId, beforeTaskId) =>
              moveSubtask.mutate({ parentId, subtaskId, beforeTaskId })
            }
            onMoveSection={(sectionId, beforeSectionId) =>
              moveSection.mutate({ sectionId, beforeSectionId })
            }
            onAddTask={addTaskFromDraft}
          />
        )}

        {view === 'gantt' && (
          <GanttView
            listId={listId}
            tasks={tasks}
            sections={board.sections}
            links={board.links ?? []}
            labelFields={labelFields}
            members={members}
            fields={cardFields}
            priorityField={priorityField}
            zoom={ganttZoom}
            onZoomChange={(z) => setViewState({ ganttZoom: z })}
            canEdit={canEdit}
            canManage={canManage}
            //  Cùng luật với kanban và Danh sách (§3.4): đang sắp theo tiêu chí
            //  thì KHÓA kéo, vì thả xong danh sách tự xếp lại chỗ cũ.
            dragEnabled={sort === 'manual'}
            defaultPicId={defaultPicId}
            onOpenTask={setOpenTaskId}
            onMoveDates={(taskId, values) => updateTask.mutate({ id: taskId, values })}
            onToggleDone={(taskId, done) =>
              updateTask.mutate({
                id: taskId,
                values: { status: done ? WORK_TASK_STATUS.DONE : WORK_TASK_STATUS.OPEN },
              })
            }
            onToggleSubtaskDone={(parentId, subtaskId, done) =>
              toggleSubtask.mutate({ parentId, subtaskId, done })
            }
            onRename={(taskId, title) => updateTask.mutate({ id: taskId, values: { title } })}
            onMoveTask={(taskId, place) => moveTask.mutate({ taskId, place })}
            onMoveSubtask={(parentId, subtaskId, beforeTaskId) =>
              moveSubtask.mutate({ parentId, subtaskId, beforeTaskId })
            }
            onMoveSection={(sectionId, beforeSectionId) =>
              moveSection.mutate({ sectionId, beforeSectionId })
            }
            onAddTask={addTaskFromDraft}
            onSetAssignees={(taskId, picIds) => setAssignees.mutate({ taskId, picIds })}
            onSetDue={(taskId, dueDate) =>
              updateTask.mutate({ id: taskId, values: { due_date: dueDate } })
            }
            onSetStart={(taskId, startDate) =>
              updateTask.mutate({ id: taskId, values: { start_date: startDate } })
            }
            onSetStatus={(taskId, status) => updateTask.mutate({ id: taskId, values: { status } })}
            onSetLabel={(taskId, fieldId, value) => setLabel.mutate({ taskId, fieldId, value })}
            onCreateLink={(values) => createLink.mutate(values)}
            onChangeLinkType={(linkId, linkType) =>
              updateLink.mutate({ linkId, values: { link_type: linkType } })
            }
            onDeleteLink={(linkId) => deleteLink.mutate(linkId)}
          />
        )}

        {/*  Nhật ký gộp của cả dự án (D-09). KHÔNG nhận `tasks` đã lọc: bộ lọc
            điều kiện nói về VIỆC, còn đây là dòng sự kiện — lọc theo nó thì
            "Gỡ nhân sự khỏi dự án" chẳng biết xếp vào đâu. */}
        {view === 'activities' && <ActivityFeed listId={listId} onOpenTask={setOpenTaskId} />}
      </div>

      <TaskDetailSheet
        taskId={openTaskId}
        listId={listId}
        sections={board.sections}
        canEdit={canEdit}
        onClose={closeTaskPanel}
      />

      <ListManageDialog
        open={manageOpen}
        list={board.list}
        myRole={myRole}
        onClose={() => setManageOpen(false)}
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
