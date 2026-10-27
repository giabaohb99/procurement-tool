// Toast nhắc cập nhật PWA: khi service worker có bản mới → hiện "Có bản mới" + nút Tải lại.
// Chỉ hoạt động ở bản build prod (devOptions.enabled=false trong vite.config).
//
// - Toast mang class `no-print` (index.css) để không lọt vào bản in khi đang hiện.
// - Có bản mới mà người dùng không bấm (kể cả bấm "Để sau") → tự tải lại lúc 0h đêm đó.
// - Tab mở cả ngày không tự biết có deploy mới (SW chỉ dò khi điều hướng) → dò lại mỗi giờ.
import { useEffect, useState } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

const UPDATE_CHECK_MS = 60 * 60 * 1000   // dò bản mới mỗi giờ
const DEADLINE_TICK_MS = 60 * 1000       // soát hạn tự tải lại mỗi phút

/** Mốc 0h của ngày kế tiếp (giờ máy người dùng). */
function nextMidnight(from: Date): number {
  const d = new Date(from)
  d.setHours(24, 0, 0, 0)
  return d.getTime()
}

export default function PwaReloadPrompt() {
  // Giữ riêng cờ "đang có bản mới": needRefresh bị tắt khi bấm "Để sau",
  // nhưng lịch tự tải lại lúc 0h vẫn phải chạy.
  const [hasUpdate, setHasUpdate] = useState(false)
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onNeedRefresh: () => setHasUpdate(true),
    onRegisteredSW: (_url, registration) => {
      if (!registration) return
      setInterval(() => {
        if (!navigator.onLine) return
        registration.update().catch(() => { /* mất mạng / máy chủ lỗi → lần sau dò tiếp */ })
      }, UPDATE_CHECK_MS)
    },
  })

  // Hẹn tự tải lại lúc 0h. Dùng nhịp soát mỗi phút thay vì một setTimeout dài,
  // vì máy ngủ qua đêm làm setTimeout trễ — thức dậy quá 0h là tải lại ngay.
  useEffect(() => {
    if (!hasUpdate) return
    const deadline = nextMidnight(new Date())
    const timer = setInterval(() => {
      if (Date.now() >= deadline) {
        clearInterval(timer)
        updateServiceWorker(true)
      }
    }, DEADLINE_TICK_MS)
    return () => clearInterval(timer)
  }, [hasUpdate, updateServiceWorker])

  if (!needRefresh) return null

  const close = () => setNeedRefresh(false)

  return (
    <div role="alert" className="no-print" style={{
      position: 'fixed', right: 16, bottom: 16, zIndex: 9999,
      background: '#fff', border: '1px solid #d7dde5', borderRadius: 12,
      boxShadow: '0 8px 24px rgba(0,0,0,.12)', padding: '14px 16px', maxWidth: 320,
      fontSize: 14, color: '#1f2937',
    }}>
      <div style={{ marginBottom: 4, fontWeight: 500 }}>
        Đã có phiên bản mới của ứng dụng.
      </div>
      <div style={{ marginBottom: 10, fontSize: 13, color: '#6b7280' }}>
        Nếu chưa tải lại, ứng dụng sẽ tự tải lại lúc 0h đêm nay.
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button className="btn ghost" onClick={close}>Để sau</button>
        <button className="btn" onClick={() => updateServiceWorker(true)}>Tải lại</button>
      </div>
    </div>
  )
}
