import { AlertTriangle, Inbox, UserCheck } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate } from '@/shared/utils/format-date'
import { ApprovalActionDialog } from '../components/approval-action-dialog'
import { ENTITY_LABELS, entityLink } from '../helpers/entity-link'
import { useMyTasks } from '../hooks/use-approvals'
import type { MyTask } from '../types/approval'

const ALL = 'all'

/**
 * VIỆC CỦA TÔI (I17) — một chỗ gom mọi thứ đang chờ tôi.
 *
 * Gom cả văn thư lẫn thu mua vào MỘT màn là toàn bộ lý do bộ máy duyệt này tồn
 * tại. Trước đó mỗi phân hệ có một danh sách chờ riêng, nên "hôm nay tôi phải
 * duyệt những gì" là câu không ai trả lời được nếu không mở lần lượt sáu màn.
 *
 * Hai thứ phải thấy được ngay mà không cần bấm vào: việc nào **quá hạn**, và
 * việc nào mình đang làm **thay người khác** theo ủy quyền — biết sau khi bấm
 * thì đã ký mất rồi.
 */
export function MyTasksPage() {
  const { data, isLoading, isError } = useMyTasks()
  const [entity, setEntity] = useState(ALL)
  const [dangXuLy, setDangXuLy] = useState<MyTask | null>(null)

  const items = useMemo(() => {
    const rows = data?.items ?? []
    return entity === ALL ? rows : rows.filter((row) => row.entity === entity)
  }, [data?.items, entity])

  const cacLoai = useMemo(
    () => [...new Set((data?.items ?? []).map((row) => row.entity))],
    [data?.items],
  )
  const soQuaHan = (data?.items ?? []).filter((row) => row.is_overdue).length

  const columns = useMemo<DataTableColumn<MyTask>[]>(
    () => [
      {
        key: 'entity',
        header: 'Loại',
        width: 150,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {ENTITY_LABELS[row.entity] ?? row.entity}
          </Badge>
        ),
      },
      {
        key: 'entity_code',
        header: 'Số hiệu',
        width: 160,
        hideable: false,
        cell: (row) => (
          <Link
            to={entityLink(row.entity, row.entity_id)}
            className="font-mono text-sm text-navy hover:underline"
          >
            {row.entity_code || `#${row.entity_id}`}
          </Link>
        ),
      },
      {
        key: 'entity_title',
        header: 'Nội dung',
        width: 380,
        cell: (row) => (
          <div className="min-w-0">
            <div className="truncate font-medium">{row.entity_title}</div>
            <div className="text-xs text-muted-foreground">
              {row.node_name || `Bước ${row.node_seq}`}
              {row.started_by_name && ` · ${row.started_by_name} trình`}
            </div>
          </div>
        ),
      },
      {
        key: 'on_behalf_of_name',
        header: 'Bấm thay',
        width: 170,
        cell: (row) =>
          //  Phải thấy TRƯỚC khi bấm chứ không phải sau: ký thay người khác là
          //  một việc khác hẳn ký cho mình, và nhật ký sẽ ghi cả hai tên.
          row.on_behalf_of_name ? (
            <span className="flex items-center gap-1.5 text-sm text-amber-800">
              <UserCheck className="size-3.5 shrink-0" />
              {row.on_behalf_of_name}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        key: 'due_at',
        header: 'Hạn duyệt',
        width: 150,
        cell: (row) =>
          row.due_at ? (
            <span className={row.is_overdue ? 'font-medium text-destructive' : undefined}>
              {formatDate(row.due_at)}
              {row.is_overdue && ' · quá hạn'}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Việc của tôi"
        description="Mọi phiếu đang chờ bạn duyệt — của cả Văn thư lẫn Thu mua, gom một chỗ."
      />

      {soQuaHan > 0 && (
        <p className="mb-3 flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
          <span>
            <b>{soQuaHan}</b> việc đã quá hạn duyệt. Quá lâu nữa thì hệ sẽ tự đẩy lên
            cấp trên của bạn.
          </span>
        </p>
      )}

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={items}
          getRowId={(row) => row.id}
          storageKey="approval.my-tasks"
          fillHeight
          isLoading={isLoading}
          isError={isError}
          onRowClick={(row) => setDangXuLy(row)}
          emptyMessage={
            (data?.items?.length ?? 0) > 0
              ? 'Không có việc nào thuộc loại chứng từ đang lọc.'
              : 'Không có việc nào đang chờ bạn.'
          }
          toolbar={
            <>
              <Select value={entity} onValueChange={setEntity}>
                <SelectTrigger className="w-56">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại chứng từ</SelectItem>
                  {cacLoai.map((ma) => (
                    <SelectItem key={ma} value={ma}>
                      {ENTITY_LABELS[ma] ?? ma}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Inbox className="size-4" />
                {items.length} việc đang chờ
              </span>
            </>
          }
        />
      </Card>

      {dangXuLy && (
        <ApprovalActionDialog
          task={dangXuLy}
          open
          onOpenChange={(mo) => !mo && setDangXuLy(null)}
        />
      )}
    </PageContainer>
  )
}
