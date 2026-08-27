import { ArrowLeft, Check, Printer, X } from 'lucide-react'
import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { usePaymentRequestPrintData } from '../hooks/use-payment-requests'
import { parseMoney } from '../utils/doc-tien'

const DOTS = '............................'

/** Có dữ liệu thì hiện, không thì để dòng chấm cho điền tay. */
function dot(value: string): string {
  return value ? value : DOTS
}

/** `yyyy-mm-dd` -> "Ngày dd tháng mm năm yyyy". */
function viDate(value: string): string {
  if (!value) return ''
  const [year, month, day] = value.split('-')
  return `Ngày ${day} tháng ${month} năm ${year}`
}

const cell: CSSProperties = { border: '1px solid #888', padding: '3px 6px', fontSize: 11, verticalAlign: 'top' }
const cellCenter: CSSProperties = { ...cell, textAlign: 'center' }
const cellRight: CSSProperties = { ...cell, textAlign: 'right' }
const cellHead: CSSProperties = { ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle', background: '#eef2f6' }
const sectionHead: CSSProperties = {
  background: '#dbe5f1',
  fontWeight: 700,
  padding: '3px 8px',
  fontSize: 11.5,
  margin: '9px 0 3px',
  border: '1px solid #c6d4e6',
}
const lbl: CSSProperties = { fontSize: 11, padding: '1px 4px' }
const hcell: CSSProperties = { border: '1px solid #888', padding: '2px 5px', fontSize: 10, lineHeight: 1.4 }

/** Ô tick vẽ bằng viền — thay ký hiệu ☑/☐ để không lệ thuộc font emoji của máy in. */
function PrintCheckbox({ checked }: { checked: boolean }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 12,
        height: 12,
        border: '1px solid #000',
        marginRight: 6,
        verticalAlign: 'middle',
      }}
    >
      {checked && <Check className="size-3" strokeWidth={3} />}
    </span>
  )
}

/**
 * Bản in Đề nghị thanh toán — Mẫu 002/BM/PKT.
 *
 * Route nằm NGOÀI layout để trang in không mang theo menu. Bố cục chép sát bản v1
 * (`frontend/src/pages/PrintPaymentRequest.tsx`) để kế toán đối chiếu với chứng từ
 * cũ không lệch; số đọc bằng chữ dùng chung `docTien`.
 */
export function PaymentRequestPrintPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const paymentRequestId = Number(id)
  const { data: req, isLoading, isError } = usePaymentRequestPrintData(paymentRequestId)
  const [taxMode, setTaxMode] = useState(false)

  useEffect(() => {
    if (!req?.code) return
    const previousTitle = document.title
    document.title = `${req.code} - Đề nghị thanh toán`
    return () => {
      document.title = previousTitle
    }
  }, [req?.code])

  // Gom các dòng trùng chứng từ (ví dụ 256) lại thành 1 dòng + tổng tiền
  const lines = req?.lines
  const groupedLines = useMemo(() => {
    if (!lines || !Array.isArray(lines)) return []
    const map = new Map<string, any>()
    for (const l of lines) {
      const invNo = (l.invoice_no || '').trim()
      const invDate = (l.invoice_date || '').trim()
      const key = `${invNo}||${invDate}`
      if (map.has(key)) {
        const existing = map.get(key)
        existing.amount = (Number(existing.amount) || 0) + (Number(l.amount) || 0)
      } else {
        map.set(key, { ...l, amount: Number(l.amount) || 0 })
      }
    }
    return Array.from(map.values())
  }, [lines])

  if (isLoading) {
    return (
      <main className="min-h-[100dvh] bg-slate-200 p-5">
        <Skeleton className="mx-auto mb-3 h-10 max-w-[210mm]" />
        <Skeleton className="mx-auto h-[260mm] max-w-[210mm] bg-white" />
      </main>
    )
  }

  if (isError || !req) {
    return (
      <ErrorState
        title="Không mở được bản in"
        description="Phiếu có thể đã bị xóa, hoặc bạn không có quyền in phiếu này."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.finance.paymentRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  const company = req.company ?? {}
  const supplier = req.supplier_name || req.supplier_code
  const period = (req.period || '').split('-').reverse().join('/') // YYYY-MM -> MM/YYYY
  // CR-146 main (ticket #12): phiếu đánh dấu THANH TOÁN TRƯỚC thì đổi câu nội dung
  const content = req.prepay
    ? `Thanh toán trước cho nhà cung cấp ${supplier}${period ? ` ${period}` : ''}`
    : `Thanh toán công nợ ${supplier}${period ? ` ${period}` : ''}`
  // CR-149 (ticket #14): người dùng sửa được 3 câu — khóa nào rỗng thì in câu tự động.
  const printTexts = req.print_texts ?? {}
  const contentText = printTexts.content || content
  const lineDescText = printTexts.line_desc || content
  const transferText = printTexts.transfer || content
  const isCash = req.payment_method === 'cash' // CR-035 — tiền mặt thì bỏ trống cụm chuyển khoản

  return (
    <main className="pr-print-root min-h-[100dvh] bg-slate-200 p-4 text-slate-950">
      <style>{PRINT_STYLES}</style>

      <div className="no-print mx-auto mb-3 flex max-w-[210mm] flex-wrap items-center gap-2">
        <Button onClick={() => window.print()}>
          <Printer />
          In / Lưu PDF
        </Button>
        <Button variant="outline" onClick={() => window.close()}>
          <X />
          Đóng
        </Button>

        <div className="ml-auto inline-flex overflow-hidden rounded-md border bg-background">
          {[
            { v: false, t: 'Mẫu thường' },
            { v: true, t: 'Mẫu thuế' },
          ].map((tab) => (
            <button
              key={tab.t}
              onClick={() => setTaxMode(tab.v)}
              className={`px-4 py-1.5 text-sm font-medium transition-colors ${
                taxMode === tab.v
                  ? 'bg-sky-600 text-white'
                  : 'bg-background text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
              }`}
            >
              {tab.t}
            </button>
          ))}
        </div>
      </div>

      <div
        className="pr-print-doc"
        style={{ margin: '0 auto', maxWidth: '210mm', background: '#fff', padding: '24px 30px', fontFamily: 'Arial, sans-serif', color: '#000' }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>{company.name || ''}</div>
          <table style={{ borderCollapse: 'collapse', width: 150, tableLayout: 'fixed' }}>
            <tbody>
              <tr>
                <td style={{ ...hcell, fontWeight: 600, whiteSpace: 'nowrap' }}>Mẫu</td>
                <td style={hcell}>002/BM/PKT</td>
              </tr>
              <tr>
                <td style={{ ...hcell, fontWeight: 600, whiteSpace: 'nowrap' }}>Phiên bản</td>
                <td style={hcell}>062026</td>
              </tr>
              <tr>
                <td style={{ ...hcell, fontWeight: 600, whiteSpace: 'nowrap' }}>Ngày update</td>
                <td style={hcell}>17/6/2025</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h2 style={{ textAlign: 'center', fontSize: 17, margin: '10px 0 2px' }}>ĐỀ NGHỊ THANH TOÁN</h2>
        <div style={{ textAlign: 'center', fontSize: 12 }}>Số: {req.code}</div>
        <div style={{ textAlign: 'center', fontSize: 12, marginBottom: 4 }}>{viDate(req.request_date)}</div>

        {/* Thông tin chung */}
        <div style={sectionHead}>THÔNG TIN CHUNG</div>
        <div style={{ lineHeight: 1.55 }}>
          <div style={lbl}>
            <b>Người đề nghị thanh toán:</b> {taxMode ? '' : (req.created_by_name || '')}
          </div>
          <div style={lbl}>
            <b>Chức vụ:</b> {taxMode ? '' : dot(req.created_by_position)}
          </div>
          <div style={lbl}>
            <b>Hiện công tác tại bộ phận:</b> {taxMode ? '' : dot(req.created_by_dept)}
          </div>
          <div style={lbl}>
            <b>Trưởng phòng ban/bộ phận:</b> {taxMode ? '' : dot(req.dept_manager)}
          </div>
        </div>

        {/* Nội dung thanh toán */}
        <div style={sectionHead}>NỘI DUNG THANH TOÁN</div>
        <div style={{ lineHeight: 1.55, marginBottom: 4 }}>
          <div style={lbl}>
            <b>Đối tượng:</b> {supplier}
          </div>
          <div style={lbl}>
            <b>Mã khoản mục CP:</b> {DOTS}
          </div>
          <div style={lbl}>
            <b>Nội dung:</b> {contentText}
          </div>
        </div>

        <div style={{ ...lbl, fontWeight: 700 }}>Đề nghị thanh toán:</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '13%' }} />
            <col style={{ width: '11%' }} />
            <col style={{ width: '40%' }} />
            <col style={{ width: '15%' }} />
            <col style={{ width: '13%' }} />
            <col style={{ width: '8%' }} />
          </colgroup>
          <thead>
            <tr>
              <td style={cellHead} colSpan={2}>
                Chứng từ
              </td>
              <td style={cellHead} rowSpan={2}>
                Diễn giải
              </td>
              <td style={cellHead} rowSpan={2}>
                Số tiền đề nghị thanh toán
              </td>
              <td style={cellHead} rowSpan={2}>
                Số tiền được duyệt
              </td>
              <td style={cellHead} rowSpan={2}>
                Ghi chú
              </td>
            </tr>
            <tr>
              <td style={cellHead}>Số</td>
              <td style={cellHead}>Ngày</td>
            </tr>
          </thead>
          <tbody>
            {groupedLines.map((line, index) => (
              <tr key={line.id ?? index}>
                <td style={{ ...cellCenter, wordBreak: 'break-word', overflowWrap: 'anywhere' }}>{line.invoice_no}</td>
                {/* CR-066: chưa có hóa đơn thì in trắng để điền tay — không lấy ngày phát sinh thay thế. */}
                <td style={cellCenter}>{formatDate(line.invoice_date)}</td>
                {/* Diễn giải gộp cho mọi dòng (rowSpan) — chỉ vẽ ở dòng đầu. */}
                {index === 0 && (
                  <td style={{ ...cell, verticalAlign: 'middle' }} rowSpan={groupedLines.length || 1}>
                    {lineDescText}
                  </td>
                )}
                <td style={cellRight}>{formatMoney(line.amount)}</td>
                <td style={cell} />
                <td style={cell} />
              </tr>
            ))}
            {groupedLines.length === 0 && (
              <tr>
                <td style={cell} />
                <td style={cell} />
                <td style={cell}>{lineDescText}</td>
                <td style={cell} />
                <td style={cell} />
                <td style={cell} />
              </tr>
            )}
            <tr>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={3}>
                Cộng
              </td>
              <td style={{ ...cellRight, fontWeight: 700 }}>{formatMoney(req.total)}</td>
              <td style={cell} colSpan={2} />
            </tr>
          </tbody>
        </table>

        {/* Đã tạm ứng/thanh toán — để trống điền tay (theo mẫu 002/BM/PKT). */}
        <div style={{ ...lbl, fontWeight: 700, marginTop: 10 }}>Đã tạm ứng/thanh toán:</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '6%' }} />
            <col style={{ width: '11%' }} />
            <col style={{ width: '33%' }} />
            <col style={{ width: '20%' }} />
            <col style={{ width: '18%' }} />
            <col style={{ width: '12%' }} />
          </colgroup>
          <thead>
            <tr>
              <td style={cellHead} colSpan={2}>
                Chứng từ
              </td>
              <td style={cellHead} rowSpan={2}>
                Diễn giải
              </td>
              <td style={cellHead} rowSpan={2}>
                Số tiền đề nghị tạm ứng
              </td>
              <td style={cellHead} rowSpan={2}>
                Số tiền đã tạm ứng
              </td>
              <td style={cellHead} rowSpan={2}>
                Ghi chú
              </td>
            </tr>
            <tr>
              <td style={cellHead}>Số</td>
              <td style={cellHead}>Ngày</td>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ ...cell, height: 24 }} />
              <td style={cell} />
              <td style={cell} />
              <td style={cell} />
              <td style={cell} />
              <td style={cell} />
            </tr>
            <tr>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Cộng</td>
              <td style={cell} />
              <td style={{ ...cell, fontWeight: 700 }}>Số lượng: ....mục</td>
              <td style={cell} />
              <td style={cell} />
              <td style={cell} />
            </tr>
          </tbody>
        </table>

        <div style={{ marginTop: 8, fontSize: 11 }}>
          <div style={{ display: 'flex' }}>
            <div style={{ width: '3%' }} />
            <div style={{ width: '47%' }}>
              <PrintCheckbox checked />
              Còn lại phải thanh toán:
            </div>
            <div style={{ width: '20%', textAlign: 'left', fontWeight: 700 }}>{formatMoney(req.total)}</div>
          </div>
          <div style={{ display: 'flex', marginTop: 3 }}>
            <div style={{ width: '3%' }} />
            <div style={{ width: '47%' }}>
              <PrintCheckbox checked={false} />
              Phải hoàn lại cho Công ty:
            </div>
          </div>
        </div>
        <div style={{ ...lbl, marginTop: 4 }}>
          <b>Bằng chữ:</b> <i>{parseMoney(req.total)}</i>
        </div>

        {/* Hình thức thanh toán — trái (đơn vị + hình thức) / phải (thông tin chuyển khoản). */}
        <div style={sectionHead}>HÌNH THỨC THANH TOÁN</div>
        <div style={{ display: 'flex', fontSize: 11, lineHeight: 1.55 }}>
          <div style={{ width: '48%', paddingRight: 8 }}>
            <div style={lbl}>
              <b>Mã đơn vị:</b> {company.name || ''}
            </div>
            <div style={lbl}>
              <PrintCheckbox checked={isCash} />
              Tiền mặt
            </div>
            <div style={lbl}>
              <PrintCheckbox checked={!isCash} />
              Chuyển khoản
            </div>
          </div>
          <div style={{ width: '52%' }}>
            <div style={{ ...lbl, fontWeight: 700 }}>Thông tin chuyển khoản:</div>
            <div style={lbl}>
              <b>Tên TK thụ hưởng:</b> {isCash ? DOTS : supplier}
            </div>
            <div style={lbl}>
              <b>Số TK thụ hưởng:</b> {isCash ? DOTS : dot(req.bank_account)}
            </div>
            <div style={lbl}>
              <b>Ngân hàng:</b> {isCash ? DOTS : dot(req.bank_name)}
            </div>
            <div style={lbl}>
              <b>Nội dung chuyển khoản:</b> {isCash ? DOTS : transferText}
            </div>
          </div>
        </div>

        {/* Xét duyệt */}
        <div style={sectionHead}>XÉT DUYỆT</div>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', fontSize: 11, marginTop: 6 }}>
          {['Giám đốc', 'KT trưởng/TP.Kế toán', 'TP/Trưởng BP duyệt', 'Người lập phiếu'].map((role) => (
            <div key={role} style={{ flex: 1 }}>
              <b>{role}</b>
              <div style={{ fontStyle: 'italic', fontSize: 10 }}>(Ký, ghi rõ họ tên)</div>
              <div style={{ height: 44 }} />
            </div>
          ))}
        </div>

        <div style={sectionHead}>HỒ SƠ ĐÍNH KÈM</div>
        <div style={{ fontSize: 11, padding: '2px 8px', lineHeight: 1.5 }}>
          {[1, 2, 3].map((index) => (
            <div key={index}>{index}. ............................................</div>
          ))}
        </div>

        {/* Cụm ký nhận Kế toán — Thanh toán / Công nợ (điền tay). */}
        <div style={{ marginTop: 12, fontSize: 11 }}>
          <div style={{ display: 'flex', textAlign: 'center', fontWeight: 700 }}>
            <div style={{ width: '24%' }} />
            {['KT Thanh toán', 'KT Công nợ'].map((role) => (
              <div key={role} style={{ flex: 1 }}>
                {role}
                <div style={{ fontStyle: 'italic', fontSize: 10, fontWeight: 400 }}>(Thời gian, ký tên)</div>
              </div>
            ))}
          </div>
          {['Nhận hồ sơ:', 'Chứng từ hạch toán:', 'Hồ sơ trả về:'].map((role) => (
            <div key={role} style={{ display: 'flex', alignItems: 'flex-end', marginTop: 9 }}>
              <div style={{ width: '24%', fontWeight: 700, whiteSpace: 'nowrap' }}>{role}</div>
              <div style={{ flex: 1, borderBottom: '1px solid #000', margin: '0 10px' }} />
              <div style={{ flex: 1, borderBottom: '1px solid #000', margin: '0 10px' }} />
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}

/**
 * `@page { margin: 12mm }`: chứng từ này in DỌC A4, lề để trình duyệt tự chừa. Khối
 * `.no-print` (thanh nút) ẩn khi in; nền xám chỉ để xem trên màn hình.
 */
const PRINT_STYLES = `
  @media print {
    @page { size: A4 portrait; margin: 12mm; }
    html, body { margin: 0 !important; background: #fff !important; }
    .no-print { display: none !important; }
    .pr-print-root { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
    .pr-print-doc { max-width: none !important; padding: 0 !important; }
  }
`
