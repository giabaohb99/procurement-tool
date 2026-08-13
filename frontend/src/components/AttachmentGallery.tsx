import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { askConfirm } from './confirm'
import FileDropzone from './FileDropzone'
import Lightbox from './Lightbox'

// Gallery ẢNH đính kèm tổng quát (tái dùng cho product, purchase_request_line_image, …).
// Upload nhiều ảnh, xóa, kéo-thả sắp thứ tự, click ảnh mở lightbox next/prev.
// Ảnh đầu (sort_order nhỏ nhất) = thumbnail. readOnly ép chỉ xem (bỏ upload/xóa/kéo-thả).
//
// CHẾ ĐỘ CHỜ LƯU (`onPendingChange` + `entityId` rỗng): đối tượng chưa có id thật nên chưa
// gọi được API đính kèm — giữ File ở client, xem trước bằng blob URL, và để TRANG CHA tải
// lên ngay sau khi lưu. Có chế độ này vì bắt người dùng "lưu phiếu rồi mới đính kèm được"
// là bắt làm 2 lượt cho một việc.
type Att = { id: number; url: string; filename?: string; content_type?: string }

const isImg = (a: Att) =>
  (a.content_type || '').startsWith('image/') ||
  /\.(jpe?g|png|webp|gif)$/i.test(a.filename || '')

type Props = {
  entity: string          // vd 'product' | 'purchase_request_line_image'
  entityId: number
  permEntity?: string     // entity để check quyền (mặc định = entity)
  readOnly?: boolean      // ép chỉ xem bất kể quyền
  title?: string          // tiêu đề <h3>; mặc định 'Ảnh'
  maxHint?: string        // dòng hint dropzone
  onImages?: (imgs: Att[]) => void   // báo danh sách ảnh sau mỗi lần load (để cha đối chiếu/gate nút)
  headerRight?: React.ReactNode      // nội dung phụ bên phải tiêu đề (vd nút "So sánh")
  compact?: boolean                  // thu gọn: thumbnail nhỏ + padding hẹp (dùng khi nhúng trên đầu popup)
  pendingFiles?: File[]              // chế độ CHỜ LƯU: file cha đang giữ (chưa có entityId để upload)
  onPendingChange?: (files: File[]) => void   // báo cha danh sách file mới sau khi thêm/xóa/sắp xếp
}

export default function AttachmentGallery({ entity, entityId, permEntity, readOnly, title, maxHint, onImages, headerRight, compact, pendingFiles, onPendingChange }: Props) {
  const { can } = useAuth()
  const pe = permEntity || entity
  // Backend đính kèm chỉ xét mode "manage" = write|create trên entity CHA (KHÔNG xét delete).
  const canManage = !readOnly && (can(pe, 'write') || can(pe, 'create'))
  const canDelete = canManage
  // Chưa có id thật + cha nhận file chờ -> chạy chế độ CHỜ LƯU (không gọi API đính kèm)
  const choLuu = !entityId && !!onPendingChange

  const [saved, setSaved] = useState<Att[]>([])
  const [previews, setPreviews] = useState<Att[]>([])
  const imgs = choLuu ? previews : saved
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [lightboxIdx, setLightboxIdx] = useState<number | null>(null)
  const [dragIdx, setDragIdx] = useState<number | null>(null)

  async function load() {
    setLoading(true)
    try {
      const r = await api.get('/api/attachments', { params: { entity, entity_id: entityId }, _silent: true } as any)
      const list = (r.data.data || []).filter(isImg)
      setSaved(list); onImages?.(list)
    } catch { setSaved([]); onImages?.([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { if (entityId) load() }, [entity, entityId])

  // Chờ lưu: dựng ảnh xem trước từ File. id ÂM để không lẫn với link đính kèm thật;
  // thu hồi blob URL khi danh sách đổi/rời màn (không thu hồi là rò bộ nhớ).
  useEffect(() => {
    if (!choLuu) return
    const list: Att[] = (pendingFiles || []).map((f, i) => ({
      id: -(i + 1), url: URL.createObjectURL(f), filename: f.name, content_type: f.type,
    }))
    setPreviews(list); onImages?.(list)
    return () => { list.forEach((a) => URL.revokeObjectURL(a.url)) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [choLuu, pendingFiles])

  async function onUpload(files: FileList) {
    if (!files.length) return
    if (choLuu) { onPendingChange!([...(pendingFiles || []), ...Array.from(files)]); return }
    const fd = new FormData()
    fd.append('entity', entity)
    fd.append('entity_id', String(entityId))
    Array.from(files).forEach((f) => fd.append('files', f))   // doc_type để rỗng
    setUploading(true)
    try { await api.post('/api/attachments', fd); await load() }
    finally { setUploading(false) }
  }

  async function onDelete(a: Att) {
    if (!(await askConfirm({ message: `Xóa ảnh "${a.filename || ''}"?` }))) return
    if (choLuu) {
      const i = imgs.findIndex((x) => x.id === a.id)
      onPendingChange!((pendingFiles || []).filter((_, idx) => idx !== i))
      return
    }
    await api.delete(`/api/attachments/${a.id}`)
    await load()
  }

  async function onDrop(toIdx: number) {
    if (dragIdx === null || dragIdx === toIdx) { setDragIdx(null); return }
    if (choLuu) {
      const arr = [...(pendingFiles || [])]
      const [f] = arr.splice(dragIdx, 1)
      arr.splice(toIdx, 0, f)
      setDragIdx(null); onPendingChange!(arr)
      return
    }
    const next = [...imgs]
    const [moved] = next.splice(dragIdx, 1)
    next.splice(toIdx, 0, moved)
    setDragIdx(null)
    setSaved(next)   // optimistic
    try {
      await api.patch('/api/attachments/reorder', {
        entity, entity_id: entityId, ordered_link_ids: next.map((x) => x.id),
      })
    } catch { await load() }   // lỗi → đồng bộ lại thứ tự thật
  }

  const thumb = compact ? 64 : 92   // cạnh ô ảnh (px)

  return (
    <div className="card" style={{ padding: compact ? 12 : 18 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: compact ? 8 : 12 }}>
        <h3 style={{ fontSize: 14, color: 'var(--navy)', margin: 0 }}>
          <i className="ti ti-photo" /> {title || 'Ảnh'} ({imgs.length})
        </h3>
        {headerRight}
      </div>

      {canManage && (
        <div style={{ marginBottom: 12 }}>
          <FileDropzone onFiles={onUpload} accept="image/*" hint={maxHint || 'JPG, PNG, WEBP · tối đa 5MB/ảnh · có thể chọn nhiều'} />
          {uploading && <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 6 }}>Đang tải lên…</div>}
        </div>
      )}

      {loading && !choLuu ? (
        <div style={{ color: '#999', fontSize: 13 }}>Đang tải…</div>
      ) : imgs.length === 0 ? (
        <div style={{ color: '#999', fontSize: 13 }}>Chưa có ảnh nào.</div>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          {imgs.map((a, i) => (
            <div key={a.id}
              draggable={canManage}
              onDragStart={() => setDragIdx(i)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => onDrop(i)}
              style={{ position: 'relative', width: thumb, height: thumb, borderRadius: 8, overflow: 'hidden',
                border: '1px solid var(--border)', background: '#fff',
                cursor: canManage ? 'grab' : 'zoom-in', opacity: dragIdx === i ? 0.4 : 1 }}
              title={a.filename || ''}>
              <img src={a.url} alt={a.filename || ''} onClick={() => setLightboxIdx(i)}
                style={{ width: '100%', height: '100%', objectFit: 'cover', cursor: 'zoom-in' }} />
              {i === 0 && (
                <span style={{ position: 'absolute', left: 4, bottom: 4, fontSize: 10, padding: '1px 5px',
                  borderRadius: 4, background: 'rgba(0,0,0,.6)', color: '#fff' }}>Thumbnail</span>
              )}
              {canDelete && (
                <button onClick={(e) => { e.stopPropagation(); onDelete(a) }} title="Xóa ảnh"
                  style={{ position: 'absolute', top: 3, right: 3, width: 22, height: 22, borderRadius: '50%',
                    border: 'none', cursor: 'pointer', background: 'rgba(220,38,38,.92)', color: '#fff', fontSize: 13, lineHeight: 1 }}>✕</button>
              )}
            </div>
          ))}
        </div>
      )}

      {canManage && imgs.length > 1 && (
        <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 8 }}>Kéo-thả để sắp xếp — ảnh đầu tiên là thumbnail.</div>
      )}

      {/* Nói rõ ảnh chưa nằm trên server: đóng trình duyệt lúc này là mất, phải bấm Lưu */}
      {choLuu && imgs.length > 0 && (
        <div style={{ fontSize: 11.5, color: 'var(--warn, #b45309)', marginTop: 8 }}>
          <i className="ti ti-clock" /> {imgs.length} ảnh đang chờ — sẽ được tải lên khi bấm Lưu phiếu.
        </div>
      )}

      {lightboxIdx !== null && (
        <Lightbox images={imgs} index={lightboxIdx} onClose={() => setLightboxIdx(null)} onNav={setLightboxIdx} />
      )}
    </div>
  )
}
