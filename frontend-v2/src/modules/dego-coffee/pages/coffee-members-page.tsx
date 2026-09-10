import { Link2, Pencil, Plus, Unlink, Users } from 'lucide-react'
import { useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { cn } from '@/shared/utils/cn'
import { CoffeeBlock } from '../components/coffee-block'
import { MemberFormDialog } from '../components/member-form-dialog'
import { MemberMatchDialog } from '../components/member-match-dialog'
import { useCoffeeMembers } from '../hooks/use-coffee'
import type { CoffeeMember } from '../types/coffee'
import { formatPoints } from '../utils/format-points'

const STATUS_VARIANT: Record<number, 'default' | 'outline' | 'destructive'> = {
  1: 'default', // Đang hưởng
  2: 'outline', // Tạm ngưng
  3: 'destructive', // Đã nghỉ
}

/** Thành viên & ghép POS365 (B-01…B-04). */
export function CoffeeMembersPage() {
  const { can } = usePermission()
  const { data, isLoading, isError } = useCoffeeMembers({ page_size: '500' })
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<CoffeeMember | null>(null)
  const [matching, setMatching] = useState<CoffeeMember | null>(null)

  const canWrite = can('coffee_member', 'write')

  const columns = useMemo<DataTableColumn<CoffeeMember>[]>(
    () => [
      {
        key: 'employee_name',
        header: 'Nhân sự',
        width: 240,
        hideable: false,
        cell: (row) => (
          <div className="min-w-0">
            <div className="truncate font-medium">{row.employee_name}</div>
            <div className="font-mono text-xs text-muted-foreground">{row.employee_code}</div>
          </div>
        ),
      },
      { key: 'department_name', header: 'Phòng ban', width: 180, cell: (row) => row.department_name },
      { key: 'level_label', header: 'Cấp', width: 130, cell: (row) => row.level_label },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        cell: (row) => (
          <Badge variant={STATUS_VARIANT[row.status] ?? 'outline'}>{row.status_label}</Badge>
        ),
      },
      {
        key: 'pos_partner_code',
        header: 'Ghép POS365',
        width: 150,
        cell: (row) =>
          row.pos_partner_id ? (
            <span className="font-mono text-sm">{row.pos_partner_code || row.pos_partner_id}</span>
          ) : (
            <span className="text-sm text-amber-600 dark:text-amber-400">Chưa ghép</span>
          ),
      },
      {
        key: 'balance',
        header: 'Số dư',
        width: 120,
        align: 'right',
        cell: (row) => (
          <span
            className={cn('font-medium tabular-nums', (row.balance ?? 0) < 0 && 'text-destructive')}
          >
            {formatPoints(row.balance ?? 0)}
          </span>
        ),
      },
      {
        key: 'actions',
        header: '',
        width: 100,
        align: 'right',
        hideable: false,
        cell: (row) =>
          canWrite ? (
            <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
              <Button
                variant="ghost"
                size="icon"
                title={row.pos_partner_id ? 'Xem / gỡ ghép POS365' : 'Ghép khách POS365'}
                onClick={() => setMatching(row)}
              >
                {row.pos_partner_id ? <Unlink className="size-4" /> : <Link2 className="size-4" />}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                title="Sửa cấp / trạng thái"
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
        title="Thành viên & ghép POS365"
        description="Gán cấp phúc lợi cho nhân sự và ghép 1-1 với khách hàng bên POS365 — người xác nhận từng cặp."
        actions={
          can('coffee_member', 'create') && (
            <Button onClick={() => setCreating(true)}>
              <Plus className="size-4" />
              Thêm thành viên
            </Button>
          )
        }
      />
      <CoffeeBlock
        icon={Users}
        title="Danh sách thành viên"
        className="flex min-h-0 flex-1 flex-col"
      >
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          getRowId={(row) => row.id}
          storageKey="coffee.members"
          fillHeight
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có thành viên nào — thêm người rồi ghép với khách POS365 để bắt đầu."
        />
      </CoffeeBlock>
      {creating && <MemberFormDialog onClose={() => setCreating(false)} />}
      {editing && <MemberFormDialog member={editing} onClose={() => setEditing(null)} />}
      {matching && <MemberMatchDialog member={matching} onClose={() => setMatching(null)} />}
    </PageContainer>
  )
}
