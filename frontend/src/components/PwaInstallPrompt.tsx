// Banner mời cài PWA (chỉ hiện sau khi đăng nhập — mount trong AppLayout).
// Chromium: bắt beforeinstallprompt → nút "Cài đặt". iOS Safari: hướng dẫn thủ công.
// "Không hỏi lại" → lưu cờ localStorage vĩnh viễn. Đã cài (standalone) → không hiện.
import { useEffect, useState } from 'react'

const DISMISS_KEY = 'pwa-install-dismissed'

// Sự kiện beforeinstallprompt (chỉ có trên Chromium) — không có sẵn trong lib.dom.d.ts
type BIPEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const isStandalone = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  (navigator as any).standalone === true

const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent)

export default function PwaInstallPrompt() {
  const [deferred, setDeferred] = useState<BIPEvent | null>(null)
  const [showIOS, setShowIOS] = useState(false)

  useEffect(() => {
    // Đã tắt vĩnh viễn hoặc đã cài (đang chạy standalone) → không làm gì
    if (localStorage.getItem(DISMISS_KEY) === '1' || isStandalone()) return

    // iOS Safari không có beforeinstallprompt → hiện hướng dẫn thủ công
    if (isIOS()) {
      setShowIOS(true)
      return
    }

    // Chromium: giữ event lại, hiện banner của mình thay vì mini-infobar
    const onBIP = (e: Event) => {
      e.preventDefault()
      setDeferred(e as BIPEvent)
    }
    const onInstalled = () => { setDeferred(null); setShowIOS(false) }
    window.addEventListener('beforeinstallprompt', onBIP)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onBIP)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  if (!deferred && !showIOS) return null

  const dismissForever = () => {
    localStorage.setItem(DISMISS_KEY, '1')
    setDeferred(null)
    setShowIOS(false)
  }

  const install = async () => {
    if (!deferred) return
    await deferred.prompt()
    await deferred.userChoice   // 'accepted' | 'dismissed' — dù chọn gì cũng ẩn banner
    setDeferred(null)
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
