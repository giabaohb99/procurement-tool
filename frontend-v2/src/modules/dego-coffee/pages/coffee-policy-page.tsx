import { BookOpenCheck, Lock, Pencil, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { CoffeeBlock } from '../components/coffee-block'
import { PolicyFormDialog } from '../components/policy-form-dialog'
import { useCoffeePolicies } from '../hooks/use-coffee'
import type { CoffeePolicy } from '../types/coffee'
import { formatPoints } from '../utils/format-points'

/**
 * Chính sách cấp điểm theo cấp (A-01). Không có nút Sửa/Xóa trên dòng đã dùng:
 * đổi mức = THÊM dòng hiệu lực mới — backend chặn thật, đây chỉ là không bày nút.
 */
export function CoffeePolicyPage() {
  const { can } = usePermission()
  const { data, isLoading, isError } = useCoffeePolicies()
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<CoffeePolicy | null>(null)
  const canWrite = can('coffee_policy', 'write')

  const columns = useMemo<DataTableColumn<CoffeePolicy>[]>(
    () => [
      {
        key: 'level_label',
        header: 'Cấp phúc lợi',
        width: 200,
        hideable: false,
        cell: (row) => <span className="font-medium">{row.level_label}</span>,
      },
      {
        key: 'monthly_points',
        header: 'Mức điểm / tháng',
        width: 160,
        align: 'right',
        cell: (row) => (
          <span className="font-medium tabular-nums">{formatPoints(row.monthly_points)}</span>
        ),
      },
      {
        key: 'effective_from',
        header: 'Hiệu lực từ',
        width: 130,
        cell: (row) => <span className="tabular-nums">{row.effective_from}</span>,
      },
      { key: 'note', header: 'Ghi chú', width: 280, cell: (row) => row.note },
      {
        key: 'locked',
        header: '',
        width: 80,
        align: 'right',
        hideable: false,
        cell: (row) =>
          row.locked ? (
            <Lock
              className="ml-auto size-4 text-muted-foreground"
              aria-label="Dòng đã được kỳ cấp phát dùng tới — chỉ đọc"
            >
              <title>Dòng đã được kỳ cấp phát dùng tới — chỉ đọc</title>
            </Lock>
          ) : canWrite ? (
            <div className="flex justify-end" onClick={(e) => e.stopPropagation()}>
              <Button
                variant="ghost"
                size="icon"
                title="Sửa dòng (chưa qua kỳ cấp nào)"
                onClick={() => setEditing(row)}
              >
                <Pencil className="size-4" />
              </Button>
            </div>
          ) : null,
      },
    ],
    [canWrite],
  )

  return (
    <PageContainer fill className="gap-6">
      <PageHeader
        title="Chính sách cấp điểm"
        description="Mỗi cấp một mức điểm/tháng. Reset đầu kỳ cấp theo dòng đang hiệu lực; dòng đã dùng chỉ đọc."
        actions={
          can('coffee_policy', 'create') && (
            <Button onClick={() => setCreating(true)}>
              <Plus className="size-4" />
              Thêm dòng
            </Button>
          )
        }
      />
      <CoffeeBlock
        icon={BookOpenCheck}
        title="Bảng mức điểm theo cấp"
        className="flex min-h-0 flex-1 flex-col"
      >
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          getRowId={(row) => row.id}
          storageKey="coffee.policies"
          fillHeight
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa khai mức nào — chưa khai thì reset đầu tháng KHÔNG cấp điểm cho cấp đó."
        />
      </CoffeeBlock>
      {creating && <PolicyFormDialog onClose={() => setCreating(false)} />}
      {editing && <PolicyFormDialog policy={editing} onClose={() => setEditing(null)} />}
    </PageContainer>
  )
}
