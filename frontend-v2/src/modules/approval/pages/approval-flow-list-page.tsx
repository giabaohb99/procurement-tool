import { Plus, Power } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Switch } from '@/shared/ui/switch'
import { ENTITY_LABELS } from '../helpers/entity-link'
import {
  useApprovalFlows,
  useApprovalSwitches,
  useSetApprovalSwitch,
} from '../hooks/use-approvals'
import type { ApprovalFlow } from '../types/approval'

/** Các loại chứng từ có thể chạy qua bộ máy duyệt — cùng danh sách với backend. */
const CAC_LOAI = Object.keys(ENTITY_LABELS)

/**
 * Danh sách LUỒNG DUYỆT + công tắc bật/tắt theo từng loại chứng từ.
 *
 * Hai thứ này đứng chung một màn vì chúng là hai nửa của một câu hỏi: *"loại
 * chứng từ này đang duyệt theo đường nào"*. Khai luồng mà quên bật công tắc thì
 * luồng nằm im, và người khai không hiểu vì sao phiếu vẫn đi đường cũ.
 */
export function ApprovalFlowListPage() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useApprovalFlows()

  const columns = useMemo<DataTableColumn<ApprovalFlow>[]>(
    () => [
      {
        key: 'name',
        header: 'Tên luồng',
        width: 300,
        hideable: false,
        cell: (row) => (
          <div>
            <div className="font-medium">{row.name}</div>
            {row.code && <div className="font-mono text-xs text-muted-foreground">{row.code}</div>}
          </div>
        ),
      },
      {
        key: 'entity',
        header: 'Loại chứng từ',
        width: 180,
        cell: (row) => ENTITY_LABELS[row.entity] ?? row.entity,
      },
      {
        key: 'node_count',
        header: 'Số bước',
        width: 100,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{row.node_count}</span>,
      },
      {
        key: 'version_no',
        header: 'Bản',
        width: 90,
        align: 'right',
        //  Phiếu đang chạy giữ bản chụp riêng nên số này không ảnh hưởng chúng —
        //  nó chỉ để tra lịch sử và để bản in nói đúng phiếu chạy theo bản nào.
        cell: (row) => <span className="tabular-nums">{row.version_no}</span>,
      },
      {
        key: 'condition',
        header: 'Áp khi',
        width: 260,
        cell: (row) => row.condition || <span className="text-muted-foreground">Mọi phiếu</span>,
      },
      {
        key: 'is_active',
        header: 'Trạng thái',
        width: 130,
        cell: (row) => (
          <Badge variant={row.is_active ? 'default' : 'outline'}>
            {row.is_active ? 'Đang dùng' : 'Ngừng'}
          </Badge>
        ),
      },
    ],
    [],
  )

  return (
    <PageContainer className="space-y-4">
      <PageHeader
        title="Luồng phê duyệt"
        description="Khai bằng giao diện — thêm bước, đổi người duyệt, rẽ nhánh mà không phải sửa mã."
        actions={
          <Button onClick={() => navigate(appRoutes.approval.flowNew)}>
            <Plus className="size-4" />
            Tạo luồng
          </Button>
        }
      />

      <CongTacTheoLoai />

      <Card className="p-4">
        <DataTable
          columns={columns}
          rows={data?.items}
          getRowId={(row) => row.id}
          storageKey="approval.flows"
          isLoading={isLoading}
          isError={isError}
          onRowClick={(row) => navigate(appRoutes.approval.flowDetail(row.id))}
          emptyMessage="Chưa khai luồng nào. Chưa có luồng thì chứng từ vẫn đi theo đường duyệt cũ."
        />
      </Card>
    </PageContainer>
  )
}

/**
 * I26 — công tắc theo từng loại chứng từ, **đường lui của cả bộ máy**.
 *
 * Tắt là loại chứng từ đó quay về đường duyệt cũ ngay, không cần deploy lại.
 * Phiếu đã bắt đầu chạy bằng bộ máy mới thì vẫn chạy tiếp cho hết — cắt ngang
 * giữa chừng là bỏ rơi phiếu ở trạng thái không màn hình nào nhặt lên.
 */
function CongTacTheoLoai() {
  const { data } = useApprovalSwitches()
  const setSwitch = useSetApprovalSwitch()

  const dangBat = new Map((data ?? []).map((row) => [row.entity, row.is_enabled]))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Power className="size-4 text-muted-foreground" />
          Bật bộ máy duyệt mới theo loại chứng từ
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">
          Mặc định <b>TẮT</b> cho mọi loại. Tắt thì chứng từ đi theo đường duyệt cũ đang
          chạy — đây là đường lui, giữ nguyên để còn quay về được khi có sự cố.
        </p>
        <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {CAC_LOAI.map((ma) => (
            <li
              key={ma}
              className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
            >
              <span className="text-sm">{ENTITY_LABELS[ma]}</span>
              <Switch
                checked={dangBat.get(ma) ?? false}
                disabled={setSwitch.isPending}
                onCheckedChange={(bat) =>
                  setSwitch.mutate({ entity: ma, is_enabled: bat, note: '' })
                }
              />
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
