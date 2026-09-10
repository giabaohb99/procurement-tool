import { Printer, X } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import {
  LANDED_COST_TABLE_STYLES,
  LandedCostItemTable,
  LandedCostPivotTable,
  LandedCostSignatures,
  LandedCostWarnings,
} from '../components/import-landed-cost-tables'
import { useImportLandedCost } from '../hooks/use-purchase-report'
import {
  landedCostViewLabel,
  type LandedCostParams,
  type LandedCostView,
} from '../types/import-landed-cost'

/**
 * Bản in BÁO CÁO GIÁ VỐN LÔ HÀNG NHẬP KHẨU (bao-CR-357, dời từ bản v1).
 *
 * Khổ **A4 NẰM NGANG** — khác mọi bản in còn lại của hệ: bảng xoay có mỗi lô hàng
 * một cột, khổ dọc chỉ lọt hai lô là tràn.
 *
 * Bộ lọc đi qua query string (`codes` / `date_from` / `date_to` / `company_id` /
 * `view`) chứ không qua id, vì báo cáo này không gắn với MỘT chứng từ nào.
 */
export function ImportLandedCostPrintPage() {
  const [searchParams] = useSearchParams()
  const { can } = usePermission()

  const view: LandedCostView = searchParams.get('view') === 'items' ? 'items' : 'orders'
  const codes = searchParams.get('codes') || ''
  const dateFrom = searchParams.get('date_from') || ''
  const dateTo = searchParams.get('date_to') || ''
  const companyId = searchParams.get('company_id') || ''

  const params = useMemo<LandedCostParams>(() => {
    const next: LandedCostParams = {}
    if (codes) next.codes = codes
    else {
      if (dateFrom) next.date_from = dateFrom
      if (dateTo) next.date_to = dateTo
    }
    if (companyId) next.company_id = companyId
    return next
  }, [codes, dateFrom, dateTo, companyId])

  const { data, isLoading, isError } = useImportLandedCost(params)
  //  Chỉ hỏi danh sách công ty khi thật sự cần TÊN của một công ty cụ thể, và chỉ
  //  khi có quyền đọc — không thì người in ăn 403 ngay lúc mở bản in.
  const { data: companies } = useCompanies(
    { page_size: 500, is_active: true },
    { enabled: !!companyId && can('company', 'read') },
  )
  const companyName = companies?.items.find((item) => String(item.id) === companyId)?.name || ''

  useEffect(() => {
    const previousTitle = document.title
    document.title = `Bao-cao-gia-von-nhap-khau${dateFrom ? `-${dateFrom.replace(/-/g, '')}` : ''}`
    return () => {
      document.title = previousTitle
    }
  }, [dateFrom])

  const scopeLabel = codes
    ? `Mã đơn: ${codes}`
    : `Ngày đặt: ${formatDate(dateFrom) || '...'} — ${formatDate(dateTo) || '...'}`

  return (
    <main className="po-print-root min-h-[100dvh] bg-slate-200 p-6 text-slate-950">
      <style>{LANDED_COST_TABLE_STYLES}</style>
      <style>{PRINT_STYLES}</style>

      <div className="no-print mx-auto mb-3 flex max-w-[1100px] flex-wrap items-center gap-2">
        <Button onClick={() => window.print()}>
          <Printer />
          In / Lưu PDF
        </Button>
        <Button variant="outline" onClick={() => window.close()}>
          <X />
          Đóng
        </Button>
      </div>

      <article className="po-print-doc lc-print-doc">
        <header className="lc-print-header">
          {companyName && <div className="lc-print-company">{companyName}</div>}
          <h1 className="lc-print-title">BÁO CÁO GIÁ VỐN LÔ HÀNG NHẬP KHẨU</h1>
          <div className="lc-print-subtitle">
            {scopeLabel} · {landedCostViewLabel(view)} · Lập ngày {formatDate(new Date())}
          </div>
        </header>

        {isLoading && <Skeleton className="h-[120mm] w-full" />}

        {isError && (
          <p className="py-10 text-center text-sm">
            Không tải được số liệu — có thể bạn không có quyền xem báo cáo này.
          </p>
        )}

        {data && !isLoading && (
          <>
            {view === 'orders' ? (
              <LandedCostPivotTable data={data} compact />
            ) : (
              <LandedCostItemTable data={data} compact />
            )}
            <div className="mt-3">
              <LandedCostWarnings data={data} />
            </div>
            <LandedCostSignatures />
          </>
        )}
      </article>
    </main>
  )
}

const PRINT_STYLES = `
  .po-print-doc {
    margin: 0 auto;
    background: #fff;
    color: #000;
    font-family: Arial, Helvetica, sans-serif;
    padding: 24px 30px;
  }
  .lc-print-doc { max-width: 1100px; }
  .lc-print-header { border-bottom: 2px solid #1a4d6b; padding-bottom: 8px; margin-bottom: 12px; }
  .lc-print-company { font-size: 12px; font-weight: 700; }
  .lc-print-title { font-size: 17px; font-weight: 700; text-align: center; color: #1a4d6b; }
  .lc-print-subtitle { font-size: 11.5px; text-align: center; margin-top: 2px; }

  @media print {
    @page { size: A4 landscape; margin: 0; }
    html, body { margin: 0 !important; background: #fff !important; }
    .no-print { display: none !important; }
    .po-print-root { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
    .po-print-doc { max-width: none !important; padding: 8mm 10mm !important; }
    .lc-table { break-inside: auto; }
    .lc-table tr { break-inside: avoid; }
  }
`
