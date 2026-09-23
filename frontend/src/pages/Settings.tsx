import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { fmtDateTime } from '../utils/datetime'

type Field = { key: string; group: string; label: string; type: string; value: any; hint?: string }
type Secret = { key: string; group: string; label: string; configured: boolean }
type LogRow = { id: number; message: string; by: string; at: string }

const GROUP_TITLE: Record<string, string> = {
  workflow: 'Quy trình duyệt', email: 'Email (SMTP)', storage: 'Lưu trữ (R2 / S3)',
}

export default function Settings() {
  const { can } = useAuth()
  const canWrite = can('setting', 'write')
  const [fields, setFields] = useState<Field[]>([])
  const [secrets, setSecrets] = useState<Secret[]>([])
  const [secretVals, setSecretVals] = useState<Record<string, string>>({})
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('')
  const [testTo, setTestTo] = useState('')
  const [busy, setBusy] = useState('')

  const [logs, setLogs] = useState<LogRow[]>([])
  const [logErr, setLogErr] = useState('')

  async function load() {
    const r = await api.get('/api/settings'); setFields(r.data.data.fields); setSecrets(r.data.data.secrets)
  }

  /**
   * Nhật ký của chính màn này. Đi bằng đường chung `/api/audit-logs` lọc
   * `entity=setting` — không truyền `page` thì backend trả về MẢNG đơn.
   *
   * Lỗi phải hiện thành lời: `client.ts` nuốt lỗi của request GET, nên bảng
   * rỗng vì 403 trông y hệt bảng rỗng vì chưa ai đổi gì.
   */
  async function loadLogs() {
    setLogErr('')
    try {
      const r = await api.get('/api/audit-logs', { params: { entity: 'setting', limit: 30 } })
      setLogs(Array.isArray(r.data.data) ? r.data.data : [])
    } catch (ex: any) {
      setLogErr(ex?.response?.data?.error?.message || 'Không đọc được nhật ký thay đổi')
    }
  }

  useEffect(() => { load(); loadLogs() }, [])

  const setVal = (key: string, v: any) => setFields((s) => s.map((f) => f.key === key ? { ...f, value: v } : f))

  async function save() {
    setErr(''); setMsg('')
    const values: any = {}; fields.forEach((f) => { values[f.key] = f.value })
    // Chỉ gửi secret nào người dùng có nhập (rỗng = giữ nguyên)
    Object.entries(secretVals).forEach(([k, v]) => { if (v && v.trim()) values[k] = v })
    try {
      const r = await api.put('/api/settings', { values })
      setFields(r.data.data.fields); setSecrets(r.data.data.secrets); setSecretVals({}); setMsg('Đã lưu cấu hình')
      loadLogs()
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  async function testEmail() {
    setErr(''); setMsg(''); setBusy('email')
    try { const r = await api.post('/api/settings/test-email', { to: testTo }); const d = r.data.data; d.ok ? setMsg(d.message) : setErr(d.message) }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi gửi thử') }
    finally { setBusy('') }
  }
  async function testStorage() {
    setErr(''); setMsg(''); setBusy('storage')
    try { const r = await api.post('/api/settings/test-storage'); const d = r.data.data; d.ok ? setMsg(d.message) : setErr(d.message) }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi kiểm tra') }
    finally { setBusy('') }
  }

  const groups = ['workflow', 'email', 'storage']
  const gFields = (g: string) => fields.filter((f) => f.group === g)
  const gSecrets = (g: string) => secrets.filter((s) => s.group === g)

  return (
    <div>
      <h2 className="page-title" style={{ marginBottom: 14 }}>Cấu hình hệ thống</h2>

      <div className="card" style={{ padding: 14, marginBottom: 16, background: '#eff6ff', border: '1px solid #bfdbfe' }}>
        <div style={{ fontSize: 13, color: '#1e40af' }}>
          <i className="ti ti-info-circle" /> Cấu hình lưu trong DB (khóa bí mật được <b>mã hóa</b>) → đổi tại đây có hiệu lực ngay, <b>không cần sửa .env hay build lại Docker</b>.
          Ô mật khẩu/khóa để trống = giữ nguyên giá trị cũ. <code>.env</code> vẫn là giá trị dự phòng khi DB chưa đặt.
        </div>
      </div>

      {groups.map((g) => (
        <div key={g} className="card" style={{ padding: 18, marginBottom: 16 }}>
          <h3 className="sec-title">{GROUP_TITLE[g]}</h3>
          <div className="form-grid">
            {gFields(g).map((f) => (
              <div className="form-row" key={f.key} style={f.hint ? { gridColumn: '1 / -1' } : undefined}>
                <label>{f.label}</label>
                {f.type === 'bool' ? (
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: canWrite ? 'pointer' : 'default', height: 40 }}>
                    <input type="checkbox" checked={!!f.value} disabled={!canWrite} onChange={(e) => setVal(f.key, e.target.checked)} style={{ width: 18, height: 18 }} />
                    {f.value ? 'Đang bật' : 'Đang tắt'}
                  </label>
                ) : (
                  <input type={f.type === 'int' ? 'number' : 'text'} value={f.value ?? ''} disabled={!canWrite}
                    onChange={(e) => setVal(f.key, f.type === 'int' ? Number(e.target.value) : e.target.value)} />
                )}
                {/* Giải thích công tắc — tránh bật/tắt nhầm rồi đổi luôn quy trình duyệt */}
                {f.hint && <div style={{ fontSize: 12.5, color: 'var(--muted)', lineHeight: 1.5, marginTop: 2 }}>{f.hint}</div>}
              </div>
            ))}
          </div>

          {/* Khóa bí mật — nhập được, không hiển thị lại (nhóm nào không có thì bỏ hẳn khối này) */}
          {gSecrets(g).length > 0 && (
          <div style={{ marginTop: 14, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 8 }}>
              <i className="ti ti-key" /> Khóa bí mật (mã hóa khi lưu, không hiển thị lại) — để trống nếu không đổi:
            </div>
            <div className="form-grid">
              {gSecrets(g).map((s) => (
                <div className="form-row" key={s.key}>
                  <label>{s.label} {s.configured
                    ? <span className="badge" style={{ background: '#dcfce7', color: '#15803d', marginLeft: 6 }}>Đã cấu hình</span>
                    : <span className="badge" style={{ background: '#fee2e2', color: '#b91c1c', marginLeft: 6 }}>Chưa</span>}
                  </label>
                  <input type="password" autoComplete="new-password" disabled={!canWrite}
                    placeholder={s.configured ? '•••••••• (để trống nếu giữ nguyên)' : 'Nhập giá trị…'}
                    value={secretVals[s.key] ?? ''} onChange={(e) => setSecretVals((v) => ({ ...v, [s.key]: e.target.value }))} />
                </div>
              ))}
            </div>
          </div>
          )}

          {/* Nút test */}
          {canWrite && (
            <div style={{ marginTop: 14, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              {g === 'email' && (
                <>
                  <input placeholder="Email nhận thử…" value={testTo} onChange={(e) => setTestTo(e.target.value)} style={{ maxWidth: 240 }} />
                  <button className="btn ghost" disabled={busy === 'email'} onClick={testEmail}><i className="ti ti-send" />Gửi email thử</button>
                </>
              )}
              {g === 'storage' && (
                <button className="btn ghost" disabled={busy === 'storage'} onClick={testStorage}><i className="ti ti-cloud-check" />Kiểm tra kết nối R2</button>
              )}
            </div>
          )}
        </div>
      ))}

      {err && <div className="err" style={{ marginBottom: 12 }}>{err}</div>}
      {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginBottom: 12 }}><i className="ti ti-check" /> {msg}</div>}

      {canWrite && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn" onClick={save}><i className="ti ti-device-floppy" />Lưu cấu hình</button>
        </div>
      )}

      {/* Nhật ký thay đổi — ai đổi ô nào, từ giá trị gì sang giá trị gì */}
      <div className="card" style={{ padding: 18, marginTop: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <h3 className="sec-title" style={{ margin: 0 }}>Lịch sử thay đổi</h3>
          <button className="btn ghost" onClick={loadLogs}><i className="ti ti-refresh" />Tải lại</button>
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 10 }}>
          30 lần cập nhật gần nhất. Giá trị của khóa bí mật <b>không</b> được ghi vào nhật ký — chỉ ghi nhận là đã đặt lại.
        </div>
        {logErr && <div className="err">{logErr}</div>}
        {!logErr && (
          <table>
            <thead>
              <tr>
                <th style={{ width: 170 }}>Thời gian</th>
                <th style={{ width: 200 }}>Người thực hiện</th>
                <th>Nội dung</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => {
                //  Dòng đầu là câu tóm tắt, phần còn lại là chi tiết từng ô.
                //  Bản ghi cũ (trước bao-CR-461) chỉ có đúng dòng tóm tắt.
                const [title, ...detail] = String(l.message || '').split('\n')
                return (
                  <tr key={l.id}>
                    <td style={{ whiteSpace: 'nowrap' }}>{fmtDateTime(l.at)}</td>
                    <td>{l.by}</td>
                    <td>
                      <div>{title}</div>
                      {detail.length > 0 && (
                        <div style={{ fontSize: 12.5, color: 'var(--muted)', whiteSpace: 'pre-line', marginTop: 3 }}>
                          {detail.join('\n')}
                        </div>
                      )}
                    </td>
                  </tr>
                )
              })}
              {logs.length === 0 && (
                <tr><td colSpan={3} style={{ color: 'var(--muted)' }}>Chưa có lần cập nhật nào được ghi nhận.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
