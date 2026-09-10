import { Archive, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { ProjectCard } from '../components/project-card'
import { MemberAvatar, MemberStack, ProgressCell } from '../components/project-cells'
import { WorkCreateDialog } from '../components/work-create-dialog'
import { WorkSidebarPeekButton } from '../components/work-sidebar-peek-button'
import { useWorkProjects } from '../hooks/use-work-lists'
import type { WorkList } from '../types/work'
import { dotClass } from '../utils/work-colors'

/**
 * Bảng liệt kê MỌI dự án — màn giữa của phân hệ, mở bằng mục «Dự án» ở thanh
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
  const { data, isLoading, isError } = useWorkProjects(showArchived)

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
    [],
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
          Dự án mới
        </Button>
      </header>

      <DataTable
        fillHeight
        columns={columns}
        rows={data}
        getRowId={(row) => row.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage={
          //  Nói rõ RỖNG VÌ BỘ LỌC hay rỗng vì chưa có gì: người vừa bật «Hiện
          //  cả dự án lưu trữ» mà đọc câu chung sẽ tưởng nút đó làm hỏng danh sách.
          showArchived
            ? 'Bạn chưa tham gia dự án nào, kể cả dự án đã lưu trữ.'
            : 'Bạn chưa tham gia dự án nào.'
        }
        storageKey="work.projects"
        //  Khổ hẹp: THẺ thay bảng — xem `ProjectCard`.
        mobileCard={(row: WorkList) => <ProjectCard project={row} />}
        onRowClick={(row) => navigate(appRoutes.project.detail(row.id))}
        toolbar={
          <Button
            variant={showArchived ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => setShowArchived((value) => !value)}
          >
            <Archive className="size-4" />
            {showArchived ? 'Đang hiện dự án lưu trữ' : 'Hiện cả dự án lưu trữ'}
          </Button>
        }
      />

      <WorkCreateDialog
        mode={creating ? 'list' : null}
        parentGroupId={null}
        onClose={() => setCreating(false)}
      />
    </div>
  )
}
