import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { useAuth } from '../../auth/AuthContext'
import { usePrintTitle } from '../../hooks/usePrintTitle'
import { fmtDateTime } from '../../utils/datetime'
import { buildPackagingPrintTitle } from '../../utils/packaging-print-title'
import PRINT_CSS from './packaging-print.css?raw'

/** Chờ một nhịp sau khi dữ liệu + font về để bảng / biểu đồ kịp dựng rồi mới mở hộp thoại in. */
export const PACKAGING_PRINT_DELAY_MS = 500
/** Chờ font Montserrat tối đa bấy nhiêu — mạng chậm thì in bằng font dự phòng chứ không treo. */
const FONT_WAIT_MS = 2500
const REPORT_TITLE = 'BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT'
const CRUMB = 'Dego Holding › Phòng Thu mua › Báo cáo giá'
/** Font của bản mẫu (Google Fonts, có tiếng Việt). Không tải được thì rơi về `Segoe UI`, `Arial` như bản mẫu. */
const FONT_URL = 'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap&subset=vietnamese,latin-ext'

export type PackagingPrintStatus = 'loading' | 'error' | 'ready'

/** Ô chưa có số: gạch mờ (khác với 0 đồng). */
export const PrintDash = () => <span className="faint">—</span>

/** Đợi font sẵn sàng nhưng không quá `FONT_WAIT_MS` (trình duyệt không có `document.fonts` thì bỏ qua). */
function fontsReady(): Promise<void> {
  const ready = (document as any).fonts?.ready as Promise<unknown> | undefined
  if (!ready) return Promise.resolve()
  return Promise.race([ready.then(() => undefined), new Promise<void>((resolve) => window.setTimeout(resolve, FONT_WAIT_MS))])
}

/**
 * duoc-CR-784 — KHUNG chung của các bản in cụm Giá bao bì (Lịch sử mua hàng, Tác động giá), dựng theo bản mẫu HTML của người
 * chủ: thanh đầu (logo DEGO · đường dẫn "Dego Holding › Phòng Thu mua › Báo cáo giá › <bản in>" · tên báo cáo · giờ in /
 * người in), thanh nút trên màn hình ("In lại" / "Đóng", ẩn khi in), chân trang thương hiệu (chỉ trên màn hình, bản mẫu cũng
 * ẩn khi in). Các ô lọc, thẻ số liệu, bảng do trang con truyền vào. CSS ở `packaging-print.css`, gắn bằng thẻ <style> khi
 * trang in đang mở (như các phiếu in khác của v1) nên `@page` không đổi khổ giấy của phiếu nào khác.
 *
 * Tự mở hộp thoại in MỘT lần khi `status = 'ready'`: chờ font Montserrat + một nhịp ngắn cho bảng / biểu đồ dựng xong. Lỗi
 * tải thì chỉ hiện câu lỗi, KHÔNG bật hộp thoại in. "In lại" mở lại bất cứ lúc nào.
 */
export default function PackagingPrintShell({ subtitle, status, errorMessage, children }: {
  /** Tên bản in — đuôi đường dẫn ở đầu trang, cũng là gốc tên tệp PDF gợi ý. */
  subtitle: string
  status: PackagingPrintStatus
  errorMessage?: string
  children: ReactNode
}) {
  const { user } = useAuth()
  //  Một mốc giờ cố định cho cả tờ — render lại không làm giờ in nhảy.
  const [printedAt] = useState(() => fmtDateTime(new Date()))
  usePrintTitle(buildPackagingPrintTitle(subtitle))

  useEffect(() => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = FONT_URL
    document.head.appendChild(link)
    return () => link.remove()
  }, [])

  useEffect(() => {
    if (status !== 'ready') return
    //  Cờ huỷ thay cho clearTimeout: effect chạy lại (StrictMode dựng hai lần) thì lượt cũ bị bỏ, chỉ còn một lệnh in.
    let cancelled = false
    let timer = 0
    void fontsReady().then(() => {
      if (!cancelled) timer = window.setTimeout(() => window.print(), PACKAGING_PRINT_DELAY_MS)
    })
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [status])

  return (
    <div className="pp">
      <style>{PRINT_CSS}</style>
      <div className="pp-bar no-print">
        <button className="btn" disabled={status !== 'ready'} onClick={() => window.print()}><i className="ti ti-printer" />In lại</button>
        <button className="btn ghost" onClick={() => window.close()}><i className="ti ti-x" />Đóng</button>
      </div>
      <div className="pp-app">
        <header className="pp-topbar">
          <img src="/logo.svg" alt="Dego Holding" className="pp-logo" />
          <div className="pp-sep" />
          <div>
            <div className="pp-crumb">{CRUMB} › {subtitle}</div>
            <h1 className="pp-title">{REPORT_TITLE}</h1>
          </div>
          <div className="pp-spacer" />
          <div className="pp-meta">
            <div>In lúc: {printedAt}</div>
            {user?.full_name && <div>Người in: {user.full_name}</div>}
          </div>
        </header>
        <div className="pp-body">
          {status === 'loading' && <p className="panel empty">Đang tải số liệu…</p>}
          {status === 'error' && <p role="alert" className="panel empty">{errorMessage || 'Không tải được số liệu để in.'}</p>}
          {status === 'ready' && children}
        </div>
      </div>
      <footer className="pp-bfoot">
        <svg viewBox="0 0 1440 40" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0,28 C240,4 480,40 760,22 C1040,4 1240,30 1440,14 L1440,40 L0,40 Z" fill="#00AEEF" opacity=".55" />
          <path d="M0,34 C300,18 560,44 880,28 C1120,16 1300,36 1440,26 L1440,40 L0,40 Z" fill="#0F3B6E" />
        </svg>
        <div className="in">
          <b>DEGO HOLDING</b><span className="tag">FOR A BETTER LIFE</span><span className="pp-spacer" />
          <span className="kw">PEOPLE <i>|</i> NATURE <i>|</i> INNOVATION <i>|</i> SUSTAINABILITY</span>
        </div>
      </footer>
    </div>
  )
}
