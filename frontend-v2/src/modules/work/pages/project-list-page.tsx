import { Archive, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { Progress } from '@/shared/ui/progress'
import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { WorkCreateDialog } from '../components/work-create-dialog'
import { useWorkProjects } from '../hooks/use-work-lists'
import type { WorkList, WorkMember } from '../types/work'
import { dotClass } from '../utils/work-colors'

/**
 * Bảng liệt kê MỌI dự án — màn giữa của phân hệ, mở bằng mục «Dự án» ở thanh
 * trái. Dựng theo màn *Task List* của Lark: tên · chủ sở hữu · thành viên ·
 * ngày tạo.
 *
 * Một dự án CHÍNH LÀ một danh sách công việc (`WorkList`), nên đây chỉ là một
 * lối nhìn khác của đúng dữ liệu cây bên trái — bấm một dòng là vào thẳng bảng
 * kanban của dự án đó.
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
              <Avatar member={row.owner} />
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
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-navy">Dự án</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Mọi dự án bạn tham gia. Bấm một dòng để mở bảng công việc của dự án đó.
          </p>
        </div>
        <Button size="sm" onClick={() => setCreating(true)}>
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
        emptyMessage="Bạn chưa tham gia dự án nào."
        storageKey="work.projects"
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

/**
 * Thanh tiến độ của một dự án: việc đã xong / tổng số việc.
 *
 * Dự án CHƯA CÓ VIỆC NÀO hiện 0% chứ không phải 100%: `0/0` mà làm tròn thành
 * "xong hết" thì bảng báo một dự án trắng trơn là đã hoàn tất.
 */
function ProgressCell({ done, total }: { done: number; total: number }) {
  const percent = total > 0 ? Math.round((done / total) * 100) : 0
  return (
    <span className="flex items-center gap-2" title={`${done}/${total} việc`}>
      <Progress value={percent} className="h-2 flex-1" />
      <span className="w-10 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
        {percent}%
      </span>
    </span>
  )
}

/** Chữ tắt trên avatar: hai chữ cái đầu của TỪ CUỐI — tên Việt gọi theo tên. */
function Avatar({ member }: { member: WorkMember }) {
  const words = member.employee_name.trim().split(/\s+/).filter(Boolean)
  const initials = words.length ? words[words.length - 1].slice(0, 2).toUpperCase() : '?'
  return (
    <span
      title={member.employee_name || `Nhân sự #${member.employee_id}`}
      className="grid size-6 shrink-0 place-items-center rounded-full border bg-accent text-[10px] font-medium text-accent-foreground"
    >
      {initials}
    </span>
  )
}

/**
 * Tối đa 4 avatar rồi "+n" — dự án đông người mà xếp hết thì cột nong ra, mà
 * bảng chạy `table-fixed` nên phần thừa bị cắt cụt chứ không xuống dòng.
 */
function MemberStack({ members }: { members: WorkMember[] }) {
  if (members.length === 0) return <span className="text-muted-foreground">—</span>
  return (
    <span className="flex items-center -space-x-1.5">
      {members.slice(0, 4).map((member) => (
        <Avatar key={member.employee_id} member={member} />
      ))}
      {members.length > 4 && (
        <span className="pl-2.5 text-xs text-muted-foreground">+{members.length - 4}</span>
      )}
    </span>
  )
}
