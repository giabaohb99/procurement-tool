import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { askConfirm } from './confirm'
import { toast } from './toast'
import DocumentUploadModal from './DocumentUploadModal'
import FileDropzone from './FileDropzone'
import { fmtSize, fileIcon } from '../utils/file-type'

export type AttachmentFile = {
  id: number
  file_id?: number
  filename: string
  url: string
  content_type?: string
  size: number
  doc_type?: string
  entity?: string
  entity_id?: number
}

// Cấu hình trạng thái hồ sơ chứng từ (màu sắc, icon, nhãn)
const DOC_STATUS_MAP: Record<string, { label: string; bg: string; color: string; border: string; icon: string }> = {
  'chưa có chứng từ': {
    label: 'Chưa có chứng từ',
    bg: '#fef2f2',
    color: '#dc2626',
    border: '#fca5a5',
    icon: 'ti-alert-circle',
  },
  'đã có thông tin chứng từ': {
    label: 'Đã có chứng từ',
    bg: '#fffbe6',
    color: '#b45309',
    border: '#fde68a',
    icon: 'ti-file-text',
  },
  'đã đủ chứng từ': {
    label: 'Đã đủ chứng từ',
    bg: '#ecfdf5',
    color: '#047857',
    border: '#6ee7b7',
    icon: 'ti-circle-check-filled',
  },
}

type Props = {
  entity: string
  entityId: number
  files: AttachmentFile[]
  editable?: boolean
  permEntity?: string
  title?: string
  isNew?: boolean
  maxSizeMb?: number
  // Thuộc tính riêng cho Đơn mua hàng (hoặc phiếu cần theo dõi hồ sơ chứng từ)
  showDocumentStatus?: boolean
  documentStatus?: string
  onDocumentStatusChange?: (val: string) => void
  showChainDetailButton?: boolean
  onRefresh: () => void
  purchaseOrderId?: number
}

// Cache nhãn loại chứng từ dùng chung toàn app
let _docTypeLabelsCache: Record<string, string> | null = null

// Modal Popup hiển thị danh sách file theo Mục / Loại chứng từ
function CategoryFilesModal({
  categoryLabel,
  files,
  canWrite,
  docTypeLabels,
  onClose,
  onDeleteFile,
  onUploadMore,
}: {
  categoryKey: string
  categoryLabel: string
  files: AttachmentFile[]
  canWrite: boolean
  docTypeLabels: Record<string, string>
  onClose: () => void
  onDeleteFile: (f: AttachmentFile) => void
  onUploadMore: () => void
}) {
  return (
    <div className="modal-backdrop" onClick={onClose} style={{ zIndex: 1000 }}>
      <div
        className="modal-card"
        style={{ maxWidth: 620, width: '92%', padding: 20, borderRadius: 12 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Modal */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 12 }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--navy)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="ti ti-folder-check" style={{ color: 'var(--teal)', fontSize: 20 }} />
            <span>{categoryLabel}</span>
            <span className="badge" style={{ background: '#e0f2fe', color: '#0369a1', fontSize: 12, fontWeight: 700, padding: '2px 9px', borderRadius: 999 }}>
              {files.length} tệp
            </span>
          </h3>
          <button className="icon-btn" onClick={onClose} title="Đóng modal">
            <i className="ti ti-x" style={{ fontSize: 18 }} />
          </button>
        </div>

        {/* Danh sách file trong loại này */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 380, overflowY: 'auto', paddingRight: 4 }}>
          {files.map((f) => {
            const ic = fileIcon(f.filename, f.content_type)
            return (
              <div
                key={f.id}
                className="doc-file-row"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '9px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--border)',
                  background: '#ffffff',
                }}
              >
                <i className={'ti ' + ic.icon} style={{ fontSize: 22, color: ic.color, flexShrink: 0 }} />

                {f.doc_type && (
                  <span
                    className="badge"
                    style={{
                      background: '#eef2ff',
                      color: '#3730a3',
                      fontSize: 11,
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: 999,
                      flexShrink: 0,
                    }}
                  >
                    {docTypeLabels[f.doc_type] || f.doc_type}
                  </span>
                )}

                <a
                  href={f.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    flex: 1,
                    minWidth: 0,
                    fontSize: 13,
                    fontWeight: 500,
                    color: 'var(--navy)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    textDecoration: 'none',
                  }}
                  title={f.filename}
                >
                  {f.filename}
                </a>

                <span style={{ color: 'var(--muted)', fontSize: 12, flexShrink: 0 }}>
                  {fmtSize(f.size)}
                </span>

                <a
                  href={f.url}
                  target="_blank"
                  rel="noreferrer"
                  download={f.filename}
                  className="icon-btn"
                  style={{ flexShrink: 0, color: 'var(--teal)' }}
                  title="Tải tệp"
                >
                  <i className="ti ti-download" style={{ fontSize: 16 }} />
                </a>

                {canWrite && (
                  <button
                    className="icon-btn"
                    style={{ flexShrink: 0 }}
                    title="Xóa tệp"
                    onClick={() => onDeleteFile(f)}
                  >
                    <i className="ti ti-trash" style={{ color: 'var(--red)', fontSize: 16 }} />
                  </button>
                )}
              </div>
            )
          })}
          {files.length === 0 && (
            <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 20, fontSize: 13 }}>
              Mục này chưa có tệp nào.
            </div>
          )}
        </div>

        {/* Footer Modal */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 18, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
          {canWrite ? (
            <button
              className="btn secondary"
              style={{ height: 34, padding: '0 14px', fontSize: 12.5, display: 'inline-flex', alignItems: 'center', gap: 6 }}
              onClick={() => {
                onClose()
                onUploadMore()
              }}
            >
              <i className="ti ti-upload" /> Upload thêm file cho mục này
            </button>
          ) : <div />}
          <button className="btn ghost" style={{ height: 34, padding: '0 16px', fontSize: 12.5 }} onClick={onClose}>
            Đóng
          </button>
        </div>
      </div>
    </div>
  )
}

export default function DocumentAttachmentSection({
  entity,
  entityId,
  files = [],
  editable = true,
  permEntity,
  title,
  isNew = false,
  maxSizeMb = 20,
  showDocumentStatus = false,
  documentStatus = 'chưa có chứng từ',
  onDocumentStatusChange,
  showChainDetailButton = false,
  onRefresh,
  purchaseOrderId,
}: Props) {
  const navigate = useNavigate()
  const { can } = useAuth()
  const pe = permEntity || entity
  // Đính kèm: cần write HOẶC create trên phiếu cha (khớp backend _check) — người yêu cầu
  // (vai trò chỉ có 'create') vẫn đính được chứng từ cho phiếu của mình.
  const canWrite = editable && (can(pe, 'write') || can(pe, 'create'))

  const [docModal, setDocModal] = useState(false)
  const [docTypeLabels, setDocTypeLabels] = useState<Record<string, string>>(_docTypeLabelsCache || {})
  const [uploadingDirect, setUploadingDirect] = useState(false)

  // Popover menu chọn trạng thái hồ sơ
  const [statusMenuOpen, setStatusMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement | null>(null)

  // Popup Modal xem danh sách file của 1 mục cụ thể
  const [selectedCategory, setSelectedCategory] = useState<{ key: string; label: string; files: AttachmentFile[] } | null>(null)

  useEffect(() => {
    if (_docTypeLabelsCache) return
    api.get('/api/attachments/doc-types')
      .then((x) => {
        const map = Object.fromEntries((x.data.data || []).map((t: any) => [t.value, t.label]))
        _docTypeLabelsCache = map
        setDocTypeLabels(map)
      })
      .catch(() => {})
  }, [])

  // Đóng status popover khi click ngoài
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setStatusMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Quy tắc tự động nhảy trạng thái
  useEffect(() => {
    if (!showDocumentStatus || !onDocumentStatusChange || isNew) return

    if (files.length > 0 && documentStatus === 'chưa có chứng từ') {
      onDocumentStatusChange('đã có thông tin chứng từ')
    } else if (files.length === 0 && documentStatus === 'đã có thông tin chứng từ') {
      onDocumentStatusChange('chưa có chứng từ')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files.length])

  // Cập nhật lại danh sách file trong modal đang mở khi files prop thay đổi
  useEffect(() => {
    if (selectedCategory) {
      const updatedFiles = files.filter((f) => (f.doc_type || 'other') === selectedCategory.key)
      setSelectedCategory((prev) => (prev ? { ...prev, files: updatedFiles } : null))
    }
  }, [files])

  // Upload kéo thả trực tiếp
  async function handleDirectDrop(filesDropped: File[]) {
    if (!filesDropped.length) return
    if (isNew || !entityId) {
      toast.error('Vui lòng lưu phiếu trước khi đính kèm file')
      return
    }
    const fd = new FormData()
    fd.append('entity', entity)
    fd.append('entity_id', String(entityId))
    fd.append('doc_type', 'other')
    if (purchaseOrderId || entity === 'purchase_order') {
      fd.append('purchase_order_id', String(purchaseOrderId || entityId))
    }
    filesDropped.forEach((f) => fd.append('files', f))

    setUploadingDirect(true)
    try {
      await api.post('/api/attachments', fd)
      toast.success('Đã tải lên tệp đính kèm')
      onRefresh()
    } catch {
      // Interceptor handles toast
    } finally {
      setUploadingDirect(false)
    }
  }

  async function handleDeleteFile(f: AttachmentFile) {
    if (!(await askConfirm({ message: `Xóa file "${f.filename}"?` }))) return
    try {
      await api.delete(`/api/attachments/${f.id}`)
      toast.success('Đã xóa file')
      onRefresh()
    } catch {
      // Interceptor handles error
    }
  }

  const currentStatusConfig = DOC_STATUS_MAP[documentStatus] || DOC_STATUS_MAP['chưa có chứng từ']

  // Nhóm danh sách file theo Loại chứng từ
  const groupedFiles = files.reduce((acc, f) => {
    const key = f.doc_type || 'other'
    if (!acc[key]) acc[key] = []
    acc[key].push(f)
    return acc
  }, {} as Record<string, AttachmentFile[]>)

  return (
    <div className="card" style={{ padding: 18, marginBottom: 16 }}>
      {/* Header Thẻ */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justify: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
          borderBottom: '1px solid var(--border)',
          paddingBottom: 12,
          marginBottom: 14,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <h3
            className="sec-title"
            style={{
              margin: 0,
              border: 'none',
              paddingBottom: 0,
              fontSize: 15,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <i className="ti ti-paperclip" style={{ color: 'var(--teal)', fontSize: 18 }} />
            {title || 'Chứng từ & Tài liệu đính kèm'}
          </h3>
          <span
            className="badge"
            style={{
              background: '#f1f5f9',
              color: '#475569',
              fontSize: 11.5,
              fontWeight: 600,
              borderRadius: 999,
              padding: '2px 8px',
            }}
          >
            {files.length} tệp
          </span>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Cụm Trạng thái Hồ sơ Chứng từ nâng cấp (Status Badge Popover UI) */}
          {showDocumentStatus && (
            <div style={{ position: 'relative' }} ref={menuRef}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 12.5, color: 'var(--muted)', fontWeight: 600 }}>Hồ sơ chứng từ:</span>
                <button
                  type="button"
                  disabled={!canWrite}
                  onClick={() => canWrite && setStatusMenuOpen((v) => !v)}
                  title={canWrite ? 'Bấm để thay đổi trạng thái hồ sơ chứng từ' : undefined}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '4px 10px',
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 700,
                    background: currentStatusConfig.bg,
                    color: currentStatusConfig.color,
                    border: `1.5px solid ${currentStatusConfig.border}`,
                    cursor: canWrite ? 'pointer' : 'default',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                    transition: 'all .15s ease-in-out',
                  }}
                >
                  <i className={'ti ' + currentStatusConfig.icon} style={{ fontSize: 14 }} />
                  <span>{currentStatusConfig.label}</span>
                  {canWrite && <i className="ti ti-chevron-down" style={{ fontSize: 12, opacity: 0.7 }} />}
                </button>
              </div>

              {/* Popover Menu chọn trạng thái */}
              {statusMenuOpen && canWrite && (
                <div
                  style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: 6,
                    width: 220,
                    background: '#ffffff',
                    borderRadius: 10,
                    boxShadow: '0 10px 25px -5px rgba(0,0,0,0.18), 0 4px 6px -2px rgba(0,0,0,0.05)',
                    border: '1px solid var(--border)',
                    zIndex: 90,
                    padding: '6px 0',
                    overflow: 'hidden',
                  }}
                >
                  <div style={{ padding: '6px 12px', fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.5px', borderBottom: '1px solid #f1f5f9' }}>
                    Cập nhật hồ sơ chứng từ
                  </div>
                  {Object.entries(DOC_STATUS_MAP).map(([statusKey, cfg]) => {
                    const isSelected = documentStatus === statusKey
                    return (
                      <button
                        key={statusKey}
                        type="button"
                        onClick={() => {
                          onDocumentStatusChange?.(statusKey)
                          setStatusMenuOpen(false)
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          width: '100%',
                          padding: '8px 12px',
                          border: 'none',
                          background: isSelected ? '#f8fafc' : 'transparent',
                          color: cfg.color,
                          fontSize: 12.5,
                          fontWeight: isSelected ? 700 : 500,
                          textAlign: 'left',
                          cursor: 'pointer',
                          transition: 'background .1s',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = '#f1f5f9')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = isSelected ? '#f8fafc' : 'transparent')}
                      >
                        <i className={'ti ' + cfg.icon} style={{ fontSize: 15 }} />
                        <span style={{ flex: 1 }}>{cfg.label}</span>
                        {isSelected && <i className="ti ti-check" style={{ fontSize: 14, color: 'var(--teal)' }} />}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Nút Upload chứng từ theo loại */}
          {!isNew && canWrite && (
            <button
              className="btn secondary"
              style={{
                height: 32,
                padding: '0 12px',
                fontSize: 12.5,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
              }}
              onClick={() => setDocModal(true)}
            >
              <i className="ti ti-upload" /> Upload chứng từ
            </button>
          )}

          {/* Nút Xem chi tiết chuỗi chứng từ liên kết (PYC -> PKS -> YCBG -> PO) */}
          {showChainDetailButton && !isNew && (
            <button
              className="btn ghost"
              style={{
                height: 32,
                padding: '0 12px',
                fontSize: 12.5,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
              }}
              title="Xem và tải toàn bộ chứng từ liên kết từ PYC, PKS, YCBG"
              onClick={() => navigate(`/documents?po=${entityId}`)}
            >
              <i className="ti ti-link" /> Chuỗi chứng từ (PYC/PKS)
            </button>
          )}
        </div>
      </div>

      {/* Nội dung danh sách File & Khung Kéo thả */}
      {isNew ? (
        <div
          style={{
            padding: '14px',
            borderRadius: 8,
            background: '#fafafa',
            border: '1px dashed var(--border)',
            textAlign: 'center',
            color: 'var(--muted)',
            fontSize: 13,
          }}
        >
          <i className="ti ti-info-circle" style={{ marginRight: 6 }} /> Vui lòng lưu phiếu trước khi đính kèm tài liệu.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* HIỂN THỊ CÁC THẺ NHÓM GỌN NHẸ (CATEGORY CHIPS) */}
          {files.length > 0 && (
            <div>
              <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--muted)', marginBottom: 8 }}>
                Các loại chứng từ (Bấm vào mục để xem chi tiết / tải file):
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {Object.entries(groupedFiles).map(([typeKey, fileList]) => {
                  const label = docTypeLabels[typeKey] || (typeKey === 'other' ? 'Tài liệu / Khác' : typeKey)
                  return (
                    <button
                      key={typeKey}
                      type="button"
                      onClick={() => setSelectedCategory({ key: typeKey, label, files: fileList })}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '8px 14px',
                        borderRadius: 8,
                        background: '#ffffff',
                        border: '1px solid var(--border)',
                        cursor: 'pointer',
                        fontSize: 13,
                        fontWeight: 600,
                        color: 'var(--navy)',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                        transition: 'all .15s ease-in-out',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--teal)'
                        e.currentTarget.style.background = '#f0fdf4'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--border)'
                        e.currentTarget.style.background = '#ffffff'
                      }}
                    >
                      <i className="ti ti-folder-check" style={{ color: 'var(--teal)', fontSize: 18 }} />
                      <span>{label}</span>
                      <span
                        className="badge"
                        style={{
                          background: '#0284c7',
                          color: '#ffffff',
                          fontSize: 11.5,
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: 999,
                        }}
                      >
                        {fileList.length} tệp
                      </span>
                      <i className="ti ti-chevron-right" style={{ fontSize: 12, color: 'var(--muted)' }} />
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Vùng kéo-thả trực tiếp */}
          {canWrite && (
            <div style={{ marginTop: files.length > 0 ? 4 : 0 }}>
              <FileDropzone
                hint="Tải nhanh: Kéo thả file trực tiếp vào đây hoặc bấm chọn file (PDF, Ảnh, Word, Excel, XML, TXT…)"
                onFiles={handleDirectDrop}
              />
              {uploadingDirect && (
                <div style={{ fontSize: 12.5, color: 'var(--teal)', marginTop: 6, fontWeight: 500 }}>
                  <i className="ti ti-loader spin" /> Đang tải tệp lên...
                </div>
              )}
            </div>
          )}

          {/* Thông tin giới hạn dung lượng file nhỏ ở dưới */}
          <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
            <i className="ti ti-info-circle" style={{ fontSize: 13 }} />
            <span>Mỗi file dung lượng tối đa <b>{maxSizeMb} MB</b>. Hỗ trợ định dạng: PDF, Ảnh (JPG, PNG, WEBP), Word, Excel, XML (Hóa đơn), TXT, CSV, Email (MSG, EML).</span>
          </div>

          {!canWrite && files.length === 0 && (
            <div
              style={{
                padding: '16px',
                borderRadius: 8,
                background: '#fafafa',
                border: '1px dashed var(--border)',
                textAlign: 'center',
                color: 'var(--muted)',
                fontSize: 13,
              }}
            >
              Chưa có tài liệu đính kèm.
            </div>
          )}
        </div>
      )}

      {/* Modal Popup danh sách file cho từng mục cụ thể */}
      {selectedCategory && (
        <CategoryFilesModal
          categoryKey={selectedCategory.key}
          categoryLabel={selectedCategory.label}
          files={selectedCategory.files}
          canWrite={canWrite}
          docTypeLabels={docTypeLabels}
          onClose={() => setSelectedCategory(null)}
          onDeleteFile={handleDeleteFile}
          onUploadMore={() => setDocModal(true)}
        />
      )}

      {/* Modal Upload chứng từ theo loại */}
      {docModal && (
        <DocumentUploadModal
          entity={entity}
          entityId={entityId}
          purchaseOrderId={purchaseOrderId || (entity === 'purchase_order' ? entityId : undefined)}
          onClose={() => setDocModal(false)}
          onDone={onRefresh}
        />
      )}
    </div>
  )
}
