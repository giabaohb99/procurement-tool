import { useEffect, useState } from 'react'
import { toast } from '../../components/toast'
import { pushSupported, isPushSubscribed, subscribePush, unsubscribePush } from '../../push'

/** Bật/tắt thông báo đẩy cho ĐÚNG thiết bị đang dùng (mỗi máy/điện thoại đăng ký riêng). */
export default function PushNotificationCard() {
  const [supported, setSupported] = useState(true)
  const [subscribed, setSubscribed] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!pushSupported()) { setSupported(false); return }
    isPushSubscribed().then(setSubscribed).catch(() => {})
  }, [])

  async function toggle() {
    setBusy(true)
    try {
      if (subscribed) { await unsubscribePush(); setSubscribed(false); toast.success('Đã tắt thông báo trên thiết bị này') }
      else { await subscribePush(); setSubscribed(true); toast.success('Đã bật thông báo trên thiết bị này') }
    } catch (e: any) {
      toast.error(e?.message || 'Không bật được thông báo')
    } finally { setBusy(false) }
  }

  return (
    <div className="card">
      <h3 className="sec-title" style={{ marginTop: 0 }}>
        <i className="ti ti-bell" style={{ marginRight: 8, color: '#b6c2d9' }} />Thông báo đẩy trên thiết bị này
      </h3>
      {/* Trạng thái hiện tại nói thẳng bật/tắt, không bắt người dùng suy ra từ nhãn nút */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span
          style={{
            width: 8, height: 8, borderRadius: '50%', flex: 'none',
            background: !supported ? '#cbd5e1' : subscribed ? 'var(--green)' : '#cbd5e1',
          }}
        />
        <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--navy)' }}>
          {!supported ? 'Trình duyệt không hỗ trợ' : subscribed ? 'Đang bật' : 'Đang tắt'}
        </span>
      </div>
      <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12, lineHeight: 1.55 }}>
        Nhận thông báo (gửi duyệt, được phân công phụ trách…) ngay cả khi không mở app.
        Cài đặt này áp dụng riêng cho từng thiết bị.
      </div>
      {!supported ? (
        <div style={{ fontSize: 13, color: 'var(--muted)' }}>Hãy dùng Chrome/Edge/Safari bản mới để bật thông báo đẩy.</div>
      ) : (
        <button className={subscribed ? 'btn ghost' : 'btn'} disabled={busy} onClick={toggle}>
          <i className={subscribed ? 'ti ti-bell-off' : 'ti ti-bell'} />
          {busy ? 'Đang xử lý…' : subscribed ? 'Tắt thông báo' : 'Bật thông báo'}
        </button>
      )}
      <div className="me-note">
        <i className="ti ti-device-mobile" />
        <span><b>Trên iPhone/iPad:</b> cần "Thêm vào màn hình chính" rồi mở app từ đó trước khi bật.</span>
      </div>
    </div>
  )
}
