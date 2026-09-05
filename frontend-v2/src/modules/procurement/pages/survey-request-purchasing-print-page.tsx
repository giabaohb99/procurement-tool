import { ArrowLeft, Printer, X } from 'lucide-react'
import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { useSurveyRequestPurchasingPrint } from '../hooks/use-survey-request'
import { PO_STATUS_LABELS } from '../types/purchase-document'
import type { SurveyRequestPurchasingGroup } from '../types/survey-request-detail'

/**
 * P6-9 (bao-CR-287): bộ bản in của THU MUA — tách theo từng nhà cung cấp, mỗi NCC
 * một trang gồm các dòng ĐÃ CHỐT về NCC đó, trang cuối là danh sách ĐMH đã sinh.
 *
 * Backend (`/print-purchasing`) gác `supplier.read` — người yêu cầu mở là ăn 403
 * và rơi vào ErrorState; nút vào trang này cũng đã ẩn theo `can('supplier','read')`.
 */
export function SurveyRequestPurchasingPrintPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const surveyRequestId = Number(id) || 0
  const { data, isLoading, isError } = useSurveyRequestPurchasingPrint(surveyRequestId)
  const { data: companiesData } = useCompanies({ page_size: 500 })

  useEffect(() => {
    if (!data?.code) return
    const previousTitle = document.title
    document.title = `${data.code} - Bản in theo nhà cung cấp`
    return () => {
      document.title = previousTitle
    }
  }, [data?.code])

  if (isLoading) {
    return (
      <main className="min-h-[100dvh] bg-slate-200 p-5">
        <Skeleton className="mx-auto mb-3 h-10 max-w-[210mm]" />
        <Skeleton className="mx-auto h-[297mm] max-w-[210mm] bg-white" />
      </main>
    )
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Không mở được bản in"
        description="Bản in theo nhà cung cấp dành cho thu mua (cần quyền xem Nhà cung cấp), hoặc phiếu ngoài phạm vi bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.surveyRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  const companyName =
    companiesData?.items?.find((company) => company.id === data.company_id)?.name || ''

  return (
    <main className="srp-print-root min-h-[100dvh] bg-slate-200 p-5 text-slate-950">
      <style>{PRINT_STYLES}</style>

      <div className="srp-print-toolbar">
        <div className="srp-print-toolbar-actions">
          <Button onClick={() => window.print()}>
            <Printer />
            In / Lưu PDF
          </Button>
          <Button variant="outline" onClick={() => window.close()}>
            <X />
            Đóng
          </Button>
        </div>
        <p className="text-sm text-slate-600">
          {data.groups.length} nhà cung cấp · {data.purchase_orders.length} đơn mua hàng đã sinh
        </p>
      </div>

      {data.groups.length === 0 && (
        <article className="srp-print-doc">
          <DocHeader companyName={companyName} code={data.code} requestDate={data.request_date} />
          <p className="mt-6 text-center text-[13px] italic">
            Chưa có dòng nào được người yêu cầu chốt phương án — không có gì để in theo nhà cung
            cấp.
          </p>
        </article>
      )}

      {data.groups.map((group) => (
        <article key={group.supplier_code || group.supplier_name} className="srp-print-doc">
          <DocHeader companyName={companyName} code={data.code} requestDate={data.request_date} />

          <section>
            <h2 className="srp-print-section-title">NHÀ CUNG CẤP</h2>
            <div className="srp-print-section-content">
              <p>
                <b>Tên nhà cung cấp:</b> {group.supplier_name || group.supplier_code}
              </p>
              {group.supplier_code && (
                <p>
                  <b>Mã NCC:</b> {group.supplier_code}
                </p>
              )}
              <p>
                <b>Người yêu cầu:</b> {data.requester} · <b>Bộ phận:</b> {data.department}
              </p>
              <p>
                <b>Mục đích:</b> {data.purpose}
              </p>
            </div>
          </section>

          <SupplierGroupItems group={group} />
        </article>
      ))}

      <article className="srp-print-doc">
        <DocHeader companyName={companyName} code={data.code} requestDate={data.request_date} />

        <section>
          <h2 className="srp-print-section-title">DANH SÁCH ĐƠN MUA HÀNG ĐÃ SINH TỪ PHIẾU</h2>
          {data.purchase_orders.length === 0 ? (
            <p className="srp-print-section-content italic">Chưa sinh đơn mua hàng nào.</p>
          ) : (
            <table className="srp-print-items">
              <colgroup>
                <col style={{ width: '8%' }} />
                <col style={{ width: '25%' }} />
                <col style={{ width: '45%' }} />
                <col style={{ width: '22%' }} />
              </colgroup>
              <thead>
                <tr className="bg-[#e9edf1]">
                  <th>STT</th>
                  <th>Số đơn</th>
                  <th>Nhà cung cấp</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {data.purchase_orders.map((po, index) => (
                  <tr key={po.id}>
                    <td className="text-center">{index + 1}</td>
                    <td>{po.code}</td>
                    <td>{po.supplier_name || po.supplier_code}</td>
                    <td>{PO_STATUS_LABELS[po.status] ?? po.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <p className="srp-print-note">Bản in theo nhà cung cấp — in từ hệ thống thu mua</p>
      </article>
    </main>
  )
}

function DocHeader({
  companyName,
  code,
  requestDate,
}: {
  companyName: string
  code: string
  requestDate: string
}) {
  return (
    <>
      <header className="srp-print-document-header">
        <p className="text-[13px]">
          <b>Đơn vị:</b> {companyName || '...'}
        </p>
      </header>
      <h1 className="srp-print-document-title">YÊU CẦU BÁO GIÁ — BẢN IN THEO NHÀ CUNG CẤP</h1>
      <p className="srp-print-document-code">Số: {code}</p>
      <p className="srp-print-document-date">{formatVietnameseLongDate(requestDate)}</p>
    </>
  )
}

function SupplierGroupItems({ group }: { group: SurveyRequestPurchasingGroup }) {
  const total = group.lines.reduce((sum, line) => sum + line.request_qty * line.chosen_price, 0)

  return (
    <table className="srp-print-items">
      <colgroup>
        <col style={{ width: '5%' }} />
        <col style={{ width: '24%' }} />
        <col style={{ width: '10%' }} />
        <col style={{ width: '7%' }} />
        <col style={{ width: '8%' }} />
        <col style={{ width: '11%' }} />
        <col style={{ width: '7%' }} />
        <col style={{ width: '13%' }} />
        <col style={{ width: '15%' }} />
      </colgroup>
      <thead>
        <tr className="bg-[#e9edf1]">
          <th>STT</th>
          <th>Tên hàng hóa</th>
          <th>Mã hàng</th>
          <th>ĐVT</th>
          <th>Số lượng</th>
          <th>Đơn giá chốt</th>
          <th>VAT</th>
          <th>Thành tiền</th>
          <th>Thời gian giao</th>
        </tr>
      </thead>
      <tbody>
        {group.lines.map((line, index) => (
          <tr key={line.id}>
            <td className="text-center">{index + 1}</td>
            <td>{line.chosen_product_name || line.requirement_detail}</td>
            <td>{line.product_code}</td>
            <td>{line.chosen_quote_unit || line.uom}</td>
            <td className="text-right tabular-nums">{formatQuantity(line.request_qty)}</td>
            <td className="text-right tabular-nums">{formatUnitPrice(line.chosen_price)}</td>
            <td className="text-right tabular-nums">
              {line.chosen_vat ? `${line.chosen_vat}%` : ''}
            </td>
            <td className="text-right tabular-nums">
              {formatMoney(line.request_qty * line.chosen_price)}
            </td>
            <td>{line.chosen_delivery_time}</td>
          </tr>
        ))}
        <tr>
          <td className="font-bold" colSpan={7}>
            Tổng cộng (chưa VAT)
          </td>
          <td className="text-right font-bold tabular-nums">{formatMoney(total)}</td>
          <td />
        </tr>
      </tbody>
    </table>
  )
}

function formatVietnameseLongDate(value: string): string {
  if (!value) return 'Ngày ........ tháng ........ năm ........'
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `Ngày ${day} tháng ${month} năm ${year}`
}

const PRINT_STYLES = `
  .srp-print-root {
    min-height: 100dvh;
    overflow-x: auto;
    padding: 24px;
    background: #e9eef5;
    color: #0f172a;
  }

  .srp-print-toolbar {
    position: sticky;
    top: 16px;
    z-index: 10;
    display: flex;
    width: 210mm;
    max-width: calc(100vw - 48px);
    min-height: 44px;
    margin: 0 auto 16px;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .srp-print-toolbar-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  .srp-print-doc,
  .srp-print-doc * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .srp-print-doc {
    position: relative;
    box-sizing: border-box;
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto 16px;
    padding: 10mm 12mm 18mm;
    font-family: Arial, sans-serif;
    color: #000;
    background: #fff;
    border: 1px solid #d7dde7;
    border-radius: 4px;
    box-shadow: 0 18px 48px rgba(27, 37, 89, 0.14);
  }

  .srp-print-doc p {
    margin-top: 0;
    margin-bottom: 0;
  }

  .srp-print-document-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
  }

  .srp-print-document-title {
    margin: 18px 0 4px;
    text-align: center;
    font-size: 16px;
    font-weight: 700;
    line-height: 1.25;
  }

  .srp-print-document-code,
  .srp-print-document-date {
    text-align: center;
    font-size: 12px;
    line-height: 1.5;
  }

  .srp-print-document-date {
    margin-bottom: 6px !important;
  }

  .srp-print-section-title {
    margin: 12px 0 0;
    padding: 5px 8px;
    background: #e9edf1;
    border-left: 3px solid #1b2559;
    font-size: 12.5px;
    font-weight: 700;
    line-height: 1.35;
    break-after: avoid;
    page-break-after: avoid;
  }

  .srp-print-section-content {
    padding: 6px 4px;
    font-size: 12px;
    line-height: 1.7;
  }

  .srp-print-items {
    width: 100%;
    margin-top: 6px;
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 11px;
  }

  .srp-print-items th,
  .srp-print-items td {
    border: 1px solid #999;
    padding: 5px 6px;
    vertical-align: middle;
    overflow-wrap: anywhere;
  }

  .srp-print-items th {
    background: #e9edf1;
    font-weight: 700;
    text-align: center;
    line-height: 1.3;
  }

  .srp-print-items tr {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .srp-print-note {
    position: absolute;
    right: 12mm;
    bottom: 7mm;
    color: #737373;
    font-size: 8px;
    font-style: italic;
  }

  @media print {
    @page {
      size: A4 portrait;
      margin: 0;
    }

    html,
    body,
    #root {
      margin: 0 !important;
      min-height: 0 !important;
      background: #fff !important;
    }

    .srp-print-root {
      min-height: 0 !important;
      padding: 0 !important;
      background: #fff !important;
    }

    .srp-print-toolbar {
      display: none !important;
    }

    .srp-print-doc {
      width: 210mm !important;
      max-width: none !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 10mm 12mm 18mm !important;
      box-shadow: none !important;
      border: 0 !important;
      border-radius: 0 !important;
      -webkit-box-decoration-break: clone;
      box-decoration-break: clone;
    }

    /* Mỗi NCC một trang riêng — phiếu sau bắt đầu ở trang mới. */
    .srp-print-doc + .srp-print-doc {
      break-before: page;
      page-break-before: always;
    }

    .srp-print-items thead {
      display: table-header-group;
    }

    .srp-print-note {
      position: static !important;
      margin-top: 12px !important;
      text-align: right;
    }
  }

  @media screen and (max-width: 850px) {
    .srp-print-root {
      padding: 12px;
    }

    .srp-print-toolbar,
    .srp-print-doc {
      min-width: 210mm;
    }

    .srp-print-toolbar {
      position: static;
      max-width: none;
    }
  }
`
