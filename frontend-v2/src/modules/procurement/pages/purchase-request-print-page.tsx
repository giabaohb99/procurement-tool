import { ArrowLeft, Printer, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { usePurchaseRequest } from '../hooks/use-purchase-request'
import { usePurchaseRequestPrintWarehouses } from '../hooks/use-purchase-request-support'
import type { PurchaseRequestDetail, PurchaseRequestItem } from '../types/purchase-request-detail'

/**
 * Mẫu in 003/BM/PKT của Phiếu đề xuất mua hàng hóa/dịch vụ.
 *
 * Route này nằm ngoài ModuleLayout để bản in không mang theo menu và topbar.
 * Bố cục, dữ liệu và hai chế độ Mẫu thường/Mẫu thuế được giữ theo frontend v1.
 */
export function PurchaseRequestPrintPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const purchaseRequestId = Number(id)
  const { data: purchaseRequest, isLoading, isError } = usePurchaseRequest(purchaseRequestId)
  const { data: warehouses } = usePurchaseRequestPrintWarehouses()
  const [taxMode, setTaxMode] = useState(false)
  const [showSignature, setShowSignature] = useState(true)

  useEffect(() => {
    if (!purchaseRequest?.code) return
    const previousTitle = document.title
    document.title = `${purchaseRequest.code} - Phiếu đề xuất mua hàng`
    return () => {
      document.title = previousTitle
    }
  }, [purchaseRequest?.code])

  const warehouseCodes = useMemo(
    () => new Map((warehouses?.items ?? []).map((warehouse) => [warehouse.name, warehouse.code])),
    [warehouses?.items],
  )

  if (isLoading) {
    return (
      <main className="min-h-[100dvh] bg-slate-200 p-5">
        <Skeleton className="mx-auto mb-3 h-10 max-w-[210mm]" />
        <Skeleton className="mx-auto h-[297mm] max-w-[210mm] bg-white" />
      </main>
    )
  }

  if (isError || !purchaseRequest) {
    return (
      <ErrorState
        title="Không mở được bản in"
        description="Phiếu có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.purchaseRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  function closePrintPage() {
    window.close()
  }

  const supplier = hasSupplierData(purchaseRequest.supplier_pur)
    ? purchaseRequest.supplier_pur
    : purchaseRequest.supplier_req

  return (
    <main className="pr-print-root min-h-[100dvh] bg-slate-200 p-5 text-slate-950">
      <style>{PRINT_STYLES}</style>

      <div className="pr-print-toolbar">
        <div className="pr-print-toolbar-actions">
          <Button onClick={() => window.print()}>
            <Printer />
            In / Lưu PDF
          </Button>
          <Button variant="outline" onClick={closePrintPage}>
            <X />
            Đóng
          </Button>
        </div>

        <div className="pr-print-toolbar-options">
          {!taxMode && (
            <PrintToggle
              options={[
                { value: true, label: 'Có chữ ký' },
                { value: false, label: 'Không chữ ký' },
              ]}
              value={showSignature}
              onChange={setShowSignature}
            />
          )}
          <PrintToggle
            options={[
              { value: false, label: 'Mẫu thường' },
              { value: true, label: 'Mẫu thuế' },
            ]}
            value={taxMode}
            onChange={setTaxMode}
          />
        </div>
      </div>

      <article className="pr-print-doc">
        <header className="pr-print-document-header">
          <p className="text-[13px]">
            <b>Đơn vị:</b> {purchaseRequest.company_name || '...'}
          </p>
          <DocumentVersionTable />
        </header>

        <h1 className="pr-print-document-title">
          PHIẾU ĐỀ XUẤT MUA HÀNG HÓA/DỊCH VỤ
        </h1>
        <p className="pr-print-document-code">Số: {purchaseRequest.code}</p>
        <p className="pr-print-document-date">
          {formatVietnameseLongDate(purchaseRequest.request_date)}
        </p>

        <PrintSection title="THÔNG TIN CHUNG">
          <PrintLine label="Người đề xuất" value={taxMode ? '' : purchaseRequest.requester} />
          <PrintLine
            label="Chức vụ"
            value={taxMode ? '' : purchaseRequest.requester_position || '............'}
          />
          <PrintLine
            label="Hiện công tác tại bộ phận"
            value={taxMode ? '' : purchaseRequest.department || '............'}
          />
          <PrintLine
            label="Trưởng phòng ban/bộ phận"
            value={taxMode ? '' : purchaseRequest.head_of_dept || '............'}
          />
        </PrintSection>

        <PrintSection title="MỤC ĐÍCH & NỘI DUNG ĐỀ XUẤT">
          <PrintLine
            label="Mục đích mua hàng/dịch vụ"
            value={`${purchaseRequest.is_urgent ? '[Gấp] ' : ''}${purchaseRequest.purpose || ''}`}
          />
          <PrintLine
            label="Thời gian cần hàng/dịch vụ"
            value={
              getClosestNeedDate(purchaseRequest.items) ||
              formatShortDate(purchaseRequest.need_date) ||
              '...'
            }
          />
          <PrintLine label="Nội dung" value={purchaseRequest.note} />
        </PrintSection>

        <PurchaseRequestPrintItems
          purchaseRequest={purchaseRequest}
          warehouseCode={(name) => warehouseCodes.get(name) || name}
        />

        <PrintSection title="NHÀ CUNG CẤP DO BỘ PHẬN ĐỀ XUẤT">
          <PrintLine label="Tên nhà cung cấp" value={supplier.name || 'Nhà cung cấp tối ưu nhất'} />
          <PrintLine label="Mã số thuế" value={supplier.tax_code} />
          <PrintLine label="Liên hệ" value={supplier.contact} />
          <PrintLine
            label="Báo giá đính kèm"
            value={purchaseRequest.quote_file_url ? '☑ Có     ☐ Không' : '☐ Có     ☑ Không'}
          />
        </PrintSection>

        <PrintSection title="PHẦN DÀNH CHO BỘ PHẬN MUA HÀNG">
          <PrintLine label="Thời gian cần hàng/dịch vụ" value="............................." />
          <PrintLine label="Yêu cầu khác (nếu có)" value="............................." />
        </PrintSection>

        <SignatureSection
          purchaseRequest={purchaseRequest}
          taxMode={taxMode}
          showSignature={showSignature}
        />

        <p className="pr-print-note">
          Phiếu đề xuất này được in từ hệ thống thu mua
        </p>
      </article>
    </main>
  )
}

function DocumentVersionTable() {
  return (
    <table className="w-[126px] border-collapse text-left text-[7.5px] leading-tight">
      <tbody>
        <tr>
          <td className="border border-neutral-500 px-1 text-center font-bold" colSpan={2}>
            Mẫu 003/BM/PKT
          </td>
        </tr>
        <tr>
          <td className="w-11 whitespace-nowrap border border-neutral-500 px-1">Phiên bản</td>
          <td className="whitespace-nowrap border border-neutral-500 px-1 text-center">V1-062025</td>
        </tr>
        <tr>
          <td className="w-11 whitespace-nowrap border border-neutral-500 px-1">Ngày update:</td>
          <td className="whitespace-nowrap border border-neutral-500 px-1 text-center">17/7/2025</td>
        </tr>
      </tbody>
    </table>
  )
}

function PrintSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="pr-print-section-title">
        {title}
      </h2>
      <div className="pr-print-section-content">{children}</div>
    </section>
  )
}

function PrintLine({ label, value }: { label: string; value?: React.ReactNode }) {
  return (
    <p>
      <b>{label}:</b> {value || ''}
    </p>
  )
}

function PurchaseRequestPrintItems({
  purchaseRequest,
  warehouseCode,
}: {
  purchaseRequest: PurchaseRequestDetail
  warehouseCode: (name: string) => string
}) {
  return (
    <table className="pr-print-items">
      <colgroup>
        <col className="pr-print-col-number" />
        <col className="pr-print-col-name" />
        <col className="pr-print-col-code" />
        <col className="pr-print-col-unit" />
        <col className="pr-print-col-quantity" />
        <col className="pr-print-col-price" />
        <col className="pr-print-col-total" />
        <col className="pr-print-col-place" />
        <col className="pr-print-col-note" />
      </colgroup>
      <thead>
        <tr className="bg-[#e9edf1]">
          <th>STT</th>
          <th>Tên hàng hóa/dịch vụ</th>
          <th>Mã hàng</th>
          <th>ĐVT</th>
          <th>Số lượng</th>
          <th>Đơn giá</th>
          <th>Thành tiền</th>
          <th>Nơi giao</th>
          <th>Ghi chú</th>
        </tr>
      </thead>
      <tbody>
        {purchaseRequest.items.map((item, index) => (
          <tr key={item.id ?? `${item.product_code}-${index}`}>
            <td className="text-center">{index + 1}</td>
            <td>{item.product_name}</td>
            <td>{item.product_code}</td>
            <td>{item.unit}</td>
            <td className="text-right tabular-nums">{formatQuantity(item.qty)}</td>
            <td className="text-right tabular-nums">{formatUnitPrice(item.price)}</td>
            <td className="text-right tabular-nums">
              {formatMoney(item.qty * item.price)}
            </td>
            <td>{warehouseCode(item.warehouse)}</td>
            <td>{item.note}</td>
          </tr>
        ))}
        <tr>
          <td className="font-bold" colSpan={6}>
            Tổng cộng
          </td>
          <td className="text-right font-bold tabular-nums">
            {formatMoney(purchaseRequest.subtotal)}
          </td>
          <td colSpan={2} />
        </tr>
        <tr className="pr-print-total-row">
          <td className="pt-2 text-right text-[13px]" colSpan={6}>
            Tiền VAT:
          </td>
          <td className="pt-2 text-right text-[13px] font-bold tabular-nums">
            {formatMoney(purchaseRequest.vat)}
          </td>
          <td colSpan={2} />
        </tr>
        <tr className="pr-print-total-row">
          <td className="pb-2 pt-1 text-right text-[13px]" colSpan={6}>
            Tổng cộng thanh toán (gồm VAT):
          </td>
          <td className="pb-2 pt-1 text-right text-[13px] font-bold tabular-nums">
            {formatMoney(purchaseRequest.total)}
          </td>
          <td colSpan={2} />
        </tr>
      </tbody>
    </table>
  )
}

function SignatureSection({
  purchaseRequest,
  taxMode,
  showSignature,
}: {
  purchaseRequest: PurchaseRequestDetail
  taxMode: boolean
  showSignature: boolean
}) {
  const values: Record<string, { signature: string; name: string }> = taxMode
    ? {}
    : {
        'Người lập': {
          signature: purchaseRequest.requester_signature,
          name: purchaseRequest.requester,
        },
        'TP/BP đề xuất': {
          signature: purchaseRequest.approver_signature,
          name: purchaseRequest.approver_name,
        },
        'TP/BP mua hàng': {
          signature: purchaseRequest.dispatcher_signature,
          name: purchaseRequest.dispatcher_name,
        },
      }

  return (
    <section className="pr-print-signatures">
      <h2 className="pr-print-section-title">
        XÉT DUYỆT
      </h2>
      <div className="pr-print-signature-grid">
        {['Giám đốc', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập'].map((role) => {
          const signature = showSignature ? values[role]?.signature || '' : ''
          const name = values[role]?.name || ''
          return (
            <div key={role} className="pr-print-signature-cell">
              <b>{role}</b>
              <p className="text-[11px] italic">(Ký, ghi rõ họ tên)</p>
              <div className="mt-1 flex h-[94px] flex-col items-center justify-center gap-2.5 font-bold">
                {signature && (
                  <img
                    src={signature}
                    alt={`Chữ ký ${role}`}
                    className="max-h-14 max-w-full object-contain"
                  />
                )}
                <span>{name}</span>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

function PrintToggle({
  options,
  value,
  onChange,
}: {
  options: { value: boolean; label: string }[]
  value: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <div className="inline-flex overflow-hidden rounded-lg border border-slate-300 bg-white">
      {options.map((option) => (
        <button
          key={option.label}
          type="button"
          className={
            value === option.value
              ? 'whitespace-nowrap bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground'
              : 'whitespace-nowrap bg-white px-4 py-2 text-[13px] font-medium text-slate-600 hover:bg-slate-50'
          }
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

function hasSupplierData(value: PurchaseRequestDetail['supplier_pur']): boolean {
  return Boolean(value?.name || value?.tax_code || value?.contact)
}

function formatVietnameseLongDate(value: string): string {
  if (!value) return 'Ngày ........ tháng ........ năm ........'
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `Ngày ${day} tháng ${month} năm ${year}`
}

function formatShortDate(value: string): string {
  if (!value) return ''
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function getClosestNeedDate(items: PurchaseRequestItem[]): string {
  const dates = items
    .map((item) => item.required_date)
    .filter((value): value is string => Boolean(value?.trim()))
  if (!dates.length) return ''

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const closest = dates.reduce((current, candidate) => {
    const currentDistance = Math.abs(parseLocalDate(current).getTime() - today.getTime())
    const candidateDistance = Math.abs(parseLocalDate(candidate).getTime() - today.getTime())
    return candidateDistance < currentDistance ? candidate : current
  })
  return formatShortDate(closest)
}

function parseLocalDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

const PRINT_STYLES = `
  .pr-print-root {
    min-height: 100dvh;
    overflow-x: auto;
    padding: 24px;
    background: #e9eef5;
    color: #0f172a;
  }

  .pr-print-toolbar {
    position: sticky;
    top: 16px;
    z-index: 10;
    display: flex;
    width: 210mm;
    max-width: calc(100vw - 48px);
    min-height: 44px;
    margin: 0 auto 16px;
    padding: 0;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    border: 0;
    background: transparent;
    box-shadow: none;
  }

  .pr-print-toolbar-actions,
  .pr-print-toolbar-options {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  .pr-print-toolbar-options {
    justify-content: flex-end;
  }

  .pr-print-doc,
  .pr-print-doc * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .pr-print-doc {
    position: relative;
    box-sizing: border-box;
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto;
    padding: 10mm 12mm 18mm;
    font-family: Arial, sans-serif;
    color: #000;
    background: #fff;
    border: 1px solid #d7dde7;
    border-radius: 4px;
    box-shadow: 0 18px 48px rgba(27, 37, 89, 0.14);
  }

  .pr-print-doc p {
    margin-top: 0;
    margin-bottom: 0;
  }

  .pr-print-document-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
  }

  .pr-print-document-title {
    margin: 18px 0 4px;
    text-align: center;
    font-size: 17px;
    font-weight: 700;
    line-height: 1.25;
  }

  .pr-print-document-code,
  .pr-print-document-date {
    text-align: center;
    font-size: 12px;
    line-height: 1.5;
  }

  .pr-print-document-date {
    margin-bottom: 6px !important;
  }

  .pr-print-section-title {
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

  .pr-print-section-content {
    padding: 6px 4px;
    font-size: 12px;
    line-height: 1.7;
  }

  .pr-print-items {
    width: 100%;
    margin-top: 6px;
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 11px;
  }

  .pr-print-items th,
  .pr-print-items td {
    border: 1px solid #999;
    padding: 5px 6px;
    vertical-align: middle;
    overflow-wrap: anywhere;
  }

  .pr-print-items th {
    background: #e9edf1;
    font-weight: 700;
    text-align: center;
    line-height: 1.3;
  }

  .pr-print-items th:nth-child(2),
  .pr-print-items th:nth-child(3),
  .pr-print-items th:nth-child(8),
  .pr-print-items th:nth-child(9) {
    text-align: left;
  }

  .pr-print-col-number { width: 5%; }
  .pr-print-col-name { width: 27%; }
  .pr-print-col-code { width: 10%; }
  .pr-print-col-unit { width: 6%; }
  .pr-print-col-quantity { width: 8%; }
  .pr-print-col-price { width: 10%; }
  .pr-print-col-total { width: 11%; }
  .pr-print-col-place { width: 10%; }
  .pr-print-col-note { width: 13%; }

  .pr-print-items tr {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .pr-print-items .pr-print-total-row td {
    border: 0;
  }

  .pr-print-signatures {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .pr-print-signature-grid {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 8px;
    margin-top: 16px;
    text-align: center;
    font-size: 12px;
  }

  .pr-print-signature-cell {
    min-width: 0;
    padding: 0 4px;
  }

  .pr-print-note {
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

    .pr-print-root {
      min-height: 0 !important;
      padding: 0 !important;
      background: #fff !important;
    }

    .pr-print-toolbar {
      display: none !important;
    }

    .pr-print-doc {
      width: 210mm !important;
      max-width: none !important;
      min-height: 0 !important;
      padding: 10mm 12mm 18mm !important;
      box-shadow: none !important;
      border: 0 !important;
      border-radius: 0 !important;
      -webkit-box-decoration-break: clone;
      box-decoration-break: clone;
    }

    .pr-print-items thead {
      display: table-header-group;
    }

    .pr-print-note {
      position: fixed !important;
      right: 12mm !important;
      bottom: 6mm !important;
    }
  }

  @media screen and (max-width: 850px) {
    .pr-print-root {
      padding: 12px;
    }

    .pr-print-toolbar,
    .pr-print-doc {
      min-width: 210mm;
    }

    .pr-print-toolbar {
      position: static;
      max-width: none;
    }
  }
`
