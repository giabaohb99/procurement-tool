import { BookOpen, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { LABOR_CONTRACT_TYPE } from '@/shared/constants/statuses'
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
import { laborContractTemplateApi } from '../api/labor-contract-template-api'
import { LaborContractPlaceholderGuideDialog } from '../components/labor-contract-placeholder-guide-dialog'
import { LaborContractTemplateEditDialog } from '../components/labor-contract-template-edit-dialog'
import { LaborContractTemplateUploadDialog } from '../components/labor-contract-template-upload-dialog'
import { buildLaborContractTemplateColumns } from '../config/labor-contract-template-columns'
import { useCompanies } from '../hooks/use-companies'
import {
  useDeleteLaborContractTemplate,
  useLaborContractTemplates,
  useUpdateLaborContractTemplate,
} from '../hooks/use-labor-contract-templates'
import type { LaborContractTemplate } from '../types/labor-contract'

const ALL = 'all'

/**
 * MẪU HỢP ĐỒNG LAO ĐỘNG theo pháp nhân (.docx).
 * Quyền thật do backend gác; ở đây ẩn nút theo `can()` và tự chặn khi thiếu quyền đọc.
 */
export function LaborContractTemplateListPage() {
  const { can } = usePermission()
  const canRead = can('labor_contract_template', 'read')
  const canCreate = can('labor_contract_template', 'create')
  const canWrite = can('labor_contract_template', 'write')
  const canDelete = can('labor_contract_template', 'delete')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam('q')
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [contractType, setContractType] = useUrlParamState('contract_type', ALL)
  const [active, setActive] = useUrlParamState('is_active', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [guideOpen, setGuideOpen] = useState(false)
  const [replacing, setReplacing] = useState<LaborContractTemplate | null>(null)
  const [editing, setEditing] = useState<LaborContractTemplate | null>(null)
  const navigate = useNavigate()

  const [page, setPage] = usePageResetOnFilterChange([debouncedValue, companyId, contractType, active])

  const params: ListParams = { page, page_size: pageSize }
  if (debouncedValue) params.q = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (contractType !== ALL) params.contract_type = Number(contractType)
  if (active !== ALL) params.is_active = active === 'true'

  const { data, isLoading, isError } = useLaborContractTemplates(params, { enabled: canRead })
  const { data: companies } = useCompanies({ page_size: 200 }, { enabled: canRead })
  const update = useUpdateLaborContractTemplate()
  const remove = useDeleteLaborContractTemplate()

  const columns = useMemo(
    () =>
      buildLaborContractTemplateColumns({
        canWrite,
        canDelete,
        onDownload: (t) =>
          void laborContractTemplateApi.download(t).catch((e: unknown) => toast.error(extractErrorMessage(e))),
        onEditContent: (t) => navigate(appRoutes.hr.laborContractTemplateEditor(t.id)),
        onEditInfo: setEditing,
        onReplaceFile: setReplacing,
        onToggleActive: (t) => update.mutate({ id: t.id, payload: { is_active: !t.is_active } }),
        onDelete: async (t) => {
          const ok = await confirm({
            title: 'Xóa mẫu hợp đồng',
            message: `Xóa mẫu «${t.name}»? Hợp đồng đã sinh từ mẫu này vẫn giữ nguyên. Mẫu đã có hợp đồng tham chiếu sẽ không xóa được, khi đó hãy chọn «Ngừng dùng».`,
            confirmLabel: 'Xóa',
          })
          //  Lỗi 409 (đang có HĐ dùng) đã được http-client toast đúng câu của backend.
          if (ok) remove.mutate(t.id)
        },
      }),
    // `mutate` ổn định; không đưa cả object mutation vào deps kẻo bảng dựng lại mỗi lượt.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [canWrite, canDelete],
  )

  if (!canRead) {
    return (
      <PageContainer>
        <PageHeader title="Mẫu hợp đồng" description="Bạn không có quyền xem màn này." />
      </PageContainer>
    )
  }

  const isFiltering =
    Boolean(debouncedValue) || companyId !== ALL || contractType !== ALL || active !== ALL

  return (
    <PageContainer fill>
      <PageHeader
        title="Mẫu hợp đồng"
        description="Mẫu Word (.docx) lập hợp đồng lao động của từng pháp nhân."
        actions={
          <div className="flex gap-2 max-md:w-full">
            <Button type="button" variant="outline" onClick={() => setGuideOpen(true)}>
              <BookOpen className="size-4" />
              Danh sách biến
            </Button>
            {canCreate && (
              <Button type="button" onClick={() => setUploadOpen(true)}>
                <Plus className="size-4" />
                Tải lên mẫu
              </Button>
            )}
          </div>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(t) => t.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            isFiltering
              ? 'Không có mẫu nào khớp bộ lọc.'
              : 'Chưa có mẫu hợp đồng nào. Bấm «Tải lên mẫu» để thêm.'
          }
          storageKey="hr.labor-contract-templates"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'mẫu',
          }}
          toolbar={
            <>
              <SearchField value={keyword} onChange={setKeyword} placeholder="Tìm theo tên mẫu…"
                className="md:w-64 md:max-w-sm md:flex-none" />
              <Select value={companyId} onValueChange={setCompanyId}>
                <SelectTrigger className="w-48" aria-label="Lọc theo pháp nhân"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả pháp nhân</SelectItem>
                  {(companies?.items ?? []).map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>{`${c.issue_code || c.code} — ${c.name}`}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={contractType} onValueChange={setContractType}>
                <SelectTrigger className="w-48" aria-label="Lọc theo loại hợp đồng"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại HĐ</SelectItem>
                  {LABOR_CONTRACT_TYPE.map((o) => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={active} onValueChange={setActive}>
                <SelectTrigger className="w-44" aria-label="Lọc theo trạng thái dùng"><SelectValue /></SelectTrigger>
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

      <LaborContractTemplateUploadDialog open={uploadOpen} onOpenChange={setUploadOpen} />
      <LaborContractTemplateUploadDialog
        open={replacing !== null}
        onOpenChange={(next) => !next && setReplacing(null)}
        replacing={replacing}
      />
      <LaborContractTemplateEditDialog template={editing} onOpenChange={(next) => !next && setEditing(null)} />
      <LaborContractPlaceholderGuideDialog open={guideOpen} onOpenChange={setGuideOpen} />
    </PageContainer>
  )
}
