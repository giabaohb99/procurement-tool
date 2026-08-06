import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { toast } from './toast'

type LinkedUser = { id: number; email: string; is_active: boolean; role_ids: number[] }

/**
 * Thẻ "Tài khoản đăng nhập" trên trang chi tiết Nhân sự.
 *
 * Trước đây trang nhân sự chỉ có 2 nút rời ("Đặt lại mật khẩu" / "Phân quyền tài khoản")
 * và phải BẤM VÀO mới biết nhân sự đã có tài khoản hay chưa. Thẻ này tra sẵn tài khoản
 * gắn với nhân sự rồi nói thẳng: có tài khoản chưa, email nào, còn hoạt động không,
 * đã gán vai trò gì — kèm lối đi tiếp sang màn Phân quyền.
 */
export default function EmployeeAccountCard({ employeeId, email }: { employeeId: number; email?: string }) {
  const nav = useNavigate()
  const { can } = useAuth()
  const canReadUser = can('user', 'read')
  const canSetPassword = can('employee', 'write')

  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<LinkedUser | null>(null)
  const [roleNames, setRoleNames] = useState<Record<number, string>>({})
  const [pwOpen, setPwOpen] = useState(false)
  const [pw1, setPw1] = useState('')
  const [pw2, setPw2] = useState('')
  const [saving, setSaving] = useState(false)

  async function loadUser() {
    // employeeId rỗng = form chi tiết CHƯA tải xong. Bỏ qua, nếu không axios sẽ cắt param
    // rỗng và gọi /api/users?page_size=1 → trả về user đầu danh sách (tài khoản của người khác).
    if (!canReadUser || !employeeId) { setLoading(false); return }
    setLoading(true)
    try {
      // Tra CHÍNH XÁC theo employee_id (không dựa fuzzy-search dễ sai)
      const r = await api.get('/api/users', { params: { employee_id: employeeId, page_size: 1 }, _silent: true } as any)
      setUser((r.data.data.items || [])[0] || null)
    } catch { setUser(null) } finally { setLoading(false) }
  }
  useEffect(() => { loadUser() /* eslint-disable-next-line */ }, [employeeId, canReadUser])

  // Tên vai trò để hiện chữ thay vì id — thiếu quyền đọc vai trò thì bỏ qua, không chặn thẻ
  useEffect(() => {
    if (!user?.role_ids?.length || !can('role', 'read')) return
    api.get('/api/roles', { params: { page_size: 200 }, _silent: true } as any)
      .then((r) => {
        const items = r.data.data.items || r.data.data || []
        setRoleNames(Object.fromEntries(items.map((x: any) => [x.id, x.name])))
      })
      .catch(() => {})
    // eslint-disable-next-line
  }, [user?.id])

  async function submitPassword() {
    if (pw1.length < 4) { toast.error('Mật khẩu tối thiểu 4 ký tự'); return }
    if (pw1 !== pw2) { toast.error('Hai mật khẩu không khớp'); return }
    setSaving(true)
    try {
      await api.post(`/api/employees/${employeeId}/set-password`, { password: pw1 })
      toast.success(user ? 'Đã đặt lại mật khẩu' : 'Đã tạo tài khoản đăng nhập')
      setPw1(''); setPw2(''); setPwOpen(false)
      loadUser()   // vừa tạo tài khoản → nạp lại để thẻ hiện đúng trạng thái
    } catch (e: any) {
      toast.error(e?.response?.data?.error?.message || 'Lỗi đặt mật khẩu')
    } finally { setSaving(false) }
  }

  if (!canReadUser && !canSetPassword) return null

  const roles = (user?.role_ids || []).map((id) => roleNames[id]).filter(Boolean)

  return (
    <div className="card" style={{ padding: 18 }}>
      <h3 className="sec-title" style={{ marginTop: 0 }}>
        <i className="ti ti-key" style={{ marginRight: 8, color: '#b6c2d9' }} />Tài khoản đăng nhập
      </h3>

      {loading ? (
        <div style={{ fontSize: 13, color: 'var(--muted)' }}>Đang kiểm tra…</div>
      ) : user ? (
        <>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
            <span className={'badge ' + (user.is_active ? 'ok' : 'err')}>
              {user.is_active ? 'Đang hoạt động' : 'Đã khóa'}
            </span>
            <span className="hero-chip"><i className="ti ti-mail" />{user.email}</span>
          </div>
          <div className="me-field" style={{ gridTemplateColumns: '22px 96px minmax(0,1fr)' }}>
            <i className="ti ti-shield-check" />
            <div className="me-field-label">Vai trò</div>
            <div className={'me-field-value' + (roles.length ? '' : ' empty')}>
              {roles.length
                ? roles.join(', ')
                : user.role_ids?.length
                  ? `${user.role_ids.length} vai trò`
                  : 'Chưa gán vai trò — tài khoản chưa dùng được'}
            </div>
          </div>
        </>
      ) : (
        <div className="me-note" style={{ marginTop: 0 }}>
          <i className="ti ti-alert-circle" />
          <span>
            Nhân sự này <b>chưa có tài khoản đăng nhập</b>.
            {email
              ? ' Đặt mật khẩu để tạo tài khoản, sau đó gán vai trò ở màn Phân quyền tài khoản.'
              : ' Hãy nhập Email ở form bên trên và bấm Lưu trước — tài khoản đăng nhập dùng chính email này.'}
          </span>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
        {canSetPassword && (user || email) && (
          <button className="btn ghost" onClick={() => setPwOpen((o) => !o)}>
            <i className="ti ti-key" />{user ? 'Đặt lại mật khẩu' : 'Tạo tài khoản đăng nhập'}
          </button>
        )}
        {user && can('user', 'read') && (
          <button className="btn ghost" onClick={() => nav(`/users/${user.id}`)}>
            <i className="ti ti-shield" />Phân quyền tài khoản
          </button>
        )}
      </div>

      {pwOpen && (
        <div style={{ marginTop: 14, padding: 14, border: '1px solid var(--border)', borderRadius: 12, background: '#f8fafc' }}>
          <div style={{ fontWeight: 600, color: 'var(--navy)', marginBottom: 10, fontSize: 13.5 }}>
            {user ? 'Đặt lại mật khẩu' : 'Tạo tài khoản & đặt mật khẩu'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div className="form-row">
              <label>Mật khẩu mới</label>
              <input type="password" autoComplete="new-password" value={pw1} onChange={(e) => setPw1(e.target.value)} />
            </div>
            <div className="form-row">
              <label>Nhập lại mật khẩu</label>
              <input type="password" autoComplete="new-password" value={pw2} onChange={(e) => setPw2(e.target.value)} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button className="btn" disabled={saving} onClick={submitPassword}>
              <i className="ti ti-check" />{saving ? 'Đang lưu…' : 'Xác nhận'}
            </button>
            <button className="btn ghost" onClick={() => { setPwOpen(false); setPw1(''); setPw2('') }}>Hủy</button>
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 10 }}>
            Mật khẩu tối thiểu 4 ký tự. Nhân sự dùng email để đăng nhập.
          </div>
        </div>
      )}
    </div>
  )
}
