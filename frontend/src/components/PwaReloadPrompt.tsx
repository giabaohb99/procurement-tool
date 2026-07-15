// Toast nhắc cập nhật PWA: khi service worker có bản mới → hiện "Có bản mới" + nút Tải lại.
// Chỉ hoạt động ở bản build prod (devOptions.enabled=false trong vite.config).
import { useRegisterSW } from 'virtual:pwa-register/react'

export default function PwaReloadPrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW()

  if (!needRefresh) return null

  const close = () => setNeedRefresh(false)

  return (
    <div role="alert" style={{
      position: 'fixed', right: 16, bottom: 16, zIndex: 9999,
      background: '#fff', border: '1px solid #d7dde5', borderRadius: 12,
      boxShadow: '0 8px 24px rgba(0,0,0,.12)', padding: '14px 16px', maxWidth: 320,
      fontSize: 14, color: '#1f2937',
    }}>
      <div style={{ marginBottom: 10, fontWeight: 500 }}>
        Đã có phiên bản mới của ứng dụng.
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button className="btn ghost" onClick={close}>Để sau</button>
        <button className="btn" onClick={() => updateServiceWorker(true)}>Tải lại</button>
      </div>
    </div>
  )
}
