// Banner mời cài PWA (chỉ hiện sau khi đăng nhập — mount trong AppLayout).
// Chromium: dùng event beforeinstallprompt (bắt sớm ở pwa-install.ts) → nút "Cài đặt".
// iOS Safari: hướng dẫn thủ công. "Không hỏi lại" → cờ localStorage vĩnh viễn.
import { useEffect, useState } from 'react'
import { canInstall, onInstallChange, promptInstall } from '../pwa-install'

const DISMISS_KEY = 'pwa-install-dismissed'

const isStandalone = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  (navigator as any).standalone === true

const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent)

export default function PwaInstallPrompt() {
  const [installable, setInstallable] = useState(false)
  const [showIOS, setShowIOS] = useState(false)

  useEffect(() => {
    // Đã tắt vĩnh viễn hoặc đã cài (đang chạy standalone) → không làm gì
    if (localStorage.getItem(DISMISS_KEY) === '1' || isStandalone()) return

    // iOS Safari không có beforeinstallprompt → hiện hướng dẫn thủ công
    if (isIOS()) {
      setShowIOS(true)
      return
    }

    // Chromium: đọc trạng thái từ module (event có thể đã bắn trước khi mount)
    setInstallable(canInstall())
    return onInstallChange(() => setInstallable(canInstall()))
  }, [])

  if (!installable && !showIOS) return null

  const dismissForever = () => {
    localStorage.setItem(DISMISS_KEY, '1')
    setInstallable(false)
    setShowIOS(false)
  }

  const install = async () => {
    await promptInstall()       // đồng ý hay không cũng ẩn banner (module tự clear event)
    setInstallable(false)
  }

  return (
    <div role="dialog" style={{
      position: 'fixed', left: 16, right: 16, bottom: 16, zIndex: 9998,
      margin: '0 auto', maxWidth: 400,
      background: '#fff', border: '1px solid #d7dde5', borderRadius: 12,
      boxShadow: '0 8px 24px rgba(0,0,0,.14)', padding: '14px 16px',
      fontSize: 14, color: '#1f2937',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <img src="/pwa-192.png" alt="" width={36} height={36} style={{ borderRadius: 8 }} />
        <div>
          <div style={{ fontWeight: 600 }}>Cài ứng dụng DEGO Thu Mua</div>
          {showIOS
            ? <div style={{ fontSize: 12.5, color: '#4b5563' }}>Bấm <b>Chia sẻ</b> <i className="ti ti-share" /> → <b>Thêm vào MH chính</b></div>
            : <div style={{ fontSize: 12.5, color: '#4b5563' }}>Mở nhanh như app, toàn màn hình.</div>}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button className="btn ghost" onClick={dismissForever}>Không hỏi lại</button>
        {!showIOS && <button className="btn" onClick={install}>Cài đặt</button>}
      </div>
    </div>
  )
}
