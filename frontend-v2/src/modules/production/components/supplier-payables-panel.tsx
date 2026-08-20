import { AlertTriangle, BadgeCheck, Clock, FileSignature, Truck, Wallet } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { PayableAgingBadge, PayableStatusBadge } from '@/modules/finance/components/payable-badges'
import { usePayableSummary, usePayables } from '@/modules/finance/hooks/use-payables'
import { PAYABLE_SOURCE_LABELS, type Payable } from '@/modules/finance/types/payable'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { StatCard } from '@/shared/ui/stat-card'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatPercent } from '@/shared/utils/format-money'
import { useContracts } from '../hooks/use-contracts'
import { useSupplierKpi } from '../hooks/use-supplier-kpi'
import type { Supplier } from '../types/supplier'

/** Cả kỳ. Sổ nợ của một NCC mà bó theo năm thì người đi đòi nợ đọc ra số sai. */
const ALL_YEARS = 'all'

/**
 * Tab "Công nợ & Đánh giá" của trang chi tiết NCC.
 *
 * Hai khối tách bạch có chủ ý:
 *  - ĐÁNH GIÁ (KPI giao hàng) tính trên TOÀN BỘ lịch sử giao hàng;
 *  - CÔNG NỢ là sổ nợ còn treo.
 * Cho hai khối ăn chung một bộ lọc là ra số sai: lọc "nợ quá hạn" xong nhìn sang
 * tỷ lệ giao trễ sẽ tưởng đó là tỷ lệ của riêng mấy đơn quá hạn.
 */
export function SupplierPayablesPanel({ supplier }: { supplier: Supplier }) {
  const { can } = usePermission()

  const { data: kpi, isLoading: isKpiLoading } = useSupplierKpi(supplier.name, {
    enabled: can('report', 'read'),
  })

  // Chỉ cần con số tổng, không cần dòng nào -> xin đúng 1 dòng cho nhẹ.
  const { data: contracts } = useContracts(
    { party_code: supplier.code, page_size: 1 },
    { enabled: can('contract', 'read') && Boolean(supplier.code) },
  )

  return (
    <div className="space-y-4">
      <Card className="gap-3 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold text-navy dark:text-foreground">
            Đánh giá nhà cung cấp
          </h3>
          <span className="text-xs text-muted-foreground">
            · tính trên toàn bộ lịch sử giao hàng, không theo bảng công nợ bên dưới
          </span>
          {kpi?.warn && (
            <Badge variant="secondary" className="border-0 bg-destructive/10 text-destructive">
              <AlertTriangle className="size-3.5" />
              Tỷ lệ giao trễ cao (trên 30%)
            </Badge>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={Truck}
            label="Số lần giao dịch"
            value={kpi ? kpi.trans.toLocaleString('vi-VN') : '—'}
            loading={isKpiLoading}
          />
          <StatCard
            icon={Clock}
            label="Số lần giao trễ"
            value={kpi ? kpi.late.toLocaleString('vi-VN') : '—'}
            loading={isKpiLoading}
            tone={kpi && kpi.late > 0 ? 'warning' : undefined}
            hint={kpi && kpi.late > 0 ? 'So với ngày quy định trên đơn' : undefined}
          />
          <StatCard
            icon={BadgeCheck}
            label="Tỷ lệ trễ"
            value={kpi ? formatPercent(kpi.rate) : '—'}
            loading={isKpiLoading}
            tone="danger"
            hint={kpi?.warn ? 'Vượt ngưỡng cảnh báo 30%' : undefined}
          />
          <StatCard icon={FileSignature} label="Số hợp đồng" value={contracts?.total ?? '—'} />
        </div>

        {!isKpiLoading && !kpi && (
          <p className="text-xs text-muted-foreground">
            Chưa ghi nhận lần giao hàng nào của nhà cung cấp này.
          </p>
        )}
      </Card>

      {/*
        Tách hẳn thành component con để KHÔNG gọi `/api/payables` khi thiếu quyền:
        hook không có nhánh tắt, gọi là người dùng ăn ngay một toast 403 lúc mở tab.
      */}
      {can('payable', 'read') ? (
        <SupplierPayablesBlock supplierCode={supplier.code} />
      ) : (
        <Card className="p-10 text-center text-sm text-muted-foreground">
          Tài khoản của bạn chưa được cấp quyền đọc Công nợ phải trả.
        </Card>
      )}
    </div>
  )
}

function SupplierPayablesBlock({ supplierCode }: { supplierCode: string }) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canOpenOrder = can('purchase_order', 'read')

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  // Bốn ô tổng phải tính trên CẢ tập kết quả nên không nhận tham số phân trang.
  const filterParams = { supplier_code: supplierCode, year: ALL_YEARS }
  const { data, isLoading, isError, refetch } = usePayables({
    ...filterParams,
    page,
    page_size: pageSize,
  })
  const { data: summary, isLoading: isSummaryLoading } = usePayableSummary(filterParams)

  const columns = useMemo<DataTableColumn<Payable>[]>(
    () => [
      {
        key: 'po_code',
        header: 'Mã ĐMH',
        width: 150,
        hideable: false,
        defaultPinned: true,
        cell: (p) => <span className="font-semibold text-primary">{p.po_code || '—'}</span>,
      },
      {
        key: 'source_type',
        header: 'Loại nợ',
        width: 120,
        cell: (p) => PAYABLE_SOURCE_LABELS[p.source_type] ?? p.source_type,
      },
      {
        key: 'invoice_no',
        header: 'Số hóa đơn',
        width: 150,
        // Chưa có số HĐ = chưa lên được yêu cầu thanh toán. Phải nhìn ra ngay chứ
        // không để trống như một ô rỗng bình thường.
        cell: (p) => p.invoice_no || <span className="text-xs text-destructive">chưa có HĐ</span>,
      },
      {
        key: 'incur_date',
        header: 'Ngày phát sinh',
        width: 130,
        cell: (p) => formatDate(p.incur_date) || '—',
      },
      { key: 'due_date', header: 'Hạn trả', width: 120, cell: (p) => formatDate(p.due_date) || '—' },
      {
        key: 'aging',
        header: 'Tuổi nợ',
        width: 140,
        cell: (p) => <PayableAgingBadge aging={p.aging} />,
      },
      {
        key: 'total',
        header: 'Tổng nợ',
        width: 150,
        align: 'right',
        cell: (p) => <span className="tabular-nums">{formatMoney(p.total)}</span>,
      },
      {
        key: 'paid_amount',
        header: 'Đã trả',
        width: 150,
        align: 'right',
        cell: (p) => <span className="tabular-nums">{formatMoney(p.paid_amount)}</span>,
      },
      {
        key: 'remaining',
        header: 'Còn lại',
        width: 150,
        align: 'right',
        cell: (p) => <span className="font-semibold tabular-nums">{formatMoney(p.remaining)}</span>,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 170,
        cell: (p) => <PayableStatusBadge status={p.status} />,
      },
    ],
    [],
  )

  return (
    <>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Wallet}
          label="Tổng nợ"
          value={formatMoney(summary?.total ?? 0)}
          loading={isSummaryLoading}
        />
        <StatCard
          icon={Wallet}
          label="Đã trả"
          value={formatMoney(summary?.paid ?? 0)}
          loading={isSummaryLoading}
        />
        <StatCard
          icon={Wallet}
          label="Còn phải trả"
          value={formatMoney(summary?.remaining ?? 0)}
          loading={isSummaryLoading}
        />
        <StatCard
          icon={AlertTriangle}
          label="Quá hạn"
          value={formatMoney(summary?.overdue ?? 0)}
          loading={isSummaryLoading}
          tone={(summary?.overdue ?? 0) > 0 ? 'danger' : undefined}
        />
      </div>

      <Card className="p-4">
        <DataTable
          columns={columns}
          rows={data?.items}
          getRowId={(p) => p.id}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          storageKey="production.supplier.payables"
          emptyMessage="Nhà cung cấp này chưa phát sinh khoản công nợ nào."
          onRowClick={
            canOpenOrder
              ? (p) => {
                  if (p.po_id > 0) navigate(appRoutes.procurement.purchaseOrderDetail(p.po_id))
                }
              : undefined
          }
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'khoản',
          }}
        />
      </Card>
    </>
  )
}
