import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { toast } from './toast'
import { askConfirm } from './confirm'
import { prepareSignatureImage } from '../utils/prepare-signature-image'

/**
 * Thẻ "Chữ ký cá nhân" trên trang chi tiết Nhân sự — Nhân sự/quản trị đặt chữ ký THAY cho
 * một nhân viên (bao-CR-398).
 *
 * Trước đó chữ ký chỉ có ở Trang cá nhân (mỗi người tự tải ảnh của mình). Trên bản in Phiếu
 * đề xuất mua hàng thì ảnh chữ ký của trưởng phòng / giám đốc mới là thứ hay thiếu, mà những
 * người đó ít khi tự vào hệ thống — nên Nhân sự phải làm hộ được ngay tại hồ sơ nhân viên.
 * Bản v2 đã có thẻ này (tab Tài khoản); bản cũ thiếu nên admin không thấy chỗ nào để sửa.
 *
 * Gọi POST/DELETE /api/employees/{id}/signature (backend đòi employee.write). Ảnh lưu vào
 * tab_user.signature của TÀI KHOẢN gắn với nhân sự — nhân sự chưa có tài khoản thì backend
 * trả 400, thẻ báo phải tạo tài khoản trước (thẻ "Tài khoản đăng nhập" ngay bên trên).
 */
export default function EmployeeSignatureCard({
  employeeId, signature, hasAccount,
}: { employeeId: number; signature?: string; hasAccount?: boolean }) {
  const { can } = useAuth()
  const canEdit = can('employee', 'write')
  const [src, setSrc] = useState(signature || '')
  const [busy, setBusy] = useState(false)
  // Mặc định bật: đa số ảnh là chụp/scan chữ ký trên giấy trắng.
  const [autoRemoveBg, setAutoRemoveBg] = useState(true)
  // Form chi tiết tải xong sau khi thẻ mount → đồng bộ lại khi dữ liệu vừa tới
  useEffect(() => { setSrc(signature || '') }, [signature])

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file || !employeeId) return
    setBusy(true)
    try {
      // Xử lý lỗi (ảnh hỏng, canvas bị chặn…) thì vẫn gửi ảnh gốc, không chặn người dùng
      let toSend = file
      try { toSend = await prepareSignatureImage(file, { removeBg: autoRemoveBg }) }
      catch { toast.error('Không xử lý được ảnh — giữ nguyên ảnh gốc') }
      const fd = new FormData()
      fd.append('file', toSend)
      const r = await api.post(`/api/employees/${employeeId}/signature`, fd,
        { headers: { 'Content-Type': 'multipart/form-data' }, _silent: true } as any)
      setSrc(r.data.data.signature)
      toast.success('Đã cập nhật chữ ký')
    } catch (ex: any) {
      toast.error(ex?.response?.data?.error?.message || 'Không tải được ảnh chữ ký')
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  async function remove() {
    if (!(await askConfirm({ message: 'Gỡ ảnh chữ ký của nhân sự này?' }))) return
    setBusy(true)
    try {
      await api.delete(`/api/employees/${employeeId}/signature`, { _silent: true } as any)
      setSrc('')
      toast.success('Đã gỡ chữ ký')
    } catch (ex: any) {
      toast.error(ex?.response?.data?.error?.message || 'Không gỡ được chữ ký')
    } finally {
      setBusy(false)
    }
  }

  // Người chỉ đọc hồ sơ: thấy ảnh (để biết đã có chữ ký chưa) nhưng không có nút sửa.
  // `hasAccount` undefined = API chưa cho biết → cứ mở nút, backend sẽ chặn nếu chưa có tài khoản.
  const noAccount = hasAccount === false

  return (
    <div className="card" style={{ padding: 18 }}>
      <h3 className="sec-title" style={{ marginTop: 0 }}>
        <i className="ti ti-signature" style={{ marginRight: 8, color: '#b6c2d9' }} />Chữ ký cá nhân
      </h3>

      {/* Khung xem trước nền ô carô để thấy rõ chữ ký PNG nền trong */}
      <div className="sign-preview">
        {src
          ? <img src={src} alt="Chữ ký cá nhân" />
          : <span className="sign-empty"><i className="ti ti-signature" />Chưa có chữ ký</span>}
      </div>

      {canEdit && (
        <>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, fontWeight: 500,
                          color: 'var(--muted)', margin: '12px 0 0' }}>
            <input type="checkbox" checked={autoRemoveBg} disabled={busy}
                   onChange={(e) => setAutoRemoveBg(e.target.checked)} />
            Tự động xóa nền trắng của ảnh
          </label>

          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
            <label className="btn ghost"
                   style={{ cursor: busy || noAccount ? 'default' : 'pointer', opacity: busy || noAccount ? 0.6 : 1 }}>
              <i className={busy ? 'ti ti-loader' : 'ti ti-upload'} />
              {busy ? 'Đang xử lý…' : src ? 'Đổi chữ ký' : 'Tải chữ ký lên'}
              <input type="file" hidden accept="image/*" onChange={upload} disabled={busy || noAccount} />
            </label>
            {src && (
              <button className="btn ghost" disabled={busy} onClick={remove}
                      style={{ color: 'var(--red)', borderColor: 'var(--red)' }}>
                <i className="ti ti-trash" />Gỡ chữ ký
              </button>
            )}
          </div>
        </>
      )}

      <div className="me-note">
        <i className={'ti ' + (noAccount ? 'ti-alert-circle' : 'ti-info-circle')} />
        <span>
          {noAccount
            ? 'Nhân sự này chưa có tài khoản đăng nhập — hãy tạo tài khoản ở thẻ "Tài khoản đăng nhập" trước, rồi mới đặt được chữ ký.'
            : 'Ảnh chữ ký in lên các ô ký (Giám đốc, TP/BP mua hàng, TP/BP đề xuất, Người lập) của bản in phiếu. ' +
              'Chụp/scan chữ ký viết bằng bút đậm trên giấy trắng — hệ thống tự tách nền thành ảnh trong suốt; ' +
              'ảnh đã là PNG nền trong sẵn thì bỏ chọn "Tự động xóa nền". Nhân viên cũng tự đổi được ở Trang cá nhân.'}
        </span>
      </div>
    </div>
  )
}
