import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { toast } from '../../components/toast'
import { useAuth } from '../../auth/AuthContext'
import { initialsOf } from '../../utils/name'

export type MeProfile = {
  full_name?: string
  emp_code?: string
  email?: string
  phone?: string
  department_name?: string
  position?: string
  role_name?: string
  avatar?: string
}

/**
 * Thẻ danh tính đầu trang cá nhân: ảnh đại diện (đổi được ngay tại đây), tên,
 * và các chip mã NV / chức vụ / phòng ban / vai trò — để nhìn phát biết đang xem hồ sơ ai.
 * Dải tab bên dưới (children) dính liền đáy thẻ nên danh tính và các mục là MỘT khối.
 */
export default function ProfileHero({ me, children }: { me: MeProfile | null; children?: React.ReactNode }) {
  const nav = useNavigate()
  const { user, updateUser } = useAuth()
  const [uploading, setUploading] = useState(false)
  // Ảnh lấy từ AuthContext để đổi xong hiện ngay (không phải tải lại /auth/me)
  const avatar = user?.avatar || me?.avatar || ''
  const name = me?.full_name || user?.full_name || 'Người dùng'
  const initials = initialsOf(name)

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await api.post('/api/auth/avatar', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      updateUser({ avatar: r.data.data.avatar })
      toast.success('Đã cập nhật ảnh đại diện')
    } catch {
      toast.error('Không tải được ảnh. Vui lòng thử lại.')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const chips: { icon: string; text: string; cls?: string }[] = [
    ...(me?.emp_code ? [{ icon: 'ti-id-badge-2', text: me.emp_code, cls: 'code' }] : []),
    ...(me?.position ? [{ icon: 'ti-briefcase', text: me.position }] : []),
    ...(me?.department_name ? [{ icon: 'ti-building', text: me.department_name }] : []),
    ...(me?.role_name ? [{ icon: 'ti-shield-check', text: me.role_name }] : []),
  ]

  return (
    <div className="card hero-card">
      <div className="hero-body">
        <label className="hero-avatar" title="Bấm để đổi ảnh đại diện">
          {avatar ? <img src={avatar} alt="Ảnh đại diện" /> : <span className="hero-avatar-fallback">{initials}</span>}
          <span className="hero-avatar-edit">
            <i className={uploading ? 'ti ti-loader' : 'ti ti-camera'} />
          </span>
          <input type="file" hidden accept="image/*" onChange={upload} disabled={uploading} />
        </label>

        <div style={{ minWidth: 0 }}>
          <div className="hero-name">{name}</div>
          <div className="hero-chips">
            {chips.length > 0 ? (
              chips.map((c) => (
                <span key={c.text} className={'hero-chip ' + (c.cls || '')}>
                  <i className={'ti ' + c.icon} />
                  {c.text}
                </span>
              ))
            ) : (
              <span className="hero-chip">Tài khoản chưa gắn hồ sơ nhân sự</span>
            )}
          </div>
        </div>

        <div className="hero-actions">
          <button className="btn ghost" onClick={() => nav('/notifications')}>
            <i className="ti ti-bell" />Thông báo
          </button>
        </div>
      </div>
      {children}
    </div>
  )
}
