import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { TONE_CLASS, type StatusTone } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { contractTypeLabel } from '../config/contract-type-options'
import { useContracts } from '../hooks/use-contracts'
import type { Contract } from '../types/contract'

/**
 * Tình trạng hiệu lực do backend tính. Hết hạn = đỏ, sắp hết = vàng để lọt mắt.
 * B-02: khóa là MÃ (`expired`…), không phải nhãn — đổi chữ hiển thị không làm mất màu.
 */
const EXPIRY_TONE: Record<string, StatusTone> = {
  expired: 'danger',
  expiring_soon: 'pending',
  valid: 'done',
}

/**
 * Hợp đồng đã ký với một nhà cung cấp.
 *
 * Lọc theo `party_code` chứ không theo tên: tên pháp lý đổi là mất sạch hợp đồng
 * cũ, còn mã NCC là khóa duy nhất toàn hệ.
 */
export function SupplierContractsTable({ supplierCode }: { supplierCode: string }) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canRead = can('contract', 'read')

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data, isLoading, isError, refetch } = useContracts(
    { party_code: supplierCode, page, page_size: pageSize },
    { enabled: canRead && Boolean(supplierCode) },
  )

  // Hợp đồng chỉ lưu `company_id`; đổi ra tên bằng danh mục pháp nhân.
  const { data: companies } = useCompanies(
    { page_size: 200, is_active: true },
    { enabled: canRead && can('company', 'read') },
  )
  const companyNames = useMemo(() => {
    const map = new Map<number, string>()
    for (const company of companies?.items ?? []) {
      map.set(company.id, company.short_name || company.name)
    }
    return map
  }, [companies?.items])

  const columns = useMemo<DataTableColumn<Contract>[]>(
    () => [
      {
        key: 'code',
        header: 'Số hợp đồng',
        width: 160,
        hideable: false,
        defaultPinned: true,
        cell: (c) => <span className="font-semibold text-primary">{c.code || '—'}</span>,
      },
      {
        key: 'title',
        header: 'Tên hợp đồng',
        width: 300,
        wrap: true,
        hideable: false,
        cell: (c) => c.title || '—',
      },
      {
        key: 'contract_type',
        header: 'Loại',
        width: 150,
        cell: (c) => contractTypeLabel(c.contract_type) || '—',
      },
      {
        key: 'company_id',
        header: 'Công ty ký',
        width: 200,
        wrap: true,
        cell: (c) => companyNames.get(c.company_id) || '—',
      },
      {
        key: 'start_date',
        header: 'Ngày ký',
        width: 120,
        cell: (c) => formatDate(c.start_date) || '—',
      },
      {
        key: 'end_date',
        header: 'Ngày hết hạn',
        width: 130,
        cell: (c) => formatDate(c.end_date) || '—',
      },
      {
        key: 'expiry',
        header: 'Hiệu lực',
        width: 130,
        cell: (c) =>
          c.expiry ? (
            <Badge variant="secondary" className={cn('border-0', TONE_CLASS[EXPIRY_TONE[c.expiry] ?? 'neutral'])}>
              {c.expiry_label || c.expiry}
            </Badge>
          ) : (
            <span className="text-muted-foreground">Không thời hạn</span>
          ),
      },
      {
        key: 'signed',
        header: 'Đã ký',
        width: 110,
        cell: (c) => (
          <Badge variant={c.signed ? 'default' : 'secondary'}>
            {c.signed ? 'Đã ký' : 'Chưa ký'}
          </Badge>
        ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 140,
        cell: (c) => c.status_label || c.status || '—',
      },
      { key: 'note', header: 'Ghi chú', width: 240, wrap: true, defaultHidden: true, cell: (c) => c.note || '—' },
    ],
    [companyNames],
  )

  if (!canRead) {
    return (
      <Card className="p-10 text-center text-sm text-muted-foreground">
        Tài khoản của bạn chưa được cấp quyền đọc danh mục Hợp đồng.
      </Card>
    )
  }

  return (
    <Card className="p-4">
      <DataTable
        columns={columns}
        rows={data?.items}
        getRowId={(c) => c.id}
        isLoading={isLoading}
        isError={isError}
        onRefresh={() => refetch()}
        onRowClick={(c) => navigate(appRoutes.production.contractDetail(c.id))}
        storageKey="production.supplier.contracts"
        emptyMessage="Chưa có hợp đồng nào với nhà cung cấp này."
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
          unitLabel: 'hợp đồng',
        }}
      />
    </Card>
  )
}
