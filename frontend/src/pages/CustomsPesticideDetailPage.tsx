// duoc-CR-493 — CHI TIẾT MỘT THUỐC BVTV (bản cũ): `/customs-prices/pesticides/:id`.
//
// Trang riêng thay cho hộp thoại, đồng bộ bản v2 (duoc-CR-492): tiêu đề + nút Sửa / Xóa ở đầu, thẻ
// «Thông tin đăng ký», bảng «Phạm vi sử dụng» có tiêu đề + câu giải thích, lịch sử thao tác cuối
// trang. Nút lùi quay về ĐÚNG chỗ đã mở trang (bộ lọc của thẻ Thuốc BVTV nằm trên URL, hoặc mục
// Pháp lý) nhờ `state.from`; mở thẳng link thì về thẻ Thuốc BVTV.
// Quyền: xem theo `customs_price.read`; Sửa / Xóa theo khóa riêng `customs_pesticide` (duoc-CR-490).
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import AuditTimeline from '../components/AuditTimeline'
import DocumentAttachmentSection from '../components/DocumentAttachmentSection'
import { askConfirm } from '../components/confirm'
import TableScroll from '../components/TableScroll'
import { toast } from '../components/toast'
import CustomsPesticideForm from '../components/customs/CustomsPesticideForm'
import CustomsPesticideInfoCard from '../components/customs/CustomsPesticideInfoCard'
import CustomsPesticideLookup from '../components/customs/CustomsPesticideLookup'
import CustomsPesticideRelated from '../components/customs/CustomsPesticideRelated'
import { customsSectionPath } from '../config/customs-sections'
import { extractPesticideErrorMessage } from '../utils/customs-pesticide'
import { formatBannedLabel } from '../utils/customs-regulation'

export default function CustomsPesticideDetailPage() {
  const { can } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { id } = useParams()
  const pesticideId = Number(id) || 0
  const backUrl = (location.state as { from?: string } | null)?.from || customsSectionPath('pesticides')
  const canWrite = can('customs_pesticide', 'write')
  const canDelete = can('customs_pesticide', 'delete')

  const [data, setData] = useState<any>(null)
  const [missing, setMissing] = useState(false)
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    api.get(`/api/customs/pesticides/${pesticideId}`, { _silent: true } as any)
      .then((r) => { setData(r.data.data); setMissing(false) })
      .catch(() => setMissing(true))
    //  duoc-CR-494 — tệp đính kèm của thuốc (xem theo `customs_price.read`, xem `READ_PARENT` backend).
    api.get('/api/attachments', { params: { entity: 'customs_pesticide', entity_id: pesticideId }, _silent: true } as any)
      .then((r) => setFiles(r.data.data || []))
      .catch(() => setFiles([]))
    //  Nhật ký đọc theo quyền `audit` / `setting` — thiếu quyền thì im lặng, chỉ không có lịch sử.
    api.get('/api/audit-logs', { params: { entity: 'customs_pesticide', entity_id: pesticideId }, _silent: true } as any)
      .then((r) => setLogs(Array.isArray(r.data.data) ? r.data.data : []))
      .catch(() => setLogs([]))
  }, [pesticideId])
  useEffect(() => { load() }, [load])

  async function remove() {
    if (busy || !data) return
    const ok = await askConfirm({
      title: 'Xóa thuốc BVTV',
      message: data.is_manual
        ? `Xóa «${data.trade_name}»? Không hoàn tác được.`
        : `Xóa «${data.trade_name}»? Thuốc này lấy từ bản cào — lần «Nạp danh mục» sau sẽ thêm lại nó theo nguồn.`,
      confirmText: 'Xóa',
    })
    if (!ok) return
    setBusy(true)
    try {
      await api.delete(`/api/customs/pesticides/${pesticideId}`)
      toast.success('Đã xóa thuốc BVTV')
      navigate(backUrl, { replace: true })
    } catch (e) {
      toast.error(extractPesticideErrorMessage(e, 'Không xóa được'))
    } finally {
      setBusy(false)
    }
  }

  //  Tab thân trang trên URL — gửi link là mở đúng tab; giá trị lạ về tab đầu.
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') === 'related' ? 'related' : 'info'
  function setTab(next: 'info' | 'related') {
    setSearchParams((cur) => {
      const p = new URLSearchParams(cur)
      if (next === 'info') p.delete('tab'); else p.set('tab', next)
      return p
    }, { replace: true })
  }

  const backButton = (
    <button className="btn ghost" title="Quay lại danh mục thuốc BVTV" aria-label="Quay lại danh mục thuốc BVTV"
      onClick={() => navigate(backUrl)}>
      <i className="ti ti-arrow-left" />
    </button>
  )

  if (!can('customs_price', 'read')) {
    return <div className="card" style={{ padding: 24, color: 'var(--muted)' }}>Tài khoản chưa được cấp quyền <b>Tra cứu thị trường</b>.</div>
  }
  if (missing) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
          {backButton}<h2 className="page-title" style={{ margin: 0 }}>Không tìm thấy thuốc BVTV</h2>
        </div>
        <div className="card" style={{ padding: 18, color: 'var(--muted)' }}>
          Thuốc này không còn trong danh mục — có thể đã bị xóa, hoặc đã thay bằng lần nạp danh mục mới.
        </div>
      </div>
    )
  }
  if (!data) return <div style={{ color: 'var(--muted)', padding: 12 }}>Đang tải thuốc BVTV…</div>

  const manual = !!data.is_manual
  //  01/10/2026 — Sửa / Xóa nằm trong thẻ đầu trang (đồng bộ v2), không còn hàng tiêu đề rời.
  const actions = (canWrite || canDelete) ? (
    <>
      {canWrite && <button className="btn ghost" onClick={() => setEditing(true)}><i className="ti ti-edit" />Sửa</button>}
      {canDelete && (
        <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} disabled={busy} onClick={remove}>
          <i className="ti ti-trash" />Xóa
        </button>
      )}
    </>
  ) : undefined
  return (
    <div>
      {/* 01/10/2026 — bố cục đồng bộ v2: THẺ ĐẦU TRANG + hai tab (Sử dụng & tài liệu · Thuốc liên quan);
          cột «Tìm thuốc khác» + «Tra cứu nhanh» bên phải, màn hẹp xuống cuối trang
          (`pesticide-detail-layout` trong index.css). */}
      <div className="pesticide-detail-layout">
      <div style={{ minWidth: 0 }}>
      {data.banned?.length > 0 && (
        <div role="alert" style={{ border: '1px solid #fecaca', background: '#fef2f2', color: '#991b1b', borderRadius: 8,
          padding: '8px 12px', fontSize: 13, marginBottom: 16 }}>
          <i className="ti ti-alert-triangle" /> <b>Có hoạt chất nằm trong danh sách cấm</b>
          <ul style={{ margin: '4px 0 0', paddingLeft: 20 }}>
            {data.banned.map((b: any) => (
              <li key={b.id}>
                <b>{b.name}</b>{b.cas_no && ` · CAS ${b.cas_no}`} — {formatBannedLabel(b.banned_year)}
                {b.legal_basis && ` (${b.legal_basis})`}
              </li>
            ))}
          </ul>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            Khớp theo tên hoạt chất giữa hai danh mục (không có số CAS để đối chiếu) — chỉ để tham khảo,
            xem lại văn bản gốc trước khi kết luận.
          </div>
        </div>
      )}

      <CustomsPesticideInfoCard data={data} leading={backButton} actions={actions} />

      {/* Hai tab theo NGHĨA nội dung: những gì nói về CHÍNH thuốc này đọc liền một mạch; thuốc KHÁC
          (cùng công ty / cùng hoạt chất) tách tab riêng. Tab nằm trên URL (`?tab=`). */}
      <div role="tablist" style={{ display: 'flex', gap: 24, borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
        <TabButton active={tab === 'info'} onClick={() => setTab('info')}>Sử dụng &amp; tài liệu</TabButton>
        <TabButton active={tab === 'related'} onClick={() => setTab('related')}>Thuốc liên quan</TabButton>
      </div>

      {tab === 'info' && (<>


      <div className="card table-card" style={{ marginBottom: 16 }}>
        <div style={{ padding: '14px 18px 8px' }}>
          <h3 className="sec-title" style={{ margin: 0 }}>Phạm vi sử dụng ({data.uses.length})</h3>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
            Thuốc được đăng ký dùng cho cây trồng nào, trị dịch hại gì, liều lượng bao nhiêu và phải ngừng
            phun trước thu hoạch bao lâu (thời gian cách ly).
          </div>
        </div>
        <TableScroll>
          <table>
            <thead><tr><th>Cây trồng</th><th>Dịch hại</th><th>Liều lượng</th><th>Thời gian cách ly</th><th>Cách dùng</th></tr></thead>
            <tbody>
              {data.uses.map((u: any) => (
                <tr key={u.id}>
                  <td>{u.crop}</td><td>{u.pest}</td><td>{u.dosage}</td><td>{u.pre_harvest_interval}</td>
                  <td style={{ whiteSpace: 'normal' }}>{u.usage}</td>
                </tr>
              ))}
              {data.uses.length === 0 && (
                <tr><td colSpan={5} className="table-empty">
                  {manual ? 'Chưa nhập phạm vi sử dụng nào — bấm «Sửa» để thêm.' : 'Nguồn không ghi phạm vi sử dụng cho thuốc này.'}
                </td></tr>
              )}
            </tbody>
          </table>
        </TableScroll>
      </div>

      {/* duoc-CR-494 — nhãn thuốc, giấy chứng nhận đăng ký, MSDS… Tải lên / xóa theo `customs_pesticide`
          (write hoặc create — khớp `_check` backend); tệp giữ qua các lần nạp vì id thuốc giữ nguyên. */}
      <DocumentAttachmentSection
        entity="customs_pesticide"
        entityId={pesticideId}
        files={files}
        title="Tệp đính kèm của thuốc"
        onRefresh={load}
      />

      <div className="card" style={{ padding: 18, marginTop: 16 }}>
        <h3 className="sec-title" style={{ marginTop: 0 }}>
          <i className="ti ti-history" style={{ marginRight: 8, color: '#b6c2d9' }} />Lịch sử thao tác
        </h3>
        {logs.length === 0 && <div style={{ color: 'var(--muted)', fontSize: 13 }}>Chưa có thao tác nào được ghi nhận.</div>}
        <AuditTimeline logs={logs} showMessage />
      </div>
      </>)}

      {tab === 'related' && <CustomsPesticideRelated pesticideId={data.id} registrant={data.registrant || ''} />}
      </div>
      <aside className="pesticide-detail-aside">
        <CustomsPesticideLookup currentPestGroup={data.pest_group || ''} />
      </aside>
      </div>

      {editing && (
        <CustomsPesticideForm pesticideId={pesticideId} onClose={() => setEditing(false)}
          onSaved={() => { setEditing(false); load() }} />
      )}
    </div>
  )
}

/** Một tab gạch chân — cùng kiểu dải tab của màn Tra cứu thị trường. */
function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" role="tab" aria-selected={active} onClick={onClick}
      style={{ background: 'none', border: 'none', padding: '8px 0', marginBottom: -1, cursor: 'pointer', fontSize: 14,
        borderBottom: active ? '2px solid var(--teal)' : '2px solid transparent',
        color: active ? 'var(--ink)' : 'var(--muted)', fontWeight: active ? 600 : 400 }}>
      {children}
    </button>
  )
}
