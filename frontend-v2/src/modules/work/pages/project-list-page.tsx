import { Archive, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { SearchField } from '@/shared/ui/search-field'
import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { matchesVietnamese } from '@/shared/utils/vn-text'
import { GroupManageDialog } from '../components/group-manage-dialog'
import { ProjectCard } from '../components/project-card'
import { MemberAvatar, MemberStack, ProgressCell } from '../components/project-cells'
import { ProjectGroupFilter } from '../components/project-group-filter'
import { WorkCreateDialog } from '../components/work-create-dialog'
import { WorkSidebarPeekButton } from '../components/work-sidebar-peek-button'
import { useWorkProjects, useWorkSidebar } from '../hooks/use-work-lists'
import type { WorkGroup, WorkList } from '../types/work'
import { dotClass } from '../utils/work-colors'
import {
  NO_GROUP_LABEL,
  flattenGroups,
  groupNameOf,
  matchesProjectGroup,
  type ProjectGroupFilterValue,
} from '../utils/work-groups'

/**
 * Bảng liệt kê MỌI dự án — màn giữa của phân hệ, mở bằng mục "Dự án" ở thanh
 * trái. Dựng theo màn *Task List* của Lark: tên · chủ sở hữu · thành viên ·
 * ngày tạo.
 *
 * Một dự án CHÍNH LÀ một danh sách công việc (`WorkList`), nên đây chỉ là một
 * lối nhìn khác của đúng dữ liệu cây bên trái — bấm một dòng là vào thẳng bảng
 * kanban của dự án đó.
 *
 * Ở khổ hẹp bảng đổi thành danh sách THẺ (`ProjectCard`), và cây dự án rút vào
 * tờ trượt của `WorkSidebarPeekButton` — xem ghi chú ở `work-layout-page.tsx`.
 */
export function ProjectListPage() {
  const navigate = useNavigate()
  const [showArchived, setShowArchived] = useState(false)
  const [creating, setCreating] = useState(false)
  //  bao-CR-482: nhóm đang mở hộp Quản lý nhóm từ cụm nhóm phía trên bảng.
  const [manageGroup, setManageGroup] = useState<WorkGroup | null>(null)
  const { data, isLoading, isError } = useWorkProjects(showArchived)
  //  Cây nhóm — cùng truy vấn với cây bên trái nên không tốn thêm lượt gọi khi cây đang mở.
  const { data: sidebar } = useWorkSidebar(showArchived)
  const groups = useMemo(() => flattenGroups(sidebar), [sidebar])

  //  Bảng xếp theo NHÓM trước (đúng thứ tự cây), dự án ngoài nhóm đứng cuối —
  //  trước CR-482 bảng phẳng, nhìn không ra dự án nào thuộc "DX" dù cây bên trái có.
  const rows = useMemo(() => {
    if (!data) return data
    const order = new Map(groups.map((g, i) => [g.id, i]))
    const rank = (row: WorkList) => (row.group_id ? (order.get(row.group_id) ?? 9_999) : 10_000)
    return data.slice().sort((a, b) => rank(a) - rank(b) || a.sort_order - b.sort_order || a.id - b.id)
  }, [data, groups])

  //  duoc-CR-782: lọc tại trình duyệt — màn này nạp đủ mọi dự án người xem tham gia (vài chục dòng), không phân trang.
  const [query, setQuery] = useState('')
  const [groupFilter, setGroupFilter] = useState<ProjectGroupFilterValue>('all')
  const filtering = query.trim() !== '' || groupFilter !== 'all'
  const visibleRows = useMemo(
    () =>
      rows?.filter(
        (row) =>
          matchesProjectGroup(row, groupFilter) &&
          (matchesVietnamese(row.name, query) || matchesVietnamese(row.description ?? '', query)),
      ),
    [rows, groupFilter, query],
  )

  const columns = useMemo<DataTableColumn<WorkList>[]>(
    () => [
      {
        key: 'name',
        header: 'Tên dự án',
        width: 260,
        hideable: false,
        defaultPinned: true,
        cell: (row) => (
          <span className="flex items-center gap-2">
            <span className={cn('size-2 shrink-0 rounded-full', dotClass(row.color))} />
            <span className="truncate font-medium">{row.name}</span>
            {row.is_archived === 1 && (
              <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
                Đã lưu trữ
              </span>
            )}
          </span>
        ),
      },
      {
        key: 'group',
        header: 'Nhóm dự án',
        width: 140,
        cell: (row) => {
          const name = groupNameOf(groups, row.group_id)
          return name ? (
            <span className="truncate">{name}</span>
          ) : (
            <span className="truncate text-muted-foreground">{NO_GROUP_LABEL}</span>
          )
        },
      },
      {
        key: 'description',
        header: 'Mô tả',
        width: 220,
        cell: (row) => (
          <span className="truncate text-muted-foreground">{row.description || '—'}</span>
        ),
      },
      {
        key: 'owner',
        header: 'Chủ sở hữu',
        width: 180,
        cell: (row) =>
          row.owner ? (
            <span className="flex items-center gap-2">
              <MemberAvatar member={row.owner} />
              <span className="truncate">{row.owner.employee_name}</span>
            </span>
          ) : (
            //  `null` ở đây là dự án THẬT SỰ chưa có chủ (dữ liệu cũ), không
            //  phải "chưa nạp" — màn này luôn gọi kèm `with_people`.
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        key: 'members',
        header: 'Thành viên',
        width: 120,
        cell: (row) => <MemberStack members={row.members} />,
      },
      {
        key: 'progress',
        header: 'Tiến độ',
        width: 170,
        cell: (row) => <ProgressCell done={row.task_done} total={row.task_count} />,
      },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        width: 110,
        cell: (row) => formatDate(row.created_at),
      },
    ],
    [groups],
  )

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 p-4 lg:p-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        {/*  Nút mở lại cây dự án đứng NGANG tiêu đề, chỉ hiện khi cây đang ẩn —
             phải có ở ĐÂY nữa, không chỉ ở trang chi tiết dự án: ẩn cây rồi bấm
             về danh sách dự án mà trang này không có nút thì người dùng kẹt.
             Ở khổ hẹp nút luôn hiện: cây không đứng cạnh nội dung nữa nên đây là
             đường DUY NHẤT tới nó. */}
        <div className="flex min-w-0 items-start gap-2">
          <WorkSidebarPeekButton />
          <div className="min-w-0">
            <h1 className="text-xl font-semibold tracking-tight text-navy">Dự án</h1>
            {/*  Dòng mô tả ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi
                 — mà ở đây nó ngốn ba hàng chữ ngay trên đầu danh sách. */}
            <p className="mt-1 text-sm text-muted-foreground max-md:hidden">
              Mọi dự án bạn tham gia. Bấm một dòng để mở bảng công việc của dự án đó.
            </p>
          </div>
        </div>
        {/*  Khổ hẹp: nút chiếm trọn hàng — hành động chính phải dễ chạm nhất. */}
        <Button size="sm" className="max-md:w-full" onClick={() => setCreating(true)}>
          <Plus className="size-4" />
          Tạo dự án
        </Button>
      </header>

      <DataTable
        fillHeight
        columns={columns}
        rows={visibleRows}
        getRowId={(row) => row.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage={
          //  Nói rõ RỖNG VÌ BỘ LỌC hay rỗng vì chưa có gì: người vừa bật "Hiện
          //  cả dự án lưu trữ" mà đọc câu chung sẽ tưởng nút đó làm hỏng danh sách.
          filtering
            ? 'Không có dự án nào khớp bộ lọc.'
            : showArchived
              ? 'Bạn chưa tham gia dự án nào, kể cả dự án đã lưu trữ.'
              : 'Bạn chưa tham gia dự án nào.'
        }
        storageKey="work.projects"
        //  Khổ hẹp: THẺ thay bảng — xem `ProjectCard`.
        mobileCard={(row: WorkList) => <ProjectCard project={row} />}
        onRowClick={(row) => navigate(appRoutes.project.detail(row.id))}
        toolbar={
          <>
            {/*  Khung cố định bề rộng: `SearchField` tự giãn `flex-1`, để trần là nó ăn hết hàng. */}
            <div className="w-full sm:w-56">
              <SearchField
                value={query}
                onChange={setQuery}
                placeholder="Tìm tên, mô tả dự án…"
                placeholderShort="Tìm dự án…"
                aria-label="Tìm dự án"
                className="w-full"
              />
            </div>
            {/*  bao-CR-482 → duoc-CR-782: nhóm thấy được ngay trên bảng (ai ẩn cây trái vẫn biết nhóm tồn tại, vẫn có
                 chỗ đổi tên / phân quyền cả nhóm), giờ kiêm luôn bộ lọc. */}
            {groups.length > 0 && (
              <ProjectGroupFilter
                groups={groups}
                projects={data ?? []}
                value={groupFilter}
                onChange={setGroupFilter}
                onManage={setManageGroup}
                showArchived={showArchived}
              />
            )}
            {/*  Nhãn ngắn + trạng thái bấm (`aria-pressed`, nền đậm khi bật): nhãn cũ "Hiện cả dự án lưu trữ" dài 180px
                 đẩy nút Tải lại / Cột rớt xuống hàng hai khi thanh công cụ có thêm ô tìm và nút nhóm. */}
            <Button
              variant={showArchived ? 'secondary' : 'outline'}
              size="sm"
              aria-pressed={showArchived}
              title={showArchived ? 'Đang hiện cả dự án đã lưu trữ — bấm để ẩn' : 'Hiện cả dự án đã lưu trữ'}
              onClick={() => {
                setShowArchived((value) => !value)
                //  Nhóm đang lọc có thể là nhóm lưu trữ sắp bị ẩn khỏi ô chọn — về "Tất cả" cho khỏi kẹt.
                setGroupFilter('all')
              }}
            >
              <Archive className="size-4" />
              Lưu trữ
            </Button>
          </>
        }
      />

      <WorkCreateDialog
        mode={creating ? 'list' : null}
        parentGroupId={null}
        onClose={() => setCreating(false)}
      />
      <GroupManageDialog
        open={manageGroup !== null}
        group={manageGroup}
        onClose={() => setManageGroup(null)}
      />
    </div>
  )
}
