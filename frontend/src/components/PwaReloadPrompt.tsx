// Toast nhắc cập nhật PWA: khi service worker bản mới đã chiếm quyền → hiện "Có bản mới" + nút Tải lại.
// Chỉ hoạt động ở bản build prod (devOptions.enabled=false trong vite.config).
//
// duoc-CR-685:
// - SW chạy chế độ autoUpdate (tự kích hoạt, không chờ bấm). Tab này đã chạy JS cũ nên vẫn phải
//   tải lại trang mới lên bản mới — popup để người dùng chủ động, không thì tự tải lại lúc 0h.
// - Tab bản này trả lời tin "PWA_VERSION_PING" của SW mới (public/sw-update-old-clients.js);
//   tab nào im lặng bị coi là bản cũ và SW tự tải lại ngay.
// - Toast mang class `no-print` (index.css) để không lọt vào bản in khi đang hiện.
// - Tab mở cả ngày không tự biết có deploy mới (SW chỉ dò khi điều hướng) → dò lại mỗi giờ.
import { useEffect, useState } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

const UPDATE_CHECK_MS = 60 * 60 * 1000   // dò bản mới mỗi giờ
const DEADLINE_TICK_MS = 60 * 1000       // soát hạn tự tải lại mỗi phút

// Gắn ngay khi nạp module (trước cả lúc React dựng cây) để không lỡ tin hỏi của SW.
navigator.serviceWorker?.addEventListener('message', (event) => {
  if (event.data?.type === 'PWA_VERSION_PING') event.ports[0]?.postMessage('handled')
})

/** Mốc 0h của ngày kế tiếp (giờ máy người dùng). */
function nextMidnight(from: Date): number {
  const d = new Date(from)
  d.setHours(24, 0, 0, 0)
  return d.getTime()
}

export default function PwaReloadPrompt() {
  // hasUpdate giữ lịch tự tải lại lúc 0h; showPrompt chỉ là popup ("Để sau" tắt popup, không tắt lịch).
  const [hasUpdate, setHasUpdate] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)

  useRegisterSW({
    // autoUpdate mặc định reload ngay khi SW mới kích hoạt — thay bằng popup + hẹn 0h.
    onNeedReload: () => {
      setHasUpdate(true)
      setShowPrompt(true)
    },
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
        window.location.reload()
      }
    }, DEADLINE_TICK_MS)
    return () => clearInterval(timer)
  }, [hasUpdate])

  if (!showPrompt) return null

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
        <button className="btn ghost" onClick={() => setShowPrompt(false)}>Để sau</button>
        <button className="btn" onClick={() => window.location.reload()}>Tải lại</button>
      </div>
    </div>
  )
}
