import { useState } from 'react'
import { api } from '../../api/client'
import { toast } from '../../components/toast'

/**
 * Bật/tắt EMAIL thông báo luồng duyệt cho chính tài khoản đang đăng nhập (bao-CR-349).
 *
 * Khác thẻ "Thông báo đẩy" ngay bên dưới: cái kia theo từng THIẾT BỊ, cái này theo TÀI KHOẢN.
 * Tắt rồi thì việc cần duyệt chỉ còn thấy ở chuông trong app — phải nói thẳng điều đó ra,
 * chứ không ai tự suy được từ nhãn nút.
 */
export default function EmailNotificationCard({ value }: { value?: boolean }) {
  const [on, setOn] = useState(value !== false)
  const [busy, setBusy] = useState(false)

  async function toggle() {
    const next = !on
    setBusy(true)
    try {
      await api.put('/api/auth/notify-email', { notify_email: next })
      setOn(next)
      toast.success(next ? 'Đã bật email thông báo' : 'Đã tắt email thông báo')
    } catch (e: any) {
      toast.error(e?.response?.data?.error?.message || 'Không đổi được cài đặt')
    } finally { setBusy(false) }
  }

  return (
    <div className="card">
      <h3 className="sec-title" style={{ marginTop: 0 }}>
        <i className="ti ti-mail" style={{ marginRight: 8, color: '#b6c2d9' }} />Email thông báo
      </h3>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', flex: 'none',
          background: on ? 'var(--green)' : '#cbd5e1' }} />
        <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--navy)' }}>
          {on ? 'Đang bật' : 'Đang tắt'}
        </span>
      </div>
      <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12, lineHeight: 1.55 }}>
        Thư báo về hộp thư của bạn mỗi khi có chứng từ cần duyệt, được duyệt hoặc bị trả lại.
        Cài đặt này áp cho tài khoản, không phụ thuộc thiết bị.
      </div>
      <button className={on ? 'btn ghost' : 'btn'} disabled={busy} onClick={toggle}>
        <i className={on ? 'ti ti-mail-off' : 'ti ti-mail'} />
        {busy ? 'Đang xử lý…' : on ? 'Tắt email thông báo' : 'Bật email thông báo'}
      </button>
      <div className="me-note">
        <i className="ti ti-bell" />
        <span>
          Tắt email <b>không</b> tắt thông báo: chuông trong app vẫn chạy đủ. Nhưng nếu bạn là
          người duyệt, hãy bật <b>Thông báo đẩy</b> ở thẻ bên dưới để không bỏ sót việc cần ký.
        </span>
      </div>
      <div className="me-note">
        <i className="ti ti-key" />
        <span>Thư đặt lại mật khẩu và thư cấp tài khoản vẫn gửi bình thường.</span>
      </div>
    </div>
  )
}
