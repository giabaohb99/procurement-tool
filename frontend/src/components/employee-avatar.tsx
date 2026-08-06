import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { toast } from './toast'
import { initialsOf } from '../utils/name'

/**
 * Ảnh đại diện nhân sự ở đầu trang chi tiết. Mặc định hiện chữ cái đầu của tên.
 * Ảnh lưu trên TÀI KHOẢN đăng nhập của nhân sự (tab_user.avatar) — cùng chỗ với ảnh
 * người dùng tự đổi ở Trang cá nhân. Nhân sự chưa có tài khoản thì chưa đổi được ảnh.
 */
export default function EmployeeAvatar({ employeeId, fullName, avatar, hasAccount }: {
  employeeId: number
  fullName?: string
  avatar?: string
  hasAccount?: boolean
}) {
  const { can } = useAuth()
  // employeeId rỗng = dữ liệu chi tiết chưa về → chưa cho bấm đổi ảnh (tránh gọi API thiếu id)
  const canEdit = can('employee', 'write') && !!hasAccount && !!employeeId
  const [src, setSrc] = useState(avatar || '')
  const [busy, setBusy] = useState(false)
  // Form chi tiết nạp sau khi component mount → đồng bộ lại ảnh khi dữ liệu về
  useEffect(() => { setSrc(avatar || '') }, [avatar])

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await api.post(`/api/employees/${employeeId}/avatar`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setSrc(r.data.data.avatar)
      toast.success('Đã cập nhật ảnh đại diện')
    } catch (ex: any) {
      toast.error(ex?.response?.data?.error?.message || 'Không tải được ảnh')
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  const inner = src
    ? <img src={src} alt={fullName || 'Ảnh đại diện'} />
    : <span className="hero-avatar-fallback">{initialsOf(fullName || '')}</span>

  if (!canEdit) {
    return (
      <div
        className="hero-avatar"
        title={hasAccount ? 'Ảnh đại diện' : 'Nhân sự chưa có tài khoản đăng nhập nên chưa đặt được ảnh'}
      >
        {inner}
      </div>
    )
  }

  return (
    <label className="hero-avatar" title="Bấm để đổi ảnh đại diện">
      {inner}
      <span className="hero-avatar-edit"><i className={busy ? 'ti ti-loader' : 'ti ti-camera'} /></span>
      <input type="file" hidden accept="image/*" onChange={upload} disabled={busy} />
    </label>
  )
}
