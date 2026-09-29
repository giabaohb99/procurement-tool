// duoc-CR-490 — hộp thêm / sửa MỘT thuốc BVTV (bản v2 chưa có form này, thiết kế riêng cho bản cũ).
// API: POST/PATCH /api/customs/pesticides — PATCH gửi ĐỦ cả bản ghi lẫn TOÀN BỘ phạm vi sử dụng
// (thay hết, không vá từng dòng con — xem `pesticide_schema.py`).
//
// Hộp không nằm trong <form> (CustomsModal dùng <div>) nên không có nguy cơ Enter tự nộp; vẫn
// khai mọi nút `type="button"` và chặn bấm đúp bằng `useRef` (không dựa vào mỗi `disabled`,
// state React chậm một nhịp render) cho chắc.
import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import DateInput from '../DateInput'
import SearchSelect from '../SearchSelect'
import { toast } from '../toast'
import CustomsModal from './CustomsModal'
import CustomsPesticideUsesEditor from './CustomsPesticideUsesEditor'
import {
  PESTICIDE_FIELD_LIMITS, PESTICIDE_STATUS_OPTIONS, PesticideForm, blankPesticideForm,
  extractPesticideErrorMessage, pesticideFormToPayload, pesticideToForm,
} from '../../utils/customs-pesticide'

export default function CustomsPesticideForm({ pesticideId, onClose, onSaved }: {
  /** Bỏ trống = THÊM mới. */
  pesticideId?: number
  onClose: () => void
  /** Nhận bản ghi vừa lưu — thêm mới xong thì trang gọi mở luôn trang chi tiết của nó. */
  onSaved: (saved: any) => void
}) {
  const isNew = pesticideId == null
  const [form, setForm] = useState<PesticideForm>(blankPesticideForm())
  const [loading, setLoading] = useState(!isNew)
  // Thuốc LẤY TỪ NGUỒN (không phải tự thêm) — sửa xong vẫn bị ghi đè ở lần «Nạp danh mục» sau.
  const [isManualSource, setIsManualSource] = useState(true)
  const [err, setErr] = useState('')
  const [saving, setSaving] = useState(false)
  const busy = useRef(false)

  useEffect(() => {
    if (isNew || pesticideId == null) return
    api.get(`/api/customs/pesticides/${pesticideId}`).then((r) => {
      setForm(pesticideToForm(r.data.data))
      setIsManualSource(!r.data.data.is_manual)
    }).finally(() => setLoading(false))
  }, [isNew, pesticideId])

  const set = (k: keyof PesticideForm, v: any) => setForm((s) => ({ ...s, [k]: v }))

  async function save() {
    if (busy.current) return
    busy.current = true
    setSaving(true)
    setErr('')
    try {
      const payload = pesticideFormToPayload(form)
      const r = isNew
        ? await api.post('/api/customs/pesticides', payload)
        : await api.patch(`/api/customs/pesticides/${pesticideId}`, payload)
      toast.success(isNew ? 'Đã thêm thuốc BVTV' : 'Đã lưu thuốc BVTV')
      onSaved(r.data.data)
    } catch (e: any) {
      setErr(extractPesticideErrorMessage(e, 'Lỗi khi lưu'))
    } finally {
      busy.current = false
      setSaving(false)
    }
  }

  return (
    <CustomsModal title={isNew ? 'Thêm thuốc BVTV' : 'Sửa thuốc BVTV'} width={880} onClose={onClose}
      footer={<>
        <button className="btn ghost" type="button" onClick={onClose}>Hủy</button>
        <button className="btn" type="button" disabled={saving || loading} onClick={save}>
          <i className="ti ti-device-floppy" />{saving ? 'Đang lưu…' : 'Lưu'}
        </button>
      </>}>
      {loading ? <div style={{ color: 'var(--muted)' }}>Đang tải…</div> : (
        <>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>
            Tên thuốc / hoạt chất vừa sửa chỉ gắn vào dòng hàng hải quan sau khi bấm «Gắn lại nhãn»
            ở mục «Cấu hình», hoặc lần «Nạp danh mục» kế tiếp.
          </div>
          {!isNew && isManualSource && (
            <div style={{ border: '1px solid #f5c26b', background: '#fff8e8', color: '#8a5a00', borderRadius: 8,
              padding: '8px 12px', fontSize: 13, marginBottom: 12 }}>
              <i className="ti ti-alert-triangle" /> Thuốc này lấy từ bản cào — lần «Nạp danh mục» sau sẽ ghi đè
              chỗ sửa tay theo nguồn.
            </div>
          )}

          <div className="form-grid">
            <div className="form-row">
              <label>Tên thuốc *</label>
              <input value={form.trade_name} maxLength={PESTICIDE_FIELD_LIMITS.trade_name}
                onChange={(e) => set('trade_name', e.target.value)} />
            </div>
            <div className="form-row">
              <label>Hoạt chất *</label>
              <input value={form.active_ingredient} maxLength={PESTICIDE_FIELD_LIMITS.active_ingredient}
                onChange={(e) => set('active_ingredient', e.target.value)} />
            </div>
            <div className="form-row">
              <label>Hàm lượng</label>
              <input value={form.concentration} maxLength={PESTICIDE_FIELD_LIMITS.concentration}
                onChange={(e) => set('concentration', e.target.value)} />
            </div>
            <div className="form-row">
              <label>Phân nhóm</label>
              <input value={form.pest_group} maxLength={PESTICIDE_FIELD_LIMITS.pest_group}
                onChange={(e) => set('pest_group', e.target.value)} />
            </div>
            <div className="form-row">
              <label>Lĩnh vực</label>
              <input value={form.sector} maxLength={PESTICIDE_FIELD_LIMITS.sector}
                onChange={(e) => set('sector', e.target.value)} />
            </div>
            <div className="form-row">
              <label>Công ty đăng ký</label>
              <input value={form.registrant} maxLength={PESTICIDE_FIELD_LIMITS.registrant}
                onChange={(e) => set('registrant', e.target.value)} />
            </div>
            <div className="form-row">
              <label>Số đăng ký</label>
              <input value={form.registration_no} maxLength={PESTICIDE_FIELD_LIMITS.registration_no}
                onChange={(e) => set('registration_no', e.target.value)} />
            </div>
            <div className="form-row">
              <label>Tình trạng</label>
              <SearchSelect value={form.status} autoSelectSingle={false} options={PESTICIDE_STATUS_OPTIONS}
                onChange={(v) => set('status', v)} />
            </div>
            <div className="form-row">
              <label>Ngày cấp đăng ký</label>
              <DateInput value={form.registered_on} onChange={(v) => set('registered_on', v)} />
            </div>
            <div className="form-row">
              <label>Ngày hết hạn đăng ký</label>
              <DateInput value={form.expires_on} onChange={(v) => set('expires_on', v)} />
            </div>
            <div className="form-row">
              <label>Nhóm độc</label>
              <input value={form.toxicity} maxLength={PESTICIDE_FIELD_LIMITS.toxicity}
                onChange={(e) => set('toxicity', e.target.value)} />
            </div>
            <div className="form-row">
              <label>Nguồn (đường dẫn)</label>
              <input value={form.source_url} maxLength={PESTICIDE_FIELD_LIMITS.source_url}
                placeholder="https://…" onChange={(e) => set('source_url', e.target.value)} />
            </div>
            <div className="form-row full">
              <label>Mô tả tóm tắt</label>
              <textarea value={form.summary} maxLength={20000} rows={3}
                placeholder="Vd: Thuốc trừ bệnh … hoạt chất …, sử dụng trên …, phòng trừ …, đăng ký bởi …"
                onChange={(e) => set('summary', e.target.value)} />
            </div>
            <div className="form-row full">
              <label>Nhóm kháng (quản lý tính kháng)</label>
              <textarea value={form.resistance} maxLength={20000} onChange={(e) => set('resistance', e.target.value)} />
            </div>
          </div>

          <h4 style={{ marginTop: 16, marginBottom: 8, fontSize: 14 }}>Phạm vi sử dụng</h4>
          <CustomsPesticideUsesEditor rows={form.uses} onChange={(uses) => set('uses', uses)} />

          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
        </>
      )}
    </CustomsModal>
  )
}
