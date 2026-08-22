import { Plus, Power, Search, Trash2, TriangleAlert } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import {
  applyClientFilter,
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { APPROVAL_FLOW_FILTER_FIELDS } from '../config/approval-flow-filter-fields'
import { conditionFieldsOf } from '../config/condition-fields'
import { cauDieuKien } from '../helpers/condition-sentence'
import { parseCondition } from '../helpers/node-condition'
import { useConditionChoices } from '../hooks/use-condition-choices'
import { CAC_LOAI, ENTITY_LABELS } from '../helpers/entity-link'
import { ALL, filterApprovalFlows } from '../helpers/filter-approval-flows'
import { flowStatus, type FlowStatusTone } from '../helpers/flow-status'
import {
  useApprovalFlows,
  useApprovalSwitches,
  useDeleteApprovalFlow,
} from '../hooks/use-approvals'
import type { ApprovalFlow } from '../types/approval'

const FILTER_CONFIG = {
  fields: APPROVAL_FLOW_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['loai', 'dung'],
}

/** Huy hiệu trạng thái: chỉ "Đang chạy" mới tô đậm, phần còn lại là viền. */
const BADGE_VARIANT: Record<FlowStatusTone, 'default' | 'outline'> = {
  running: 'default',
  waiting: 'outline',
  off: 'outline',
}

export function ApprovalFlowListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <ApprovalFlowListContent />
    </FilterProvider>
  )
}

/**
 * Danh sách LUỒNG DUYỆT + công tắc bật/tắt theo từng loại chứng từ.
 *
 * Hai thứ này đứng chung một màn vì chúng là hai nửa của một câu hỏi: *"loại
 * chứng từ này đang duyệt theo đường nào"*. Khai luồng mà quên bật công tắc thì
 * luồng nằm im, và người khai không hiểu vì sao phiếu vẫn đi đường cũ.
 */
function ApprovalFlowListContent() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { data, isLoading, isError } = useApprovalFlows()
  const { data: switches } = useApprovalSwitches()
  const { appliedState } = useFilterContext()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [entity, setEntity] = useUrlParamState('loai', ALL)
  const [dung, setDung] = useUrlParamState('dung', ALL)
  const deleteFlow = useDeleteApprovalFlow()

  const rows = useMemo(() => {
    //  Hai tầng lọc nối nhau: thanh công cụ (tìm + hai select) rồi mới tới bộ
    //  lọc nâng cao. Tầng đầu tách ra hàm thuần để kiểm được bằng test.
    const found = filterApprovalFlows(data?.items ?? [], {
      entity,
      dung,
      keyword: debouncedValue,
    })
    return applyClientFilter(found, appliedState)
  }, [data?.items, debouncedValue, entity, dung, appliedState])

  //  Danh mục để dịch id trong điều kiện thành TÊN. Không truyền nhân sự: điều
  //  kiện ở tầng luồng chỉ lọc theo loại/pháp nhân/phòng, và nạp cả nghìn nhân
  //  sự chỉ để dựng một dòng chữ là quá đắt cho màn danh sách.
  const layLuaChon = useConditionChoices([])

  const engineOn = useMemo(
    () => new Map((switches ?? []).map((row) => [row.entity, row.is_enabled])),
    [switches],
  )

  const columns = useMemo<DataTableColumn<ApprovalFlow>[]>(
    () => [
      {
        key: 'name',
        header: 'Tên luồng',
        width: 300,
        hideable: false,
        cell: (row) => (
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="truncate font-medium">{row.name}</span>
              {/*  Hai luồng mặc định cùng bật thì chỉ một cái chạy — dấu hiệu
                  phải nằm ngay cạnh TÊN, chỗ mắt dừng lại đầu tiên. */}
              {row.duplicate_default_warning && (
                <TriangleAlert
                  className="size-4 shrink-0 text-amber-600"
                  aria-label={row.duplicate_default_warning}
                >
                  <title>{row.duplicate_default_warning}</title>
                </TriangleAlert>
              )}
            </div>
            {row.code && (
              <div className="truncate font-mono text-xs text-muted-foreground">{row.code}</div>
            )}
            {row.duplicate_default_warning && (
              <div className="mt-0.5 text-xs text-amber-700 dark:text-amber-500">
                {row.duplicate_default_warning}
              </div>
            )}
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
        key: 'company_name',
        header: 'Pháp nhân',
        width: 220,
        cell: (row) =>
          row.company_name || <span className="text-muted-foreground">Tất cả pháp nhân</span>,
      },
      {
        key: 'condition',
        header: 'Áp khi',
        width: 300,
        cell: (row) => {
          if (!row.condition) return <span className="text-muted-foreground">Mọi phiếu</span>

          //  Dịch điều kiện thành câu tiếng Việt — cột này để ĐỌC LƯỚT, phơi
          //  JSON thô ra bảng thì người khai luồng phải tự giải mã từng dòng.
          const fields = conditionFieldsOf(row.entity)
          const { rows: dieuKien, advanced } = parseCondition(row.condition, (name) =>
            fields.some((field) => field.name === name),
          )
          if (advanced || dieuKien.length === 0) {
            return <span className="truncate font-mono text-xs">{row.condition}</span>
          }
          return <span className="truncate">{cauDieuKien(dieuKien, fields, layLuaChon)}</span>
        },
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
        //  Ẩn sẵn: phiếu đang chạy giữ bản chụp riêng nên số này không ảnh
        //  hưởng chúng — nó chỉ để tra lịch sử, không phải thứ đọc hằng ngày.
        //  Cần thì bật lại trong menu "Cột".
        defaultHidden: true,
        cell: (row) => <span className="tabular-nums">{row.version_no}</span>,
      },
      {
        key: 'is_active',
        header: 'Trạng thái',
        width: 160,
        cell: (row) => {
          const trangThai = flowStatus(row, engineOn.get(row.entity) ?? false)
          return (
            <Badge variant={BADGE_VARIANT[trangThai.tone]} title={trangThai.hint}>
              {trangThai.label}
            </Badge>
          )
        },
      },
      {
        key: 'actions',
        header: '',
        width: 70,
        align: 'right',
        hideable: false,
        cell: (row) =>
          //  Không có quyền xóa thì bỏ hẳn nút, không hiện nút mờ: người dùng
          //  không đoán được vì sao nút mờ, còn hàng rào thật vẫn ở backend.
          can('approval_flow', 'delete') ? (
            //  Chặn click lan lên dòng, nếu không mỗi lần bấm Xóa lại mở luôn
            //  màn khai luồng phía sau hộp xác nhận.
            <div className="flex justify-end" onClick={(event) => event.stopPropagation()}>
              <ConfirmIconButton
                icon={Trash2}
                title="Xóa luồng"
                confirmTitle={`Xóa luồng "${row.name}"?`}
                confirmDescription={
                  'Xóa cả các bước đã khai trong luồng và không khôi phục được. ' +
                  'Nếu còn phiếu đang chạy theo luồng này, hệ thống sẽ chặn — khi đó ' +
                  'hãy tắt luồng trong màn khai luồng thay vì xóa.'
                }
                confirmLabel="Xóa"
                destructive
                disabled={deleteFlow.isPending}
                onConfirm={() => deleteFlow.mutate(row.id)}
              />
            </div>
          ) : null,
      },
    ],
    [can, deleteFlow, engineOn, layLuaChon],
  )

  return (
    //  `fill` + `Card flex min-h-0 flex-1 flex-col` + `DataTable fillHeight` là
    //  BA MẮT XÍCH của chế độ fit chiều cao (`docs/ui/table.md` mục 2), thiếu một
    //  là hỏng cả ba.
    <PageContainer fill>
      <PageHeader
        title="Luồng phê duyệt"
        description="Khai bằng giao diện — thêm bước, đổi người duyệt, rẽ nhánh mà không phải sửa mã."
        actions={
          <>
            {/*  Hai nút này GÁC QUYỀN, như nút xóa ở cột thao tác. Người chỉ có
                 `approval_flow: read` (văn thư pháp nhân chẳng hạn) vào màn này
                 để XEM luồng nào đang áp cho văn bản của mình — bày nút cho họ
                 là dẫn thẳng vào 403 ở `PUT /switches` (`write`) và `POST` luồng
                 (`create`). */}
            {can('approval_flow', 'write') && (
              //  Lối sang công tắc bật bộ máy: cột Trạng thái bên dưới có nhắc
              //  tới nó ("Chờ bật bộ máy") nên phải với tới được từ đây.
              <Button variant="outline" onClick={() => navigate(appRoutes.approval.engine)}>
                <Power className="size-4" />
                Bật bộ máy
              </Button>
            )}
            {can('approval_flow', 'create') && (
              <Button onClick={() => navigate(appRoutes.approval.flowNew)}>
                <Plus className="size-4" />
                Tạo luồng
              </Button>
            )}
          </>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(row) => row.id}
          storageKey="approval.flows"
          fillHeight
          isLoading={isLoading}
          isError={isError}
          onRowClick={(row) => navigate(appRoutes.approval.flowDetail(row.id))}
          emptyMessage={
            (data?.items?.length ?? 0) > 0
              ? 'Không có luồng nào khớp điều kiện đang lọc.'
              : 'Chưa khai luồng nào. Chưa có luồng thì chứng từ vẫn đi theo đường duyệt cũ.'
          }
          toolbar={
            <>
              <div className="relative w-full max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo tên, mã, mô tả…"
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                />
              </div>

              <Select value={entity} onValueChange={setEntity}>
                <SelectTrigger className="w-52">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại chứng từ</SelectItem>
                  {CAC_LOAI.map((ma) => (
                    <SelectItem key={ma} value={ma}>
                      {ENTITY_LABELS[ma]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={dung} onValueChange={setDung}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {/*  Lọc theo cờ `is_active` của LUỒNG, không phải theo công
                       tắc bộ máy của loại — nói "Đang bật / Đã tắt" cho khớp
                       cái nó thực sự lọc, tránh lẫn với cột Trạng thái. */}
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  <SelectItem value="active">Luồng đang bật</SelectItem>
                  <SelectItem value="inactive">Luồng đã tắt</SelectItem>
                </SelectContent>
              </Select>

              <ConditionalFilter />
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
