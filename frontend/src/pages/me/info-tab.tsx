import { Link } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { TICKET_ENABLED } from '../../config/features'
import ChangePasswordCard from './change-password-card'
import PushNotificationCard from './push-notification-card'
import SignatureCard from './signature-card'
import type { MeProfile } from './profile-hero'

// Hồ sơ nhân sự do bộ phận Nhân sự quản lý — trang này chỉ HIỂN THỊ, không sửa được.
const HR_FIELDS: { key: keyof MeProfile; label: string; icon: string }[] = [
  { key: 'full_name', label: 'Họ và tên', icon: 'ti-user' },
  { key: 'emp_code', label: 'Mã nhân viên', icon: 'ti-id-badge-2' },
  { key: 'department_name', label: 'Phòng ban', icon: 'ti-building' },
  { key: 'position', label: 'Vị trí / Chức vụ', icon: 'ti-briefcase' },
  { key: 'role_name', label: 'Vai trò', icon: 'ti-shield-check' },
]
const CONTACT_FIELDS: { key: keyof MeProfile; label: string; icon: string }[] = [
  { key: 'email', label: 'Email / Tài khoản', icon: 'ti-mail' },
  { key: 'phone', label: 'Số điện thoại', icon: 'ti-phone' },
]

function Field({ label, icon, value }: { label: string; icon: string; value?: string }) {
  return (
    <div className="me-field">
      <i className={'ti ' + icon} />
      <div className="me-field-label">{label}</div>
      <div className={'me-field-value' + (value ? '' : ' empty')}>{value || 'Chưa cập nhật'}</div>
    </div>
  )
}

/**
 * Tab "Thông tin cá nhân" — 2 cột cố định:
 *   trái  = dữ liệu hồ sơ (chỉ xem, do Nhân sự quản lý)
 *   phải  = những thứ TỰ đổi được (mật khẩu, thông báo đẩy)
 * Tách vậy để rõ cái nào bạn sửa được, cái nào phải nhờ Nhân sự.
 */
export default function InfoTab({ me }: { me: MeProfile | null }) {
  const { can } = useAuth()
  const canAskSupport = TICKET_ENABLED && can('ticket', 'read')
  if (!me) return <div className="card" style={{ padding: 30, color: 'var(--muted)' }}>Đang tải…</div>

  return (
    <div className="detail-2cols">
      <div className="detail-col">
        <div className="card">
          <h3 className="sec-title" style={{ marginTop: 0 }}>
            <i className="ti ti-user-circle" style={{ marginRight: 8, color: '#b6c2d9' }} />Hồ sơ nhân sự
          </h3>
          {HR_FIELDS.map((f) => (
            <Field key={f.key} label={f.label} icon={f.icon} value={me[f.key] as string} />
          ))}
          <div className="me-note">
            <i className="ti ti-info-circle" />
            <span>
              Hồ sơ nhân sự và vai trò do bộ phận Nhân sự / Quản trị hệ thống cập nhật.
              Nếu thông tin chưa đúng,{' '}
              {canAskSupport ? (
                // Nối thẳng sang tab Yêu cầu hỗ trợ thay vì bắt người dùng tự đi tìm
                <Link to="/me?tab=tickets" style={{ color: 'var(--teal)', fontWeight: 600 }}>
                  gửi yêu cầu hỗ trợ
                </Link>
              ) : (
                <b>liên hệ bộ phận Nhân sự</b>
              )}{' '}
              để được chỉnh sửa.
            </span>
          </div>
        </div>

        <div className="card">
          <h3 className="sec-title" style={{ marginTop: 0 }}>
            <i className="ti ti-address-book" style={{ marginRight: 8, color: '#b6c2d9' }} />Liên hệ
          </h3>
          {CONTACT_FIELDS.map((f) => (
            <Field key={f.key} label={f.label} icon={f.icon} value={me[f.key] as string} />
          ))}
        </div>
      </div>

      <div className="detail-col">
        <SignatureCard signature={me.signature} />
        <ChangePasswordCard />
        <PushNotificationCard />
      </div>
    </div>
  )
}
