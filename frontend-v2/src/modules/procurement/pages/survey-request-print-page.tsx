import { ArrowLeft, Printer, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { useSurveyRequestPrint } from '../hooks/use-survey-request'
import type { SurveyRequestPrintLine } from '../types/survey-request-detail'

/**
 * P6-9 (bao-CR-287, chỉnh theo bao-CR-288): bản in phiếu yêu cầu của LUỒNG GỘP.
 *
 * ⚠️ ĐÂY LÀ MẪU KẾ TOÁN 003/BM/PKT — chuẩn chứng từ đi thanh toán, dùng CHUNG với
 * bản in YCMH cũ (`frontend/src/pages/PrintPurchaseRequest.tsx`). Khách chốt
 * 04/09/2026: KHÔNG thêm bớt bất kỳ chữ / cột / dòng chú thích nào so với mẫu —
 * chỉ đổ dữ liệu của phiếu vào đúng ô sẵn có. Trường mẫu có mà phiếu không có
 * dữ liệu thì in trống / chấm chấm y như bản cũ.
 *
 * Đổ dữ liệu (không đổi khuôn):
 * - Đơn giá: dòng ĐÃ CHỐT phương án lấy giá chốt (`chosen_price`), dòng chưa chốt
 *   lấy giá đề xuất của người yêu cầu — backend `/print` đã lọc theo luật ẩn NCC.
 * - Cụm NHÀ CUNG CẤP DO BỘ PHẬN ĐỀ XUẤT: mẫu chỉ có MỘT cụm NCC (xem ghi chú
 *   Task 4 ở bản in cũ) — đổ NCC người yêu cầu đề xuất (`suggested_supplier*`).
 *   NCC đã chốt theo từng dòng nằm ở bản in thu mua (`In theo NCC`), không nhét
 *   thêm cột vào mẫu này.
 *
 * Route nằm ngoài ModuleLayout để bản in không mang theo menu và topbar.
 */
export function SurveyRequestPrintPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const surveyRequestId = Number(id) || 0
  const { data, isLoading, isError } = useSurveyRequestPrint(surveyRequestId)
  const { data: companiesData } = useCompanies({ page_size: 500 })
  // Mẫu thuế: để trống thông tin người yêu cầu (giống bản cũ).
  const [taxMode, setTaxMode] = useState(false)

  useEffect(() => {
    if (!data?.code) return
    const previousTitle = document.title
    // Tên file gợi ý khi Lưu PDF = `<mã phiếu>-DDMMYYYY` — cùng khuôn `tenFileIn`
    // của các phiếu in bản v1 (trình duyệt lấy document.title làm tên file).
    document.title = buildPrintFileName(data.code, data.request_date)
    return () => {
      document.title = previousTitle
    }
  }, [data?.code, data?.request_date])

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
        description="Phiếu có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
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
    <main className="sr-print-root min-h-[100dvh] bg-slate-200 p-5 text-slate-950">
      <style>{PRINT_STYLES}</style>

      <div className="sr-print-toolbar">
        <div className="sr-print-toolbar-actions">
          <Button onClick={() => window.print()}>
            <Printer />
            In / Lưu PDF
          </Button>
          <Button variant="outline" onClick={() => window.close()}>
            <X />
            Đóng
          </Button>
        </div>
        <div className="sr-print-toolbar-actions">
          <Button
            variant={taxMode ? 'outline' : 'default'}
            size="sm"
            onClick={() => setTaxMode(false)}
          >
            Mẫu thường
          </Button>
          <Button
            variant={taxMode ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTaxMode(true)}
          >
            Mẫu thuế
          </Button>
        </div>
      </div>

      <article className="sr-print-doc">
        <header className="sr-print-document-header">
          <p className="text-[13px]">
            <b>Đơn vị:</b> {companyName || '...'}
          </p>
          <table className="sr-print-form-code">
            <tbody>
              <tr>
                <td colSpan={2} className="text-center font-bold">
                  Mẫu 003/BM/PKT
                </td>
              </tr>
              <tr>
                <td>Phiên bản</td>
                <td className="text-center">V1-062025</td>
              </tr>
              <tr>
                <td>Ngày update:</td>
                <td className="text-center">17/7/2025</td>
              </tr>
            </tbody>
          </table>
        </header>

        <h1 className="sr-print-document-title">PHIẾU ĐỀ XUẤT MUA HÀNG HÓA/DỊCH VỤ</h1>
        <p className="sr-print-document-code">Số: {data.code}</p>
        <p className="sr-print-document-date">{formatVietnameseLongDate(data.request_date)}</p>

        <PrintSection title="THÔNG TIN CHUNG">
          <PrintLine label="Người đề xuất" value={taxMode ? '' : data.requester} />
          <PrintLine
            label="Chức vụ"
            value={taxMode ? '' : data.requester_position || '............'}
          />
          <PrintLine
            label="Hiện công tác tại bộ phận"
            value={taxMode ? '' : data.department || '............'}
          />
          <PrintLine
            label="Trưởng phòng ban/bộ phận"
            value={taxMode ? '' : data.head_of_dept || '............'}
          />
        </PrintSection>

        <PrintSection title="MỤC ĐÍCH & NỘI DUNG ĐỀ XUẤT">
          <PrintLine label="Mục đích mua hàng/dịch vụ" value={data.purpose} />
          <PrintLine
            label="Thời gian cần hàng/dịch vụ"
            value={findClosestNeedDate(data.lines) || '...'}
          />
          <PrintLine label="Nội dung" value={data.note} />
        </PrintSection>

        <SurveyRequestPrintItems lines={data.lines} />

        <PrintSection title="NHÀ CUNG CẤP DO BỘ PHẬN ĐỀ XUẤT">
          <PrintLine
            label="Tên nhà cung cấp"
            value={data.suggested_supplier || 'Nhà cung cấp tối ưu nhất'}
          />
          <PrintLine label="Mã số thuế" value={data.suggested_supplier_tax_code} />
          <PrintLine label="Liên hệ" value={data.suggested_supplier_contact} />
          <PrintLine label="Báo giá đính kèm" value={'☐ Có    ☑ Không'} />
        </PrintSection>

        <PrintSection title="PHẦN DÀNH CHO BỘ PHẬN MUA HÀNG">
          <PrintLine label="Thời gian cần hàng/dịch vụ" value="............................." />
          <PrintLine label="Yêu cầu khác (nếu có)" value="............................." />
        </PrintSection>

        <section className="sr-print-signatures">
          <h2 className="sr-print-section-title">XÉT DUYỆT</h2>
          <div className="sr-print-signature-grid">
            {[
              { role: 'Giám đốc', name: '' },
              { role: 'TP/BP mua hàng', name: '' },
              { role: 'TP/BP đề xuất', name: '' },
              { role: 'Người lập', name: taxMode ? '' : data.requester },
            ].map((cell) => (
              <div key={cell.role} className="sr-print-signature-cell">
                <b>{cell.role}</b>
                <p className="text-[11px] italic">(Ký, ghi rõ họ tên)</p>
                <div className="mt-1 flex h-[94px] flex-col items-center justify-center gap-2.5 font-bold">
                  <span>{cell.name}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <p className="sr-print-note">Phiếu đề xuất này được in từ hệ thống thu mua</p>
      </article>
    </main>
  )
}

function PrintSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="sr-print-section-title">{title}</h2>
      <div className="sr-print-section-content">{children}</div>
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

function SurveyRequestPrintItems({ lines }: { lines: SurveyRequestPrintLine[] }) {
  const subtotal = lines.reduce((sum, line) => sum + line.request_qty * printPrice(line), 0)
  const vatAmount = lines.reduce(
    (sum, line) => sum + (line.request_qty * printPrice(line) * printVatPercent(line)) / 100,
    0,
  )

  return (
    <table className="sr-print-items">
      <colgroup>
        <col className="sr-print-col-number" />
        <col className="sr-print-col-name" />
        <col className="sr-print-col-code" />
        <col className="sr-print-col-unit" />
        <col className="sr-print-col-quantity" />
        <col className="sr-print-col-price" />
        <col className="sr-print-col-total" />
        <col className="sr-print-col-warehouse" />
        <col className="sr-print-col-note" />
      </colgroup>
      <thead>
        <tr className="bg-[#e9edf1]">
          <th>STT</th>
          <th>Tên hàng hóa/dịch vụ</th>
          <th>Mã hàng</th>
          <th>ĐVT</th>
          <th>Số lượng</th>
          <th>Đơn giá</th>
          {/* Mẫu kế toán 003/BM/PKT KHÔNG có cột VAT trên dòng hàng — VAT chỉ hiện ở
              phần tổng cuối bảng. Không thêm cột vào đây. */}
          <th>Thành tiền</th>
          <th>Nơi giao</th>
          <th>Ghi chú</th>
        </tr>
      </thead>
      <tbody>
        {lines.map((line, index) => {
          const price = printPrice(line)
          return (
            <tr key={line.id ?? index}>
              <td className="text-center">{index + 1}</td>
              <td>{line.requirement_detail}</td>
              <td>{line.product_code}</td>
              <td>{line.uom}</td>
              <td className="text-right tabular-nums">{formatQuantity(line.request_qty)}</td>
              <td className="text-right tabular-nums">{formatUnitPrice(price)}</td>
              <td className="text-right tabular-nums">
                {formatMoney(line.request_qty * price)}
              </td>
              <td>{line.warehouse}</td>
              <td>{line.other_requirement}</td>
            </tr>
          )
        })}
        <tr>
          <td className="font-bold" colSpan={6}>
            Tổng cộng
          </td>
          <td className="text-right font-bold tabular-nums">{formatMoney(subtotal)}</td>
          <td colSpan={2} />
        </tr>
        <tr>
          <td colSpan={6} className="sr-print-summary-label">
            Tiền VAT:
          </td>
          <td className="sr-print-summary-value">{vatAmount ? formatMoney(vatAmount) : '0'}</td>
          <td className="sr-print-summary-blank" colSpan={2} />
        </tr>
        <tr>
          <td colSpan={6} className="sr-print-summary-label">
            Tổng cộng thanh toán (gồm VAT):
          </td>
          <td className="sr-print-summary-value">{formatMoney(subtotal + vatAmount)}</td>
          <td className="sr-print-summary-blank" colSpan={2} />
        </tr>
      </tbody>
    </table>
  )
}

/** Dòng đã chốt in GIÁ CHỐT của phương án; chưa chốt in giá đề xuất của người yêu cầu. */
function printPrice(line: SurveyRequestPrintLine): number {
  return line.print_supplier_source === 'confirmed' ? line.chosen_price : line.proposed_price
}

/** VAT (%) cùng luật với giá: đã chốt lấy VAT phương án, chưa chốt lấy VAT người YC nhập. */
function printVatPercent(line: SurveyRequestPrintLine): number {
  return line.print_supplier_source === 'confirmed' ? line.chosen_vat : line.vat_pct || 0
}

/** "Thời gian cần hàng": ngày cần hàng của dòng GẦN hôm nay nhất — cùng luật bản in cũ. */
function findClosestNeedDate(lines: SurveyRequestPrintLine[]): string {
  const dates = lines
    .map((line) => line.required_date)
    .filter((value) => typeof value === 'string' && value.trim() !== '')
  if (dates.length === 0) return ''
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  let closest = ''
  let minDiff = Infinity
  for (const value of dates) {
    const [year, month, day] = value.split('-').map((part) => Number(part))
    if (!year || !month || !day) continue
    const diff = Math.abs(new Date(year, month - 1, day).getTime() - today.getTime())
    if (diff < minDiff) {
      minDiff = diff
      closest = value
    }
  }
  if (!closest) closest = dates[0]
  const [y, m, d] = closest.split('-')
  return y && m && d ? `${d}/${m}/${y}` : closest
}

function formatVietnameseLongDate(value: string): string {
  if (!value) return '............'
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `Ngày ${day} tháng ${month} năm ${year}`
}

/** `<mã phiếu>-DDMMYYYY`, lọc ký tự Windows cấm — cùng khuôn `tenFileIn` bản v1. */
function buildPrintFileName(code: string, requestDate: string): string {
  const [y, m, d] = String(requestDate || '')
    .slice(0, 10)
    .split('-')
  const ddmmyyyy = y && m && d ? `${d}${m}${y}` : ''
  return [String(code || '').trim(), ddmmyyyy]
    .filter(Boolean)
    .join('-')
    .replace(/[\\/:*?"<>|]/g, '-')
}

const PRINT_STYLES = `
  .sr-print-root {
    min-height: 100dvh;
    overflow-x: auto;
    padding: 24px;
    background: #e9eef5;
    color: #0f172a;
  }

  .sr-print-toolbar {
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

  .sr-print-toolbar-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  .sr-print-doc,
  .sr-print-doc * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .sr-print-doc {
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

  .sr-print-doc p {
    margin-top: 0;
    margin-bottom: 0;
  }

  .sr-print-document-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
  }

  .sr-print-form-code {
    width: 126px;
    border-collapse: collapse;
    font-size: 7.5px;
    text-align: left;
  }

  .sr-print-form-code td {
    border: 1px solid #999;
    padding: 0 3px;
    line-height: 1.25;
    white-space: nowrap;
  }

  .sr-print-document-title {
    margin: 11px 0 3px;
    text-align: center;
    font-size: 17px;
    font-weight: 700;
    line-height: 1.25;
  }

  .sr-print-document-code,
  .sr-print-document-date {
    text-align: center;
    font-size: 12px;
    line-height: 1.5;
  }

  .sr-print-document-date {
    margin-bottom: 6px !important;
  }

  .sr-print-section-title {
    margin: 12px 0 0;
    padding: 5px 8px;
    background: #e9edf1;
    font-size: 12.5px;
    font-weight: 700;
    line-height: 1.35;
    break-after: avoid;
    page-break-after: avoid;
  }

  .sr-print-section-content {
    padding: 6px 4px;
    font-size: 12px;
    line-height: 1.75;
  }

  .sr-print-items {
    width: 100%;
    margin-top: 6px;
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 11px;
  }

  .sr-print-items th,
  .sr-print-items td {
    border: 1px solid #999;
    padding: 5px 6px;
    vertical-align: middle;
    overflow-wrap: anywhere;
  }

  .sr-print-items th {
    background: #e9edf1;
    font-weight: 700;
    text-align: center;
    line-height: 1.3;
  }

  .sr-print-items th:nth-child(2),
  .sr-print-items th:nth-child(9) {
    text-align: left;
  }

  .sr-print-col-number { width: 5%; }
  .sr-print-col-name { width: 23%; }
  .sr-print-col-code { width: 10%; }
  .sr-print-col-unit { width: 6%; }
  .sr-print-col-quantity { width: 8%; }
  .sr-print-col-price { width: 10%; }
  .sr-print-col-total { width: 11%; }
  .sr-print-col-warehouse { width: 9%; }
  .sr-print-col-note { width: 18%; }

  /* Hai dòng tổng VAT cuối bảng: mẫu cũ in KHÔNG viền, canh phải. */
  .sr-print-summary-label,
  .sr-print-summary-value,
  .sr-print-summary-blank {
    border: none !important;
    font-size: 13px;
  }

  .sr-print-summary-label {
    padding: 8px 8px 4px;
    text-align: right;
  }

  .sr-print-summary-value {
    padding: 8px 8px 4px;
    text-align: right;
    font-weight: 700;
    /* Bảng table-layout: fixed nên ô Thành tiền chỉ rộng 11% — số tiền tỷ sẽ gãy
       làm hai dòng nếu không cho tràn; hai dòng tổng không còn viền nên nowrap an toàn. */
    white-space: nowrap;
    overflow-wrap: normal;
  }

  .sr-print-items tr {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .sr-print-signatures {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .sr-print-signature-grid {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 8px;
    margin-top: 16px;
    text-align: center;
    font-size: 12px;
  }

  .sr-print-signature-cell {
    min-width: 0;
    padding: 0 4px;
  }

  .sr-print-note {
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

    .sr-print-root {
      min-height: 0 !important;
      padding: 0 !important;
      background: #fff !important;
    }

    .sr-print-toolbar {
      display: none !important;
    }

    .sr-print-doc {
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

    .sr-print-items thead {
      display: table-header-group;
    }

    .sr-print-note {
      position: fixed !important;
      right: 12mm !important;
      bottom: 6mm !important;
    }
  }

  @media screen and (max-width: 850px) {
    .sr-print-root {
      padding: 12px;
    }

    .sr-print-toolbar,
    .sr-print-doc {
      min-width: 210mm;
    }

    .sr-print-toolbar {
      position: static;
      max-width: none;
    }
  }
`
