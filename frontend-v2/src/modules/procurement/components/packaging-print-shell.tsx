/**
 * duoc-CR-784 — KHUNG chung của các bản in cụm Giá bao bì (Lịch sử mua hàng, Tác động giá), dựng theo bản mẫu HTML của người
 * chủ: thanh đầu (logo DEGO · đường dẫn "Dego Holding › Phòng Thu mua › Báo cáo giá › <bản in>" · tên báo cáo · giờ in /
 * người in), thanh nút trên màn hình ("In lại" / "Đóng", ẩn khi in), chân trang thương hiệu (chỉ trên màn hình, bản mẫu cũng
 * ẩn khi in). Các ô lọc, thẻ số liệu, bảng do trang con truyền vào. CSS ở `packaging-print.css`, gắn bằng thẻ <style> khi
 * trang in đang mở nên không rò sang ứng dụng.
 *
 * Tự mở hộp thoại in MỘT lần khi `status = 'ready'`: chờ font Montserrat (tối đa `PACKAGING_PRINT_FONT_WAIT_MS`) + một nhịp
 * ngắn cho bảng / biểu đồ dựng xong. Lỗi tải thì chỉ hiện câu lỗi, KHÔNG bật hộp thoại in. "In lại" mở lại bất cứ lúc nào.
 */
import { Printer, X } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'

import { useAuthStore } from '@/core/auth/auth-store'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'

import { buildPackagingPrintTitle } from '../utils/packaging-print-title'
import {
  PACKAGING_PRINT_CRUMB,
  PACKAGING_PRINT_DELAY_MS,
  PACKAGING_PRINT_FONT_URL,
  PACKAGING_PRINT_FONT_WAIT_MS,
  PACKAGING_PRINT_REPORT_TITLE,
} from './packaging-print-constants'
import PRINT_CSS from './packaging-print.css?raw'

export type PackagingPrintStatus = 'loading' | 'error' | 'ready'

interface PackagingPrintShellProps {
  /** Tên bản in — đuôi đường dẫn ở đầu trang, cũng là gốc tên tệp PDF gợi ý. */
  subtitle: string
  status: PackagingPrintStatus
  /** Câu lỗi hiện khi `status = 'error'`. */
  errorMessage?: string
  children: ReactNode
}

/** Nạp font bản mẫu một lần; gỡ khi rời trang. Lỗi mạng thì thôi — CSS đã có font dự phòng. */
function useMontserrat() {
  useEffect(() => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = PACKAGING_PRINT_FONT_URL
    document.head.appendChild(link)
    return () => link.remove()
  }, [])
}

/** Đợi font sẵn sàng nhưng không quá `PACKAGING_PRINT_FONT_WAIT_MS` (môi trường không có `document.fonts` thì bỏ qua). */
function fontsReady(): Promise<void> {
  const ready = document.fonts?.ready
  if (!ready) return Promise.resolve()
  return Promise.race([
    ready.then(() => undefined),
    new Promise<void>((resolve) => window.setTimeout(resolve, PACKAGING_PRINT_FONT_WAIT_MS)),
  ])
}

export function PackagingPrintShell({ subtitle, status, errorMessage, children }: PackagingPrintShellProps) {
  const printedBy = useAuthStore((state) => state.user?.full_name)
  //  Một mốc giờ cố định cho cả tờ — render lại không làm giờ in nhảy.
  const [printedAt] = useState(() => formatDateTime(new Date()))
  useMontserrat()

  useEffect(() => {
    const previousTitle = document.title
    document.title = buildPackagingPrintTitle(subtitle)
    return () => {
      document.title = previousTitle
    }
  }, [subtitle])

  useEffect(() => {
    if (status !== 'ready') return
    //  Cờ huỷ thay cho clearTimeout: effect chạy lại (StrictMode dựng hai lần) thì lượt cũ bị bỏ, chỉ còn một lệnh in.
    let cancelled = false
    let timer = 0
    void fontsReady().then(() => {
      if (cancelled) return
      timer = window.setTimeout(() => window.print(), PACKAGING_PRINT_DELAY_MS)
    })
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [status])

  return (
    <main className="pp">
      <style>{PRINT_CSS}</style>

      <div className="pp-bar no-print">
        <Button type="button" disabled={status !== 'ready'} onClick={() => window.print()}>
          <Printer />
          In lại
        </Button>
        <Button type="button" variant="outline" onClick={() => window.close()}>
          <X />
          Đóng
        </Button>
      </div>

      <div className="pp-app">
        <header className="pp-topbar">
          <img src="/logo.svg" alt="Dego Holding" className="pp-logo" />
          <div className="pp-sep" />
          <div>
            <div className="pp-crumb">
              {PACKAGING_PRINT_CRUMB} › {subtitle}
            </div>
            <h1 className="pp-title">{PACKAGING_PRINT_REPORT_TITLE}</h1>
          </div>
          <div className="pp-spacer" />
          <div className="pp-meta">
            <div>In lúc: {printedAt}</div>
            {printedBy && <div>Người in: {printedBy}</div>}
          </div>
        </header>

        <div className="pp-body">
          {status === 'loading' && <Skeleton className="h-[120mm] w-full" />}
          {status === 'error' && (
            <p role="alert" className="panel empty">
              {errorMessage || 'Không tải được số liệu để in.'}
            </p>
          )}
          {status === 'ready' && children}
        </div>
      </div>

      <footer className="pp-bfoot">
        <svg viewBox="0 0 1440 40" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0,28 C240,4 480,40 760,22 C1040,4 1240,30 1440,14 L1440,40 L0,40 Z" fill="#00AEEF" opacity=".55" />
          <path d="M0,34 C300,18 560,44 880,28 C1120,16 1300,36 1440,26 L1440,40 L0,40 Z" fill="#0F3B6E" />
        </svg>
        <div className="in">
          <b>DEGO HOLDING</b>
          <span className="tag">FOR A BETTER LIFE</span>
          <span className="pp-spacer" />
          <span className="kw">
            PEOPLE <i>|</i> NATURE <i>|</i> INNOVATION <i>|</i> SUSTAINABILITY
          </span>
        </div>
      </footer>
    </main>
  )
}
