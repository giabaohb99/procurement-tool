// bao-CR-496 (bản cũ) — «Bộ lọc đã lưu» + «Lưu bộ lọc này» của màn Tra cứu giá hải quan, bê từ bản v2
// (`customs-saved-filter-bar.tsx`). Bộ lọc là của RIÊNG tài khoản, lưu ở backend — đổi máy không mất
// (đại ca chốt, không dùng localStorage).
//
// Dùng CHUNG kho `/api/customs/saved-filters` với bản v2: `params` là chuỗi tham số URL với đúng tên ô
// lọc (`toSavedParams`), nên bộ lọc lưu ở bản này mở ở bản kia vẫn đúng và ngược lại.
import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { askConfirm } from '../confirm'
import CustomsModal from './CustomsModal'
import { CustomsFilters, fromSavedParams, sameSavedParams, toSavedParams } from './customs-shared'

type SavedFilter = { id: number; name: string; params: string; is_shared: boolean; updated_at: string | null }

export default function CustomsSavedFilters({ filters, onApply }: {
  /** Bộ lọc ĐANG ÁP (đã bấm Tìm) — thứ được lưu. */
  filters: CustomsFilters
  onApply: (next: CustomsFilters) => void
}) {
  const [items, setItems] = useState<SavedFilter[]>([])
  const [maxPerUser, setMaxPerUser] = useState(50)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [saveOpen, setSaveOpen] = useState(false)
  const [name, setName] = useState('')
  //  Chặn bấm đúp bằng ref đổi ngay trong tick.
  const busy = useRef(false)

  const load = useCallback(() => {
    api.get('/api/customs/saved-filters').then((r) => {
      setItems(r.data.data.items || [])
      setMaxPerUser(r.data.data.max_per_user || 50)
    }).catch(() => setItems([]))
  }, [])
  useEffect(() => { load() }, [load])

  const current = toSavedParams(filters)
  const selected = items.find((f) => f.id === selectedId) || null
  const dirty = selected !== null && !sameSavedParams(selected.params, current)
  const atCap = items.length >= maxPerUser

  function pick(value: string) {
    if (!value) { setSelectedId(null); return }
    const f = items.find((x) => String(x.id) === value)
    if (!f) return
    setSelectedId(f.id)
    onApply(fromSavedParams(f.params))
  }

  async function submitSave() {
    const trimmed = name.trim()
    if (!trimmed || busy.current) return
    busy.current = true
    try {
      const r = await api.post('/api/customs/saved-filters', { name: trimmed, params: current })
      setSelectedId(r.data.data.id)
      setSaveOpen(false)
      setName('')
      load()
    } catch { /* interceptor đã báo lỗi (trùng tên, quá số bộ…) */ } finally { busy.current = false }
  }

  async function overwrite() {
    if (!selected || busy.current) return
    busy.current = true
    try {
      await api.patch(`/api/customs/saved-filters/${selected.id}`, { params: current })
      load()
    } catch { /* interceptor đã báo lỗi */ } finally { busy.current = false }
  }

  async function removeSelected() {
    if (!selected) return
    const ok = await askConfirm({
      title: 'Xóa bộ lọc đã lưu',
      message: `Xóa bộ lọc «${selected.name}»? Điều kiện đang áp trên màn hình không đổi.`,
      confirmText: 'Xóa', danger: true,
    })
    if (!ok) return
    try {
      await api.delete(`/api/customs/saved-filters/${selected.id}`)
      setSelectedId(null)
      load()
    } catch { /* interceptor đã báo lỗi */ }
  }

  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 8, fontSize: 13 }}>
      <i className="ti ti-bookmark" style={{ color: 'var(--muted)' }} />
      <select value={selected ? String(selected.id) : ''} onChange={(e) => pick(e.target.value)}
        aria-label="Bộ lọc đã lưu" style={{ minWidth: 220 }}>
        <option value="">Bộ lọc đã lưu — không chọn</option>
        {items.map((f) => <option key={f.id} value={String(f.id)}>{f.name}</option>)}
      </select>
      {dirty && (
        <button className="btn ghost" type="button" onClick={overwrite} title="Ghi điều kiện đang áp vào bộ lọc đang chọn">
          <i className="ti ti-device-floppy" />Cập nhật
        </button>
      )}
      <button className="btn ghost" type="button" disabled={!current || atCap} onClick={() => setSaveOpen(true)}
        title={atCap ? `Mỗi người lưu tối đa ${maxPerUser} bộ lọc — xóa bớt rồi lưu lại`
          : !current ? 'Chưa áp điều kiện nào để lưu (bấm Tìm trước)' : 'Đặt tên cho tổ hợp điều kiện đang áp'}>
        <i className="ti ti-bookmark-plus" />Lưu bộ lọc này
      </button>
      {selected && (
        <button className="btn ghost" type="button" onClick={removeSelected} title="Xóa bộ lọc đang chọn">
          <i className="ti ti-trash" />Xóa
        </button>
      )}

      {saveOpen && (
        <CustomsModal title="Lưu bộ lọc này" width={460} onClose={() => setSaveOpen(false)}
          footer={<>
            <button className="btn ghost" type="button" onClick={() => setSaveOpen(false)}>Hủy</button>
            <button className="btn" type="button" disabled={!name.trim()} onClick={submitSave}>Lưu</button>
          </>}>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 8 }}>
            Đặt tên cho tổ hợp điều kiện đang áp (ví dụ «Abamectin 3.6 EC»). Lần sau chọn tên này là màn hình
            về đúng trạng thái đó. Bộ lọc là của riêng bạn, dùng được ở cả hai bản giao diện.
          </div>
          <input autoFocus value={name} maxLength={120} placeholder="Tối đa 120 ký tự" style={{ width: '100%' }}
            onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submitSave() }} />
        </CustomsModal>
      )}
    </div>
  )
}
