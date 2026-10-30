// duoc-CR-630 — màn "Danh sách biến" của mẫu hợp đồng lao động: xem 48 biến hệ thống, thêm / sửa /
// ngừng dùng / xóa biến TÙY CHỈNH (nhập tay theo từng hợp đồng). Trang riêng (không hộp thoại) vì bảng
// dài + bộ lọc + hộp sửa lồng nhau; nằm dưới `/hr/labor-contract-templates` nên chung hàng rào quyền.
import { ArrowLeft, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { LABOR_CONTRACT_VARIABLE_SOURCE, LABOR_CONTRACT_VARIABLE_TYPE } from '@/shared/constants/statuses'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { LaborContractVariableFormDialog } from '../components/labor-contract-variable-form-dialog'
import { buildLaborContractVariableColumns } from '../config/labor-contract-variable-columns'
import {
  useDeleteLaborContractVariable,
  useLaborContractVariables,
  useUpdateLaborContractVariable,
} from '../hooks/use-labor-contract-variables'
import type { LaborContractVariable } from '../types/labor-contract-variable'

const ALL = 'all'

export function LaborContractVariablesPage() {
  const { can } = usePermission()
  const canRead = can('labor_contract_template', 'read')
  const navigate = useNavigate()

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam('q')
  const [source, setSource] = useUrlParamState('source', ALL)
  const [valueType, setValueType] = useUrlParamState('value_type', ALL)
  const [active, setActive] = useUrlParamState('is_active', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  //  `undefined` = đóng · `null` = THÊM mới · biến = SỬA.
  const [editing, setEditing] = useState<LaborContractVariable | null | undefined>(undefined)
  const [page, setPage] = usePageResetOnFilterChange([debouncedValue, source, valueType, active])

  const params: ListParams = { page, page_size: pageSize }
  if (debouncedValue) params.q = debouncedValue
  if (source !== ALL) params.source = Number(source)
  if (valueType !== ALL) params.value_type = Number(valueType)
  if (active !== ALL) params.is_active = active === 'true'

  const { data, isLoading, isError } = useLaborContractVariables(params, { enabled: canRead })
  const update = useUpdateLaborContractVariable()
  const remove = useDeleteLaborContractVariable()
  const canManage = data?.can_manage ?? false
  const canDelete = data?.can_delete ?? false

  const columns = useMemo(
    () =>
      buildLaborContractVariableColumns({
        canManage,
        canDelete,
        onEdit: setEditing,
        //  Danh mục dùng chung mọi pháp nhân: đổi trạng thái là ảnh hưởng ô nhập / khung chèn biến của mọi HR → hỏi lại.
        onToggleActive: async (v) => {
          const stopping = v.is_active
          const ok = await confirm({
            title: stopping ? 'Ngừng dùng biến' : 'Bật lại biến',
            message: stopping
              ? `Ngừng dùng biến "${v.label}"? Biến biến mất khỏi ô nhập và khung "Chèn biến"; mẫu mới không nhận được biến này. Mẫu cũ và giá trị đã nhập vẫn giữ nguyên.`
              : `Bật lại biến "${v.label}"? Biến hiện lại ở ô nhập hợp đồng và khung "Chèn biến".`,
            confirmLabel: stopping ? 'Ngừng dùng' : 'Bật lại',
          })
          if (ok) update.mutate({ id: v.id, payload: { is_active: !v.is_active } })
        },
        onToggleHidden: async (v) => {
          const hiding = !v.is_hidden
          const ok = await confirm({
            title: hiding ? 'Ẩn biến khỏi danh sách' : 'Hiện lại biến',
            message: hiding
              ? `Ẩn biến "${v.label}" khỏi khung "Chèn biến"? Biến vẫn dùng được trong mẫu.`
              : `Hiện lại biến "${v.label}" ở khung "Chèn biến"?`,
            confirmLabel: hiding ? 'Ẩn' : 'Hiện',
          })
          if (ok) update.mutate({ id: v.id, payload: { is_hidden: hiding } })
        },
        onDelete: async (v) => {
          const ok = await confirm({
            title: 'Xóa biến',
            message: `Xóa biến "${v.label}"? Biến đang dùng trong mẫu hoặc đã có hợp đồng nhập giá trị sẽ không xóa được, khi đó hãy chọn "Ngừng dùng".`,
            confirmLabel: 'Xóa',
          })
          //  Lỗi 409 (đang dùng) đã được http-client toast đúng câu của backend (số mẫu / hợp đồng).
          if (ok) remove.mutate(v.id)
        },
      }),
    // `mutate` ổn định; không đưa cả object mutation vào deps kẻo bảng dựng lại mỗi lượt.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [canManage, canDelete],
  )

  if (!canRead) {
    return (
      <PageContainer>
        <PageHeader title="Danh sách biến" description="Bạn không có quyền xem màn này." />
      </PageContainer>
    )
  }

  const isFiltering = Boolean(debouncedValue) || source !== ALL || valueType !== ALL || active !== ALL

  return (
    <PageContainer fill className="flex flex-col gap-3">
      <PageHeader
        leading={
          <Button type="button" variant="ghost" size="icon" aria-label="Quay lại Mẫu hợp đồng"
            onClick={() =>
              //  Về đúng trang trước (Nhân sự HAY Thiết lập văn bản); mở thẳng URL thì về trang mẫu của Nhân sự.
              (window.history.state as { idx?: number } | null)?.idx
                ? navigate(-1)
                : navigate(appRoutes.hr.laborContractTemplates)
            }>
            <ArrowLeft className="size-4" />
          </Button>
        }
        title="Danh sách biến mẫu hợp đồng"
        description={
          <>
            Gõ biến vào tệp Word đúng dạng <code>{'{{ ten_bien }}'}</code>. Biến hệ thống lấy giá trị từ hồ sơ; biến
            tùy chỉnh nhập tay theo từng hợp đồng.
            {!canManage && ' Chỉ người có phạm vi "tất cả pháp nhân" mới thêm, sửa, xóa được biến.'}
          </>
        }
        actions={
          canManage && (
            <Button type="button" onClick={() => setEditing(null)}>
              <Plus className="size-4" />
              Thêm biến
            </Button>
          )
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(v) => v.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            isFiltering ? 'Không có biến nào khớp bộ lọc.' : 'Chưa có biến tùy chỉnh. Bấm "Thêm biến".'
          }
          storageKey="hr.labor-contract-variables"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'biến',
          }}
          toolbar={
            <>
              <SearchField value={keyword} onChange={setKeyword} placeholder="Tìm theo mã hoặc tên biến…"
                className="md:w-64 md:max-w-sm md:flex-none" />
              <Select value={source} onValueChange={setSource}>
                <SelectTrigger className="w-44" aria-label="Lọc theo nguồn"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả nguồn</SelectItem>
                  {LABOR_CONTRACT_VARIABLE_SOURCE.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={valueType} onValueChange={setValueType}>
                <SelectTrigger className="w-44" aria-label="Lọc theo kiểu"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả kiểu</SelectItem>
                  {LABOR_CONTRACT_VARIABLE_TYPE.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={active} onValueChange={setActive}>
                <SelectTrigger className="w-44" aria-label="Lọc theo trạng thái"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  <SelectItem value="true">Đang dùng</SelectItem>
                  <SelectItem value="false">Ngừng</SelectItem>
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
      <LaborContractVariableFormDialog
        open={editing !== undefined}
        onOpenChange={(next) => !next && setEditing(undefined)}
        variable={editing ?? null}
      />
    </PageContainer>
  )
}
