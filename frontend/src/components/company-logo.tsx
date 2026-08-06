import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { toast } from './toast'

/**
 * Logo / ảnh đại diện pháp nhân ở đầu trang chi tiết Công ty.
 * Chưa có logo thì hiện chữ cái đầu của MÃ công ty (vd "DEGO" → "D"); tên pháp nhân
 * hay bắt đầu bằng "CÔNG TY CỔ PHẦN…" nên lấy chữ đầu của tên sẽ ra "C" cho mọi công ty.
 */
export default function CompanyLogo({ companyId, code, name, logo }: {
  companyId: number
  code?: string
  name?: string
  logo?: string
}) {
  const { can } = useAuth()
  const canEdit = can('company', 'write') && !!companyId
  const [src, setSrc] = useState(logo || '')
  const [busy, setBusy] = useState(false)
  // Form chi tiết nạp sau khi component mount → đồng bộ lại ảnh khi dữ liệu về
  useEffect(() => { setSrc(logo || '') }, [logo])

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await api.post(`/api/companies/${companyId}/logo`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setSrc(r.data.data.logo)
      toast.success('Đã cập nhật logo')
    } catch (ex: any) {
      toast.error(ex?.response?.data?.error?.message || 'Không tải được ảnh')
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  const letter = ((code || name || '?').trim()[0] || '?').toUpperCase()
  const inner = src
    ? <img src={src} alt={name || 'Logo công ty'} style={{ objectFit: 'contain', background: '#fff' }} />
    : <span className="hero-avatar-fallback">{letter}</span>

  if (!canEdit) return <div className="hero-avatar" title="Logo công ty">{inner}</div>

  return (
    <label className="hero-avatar" title="Bấm để đổi logo">
      {inner}
      <span className="hero-avatar-edit"><i className={busy ? 'ti ti-loader' : 'ti ti-camera'} /></span>
      <input type="file" hidden accept="image/*" onChange={upload} disabled={busy} />
    </label>
  )
}
