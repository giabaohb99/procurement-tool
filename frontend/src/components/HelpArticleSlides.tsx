import { api } from '../api/client'
import { askConfirm } from './confirm'
import { toast } from './toast'

// Slide ảnh hướng dẫn từng bước của 1 bài viết HDSD.
// - HelpSlideGallery: chế độ xem (scroll ngang, snap từng bước)
// - HelpSlideManager: chế độ sửa (đổi ghi chú, xóa, upload thêm)

export interface HelpSlide {
  id: number
  article_id: number
  image_url: string
  caption?: string | null
  step_order: number
}

/** Mở hộp chọn file ảnh, trả về File hoặc null nếu user hủy. */
function pickImage(): Promise<File | null> {
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = () => resolve(input.files?.[0] || null)
    input.click()
  })
}

/** Upload 1 ảnh lên storage, trả về URL công khai. */
export async function uploadHelpImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.post('/api/v1/help-center/upload-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data.data.url
}

export function HelpSlideGallery({ slides }: { slides: HelpSlide[] }) {
  if (!slides.length) return null

  return (
    <div style={{ marginTop: 48, paddingTop: 32, borderTop: '1px solid var(--border)' }}>
      <h2 style={{ marginBottom: 24, textAlign: 'center', fontSize: 22 }}>Hướng dẫn từng bước</h2>
      <div className="hc-slide-scroller">
        {slides.map((slide, index) => (
          <div key={slide.id} className="hc-slide-item">
            <div className="hc-slide-image">
              <img src={slide.image_url} alt={`Bước ${index + 1}`} loading="lazy" />
              <span className="hc-slide-badge">Bước {index + 1}</span>
            </div>
            {slide.caption && <div className="hc-slide-caption">{slide.caption}</div>}
          </div>
        ))}
      </div>
    </div>
  )
}

interface HelpSlideManagerProps {
  articleId: string
  slides: HelpSlide[]
  onChange: () => void
}

export function HelpSlideManager({ articleId, slides, onChange }: HelpSlideManagerProps) {
  const handleUpload = async () => {
    const file = await pickImage()
    if (!file) return
    try {
      const url = await uploadHelpImage(file)
      await api.post(`/api/v1/help-center/${articleId}/slides`, {
        image_url: url,
        caption: '',
        step_order: slides.length + 1,
      })
      toast.success('Đã thêm slide')
      onChange()
    } catch {
      // interceptor đã toast lỗi
    }
  }

  const handleDelete = async (slideId: number) => {
    const ok = await askConfirm({ message: 'Xóa slide này?', confirmText: 'Xóa' })
    if (!ok) return
    await api.delete(`/api/v1/help-center/slides/${slideId}`)
    onChange()
  }

  const handleCaption = async (slide: HelpSlide, caption: string) => {
    if (caption === (slide.caption || '')) return
    await api.put(`/api/v1/help-center/slides/${slide.id}`, { caption })
    onChange()
  }

  return (
    <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--border)' }}>
      <h3 style={{ marginBottom: 16, fontSize: 17 }}>Quản lý slide hướng dẫn</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {slides.map((slide, index) => (
          <div key={slide.id} className="hc-slide-row">
            <img src={slide.image_url} alt=""
                 style={{ width: 150, height: 100, objectFit: 'cover', borderRadius: 8, flexShrink: 0 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <input
                defaultValue={slide.caption || ''}
                placeholder="Nhập ghi chú cho ảnh này..."
                onBlur={(e) => handleCaption(slide, e.target.value)}
                style={{ width: '100%', marginBottom: 6 }}
              />
              <small style={{ color: 'var(--muted)' }}>Slide #{index + 1}</small>
            </div>
            <button className="btn err" onClick={() => handleDelete(slide.id)} title="Xóa slide">
              <i className="ti ti-trash" />
            </button>
          </div>
        ))}

        <div className="hc-slide-drop" onClick={handleUpload}>
          <i className="ti ti-upload" style={{ fontSize: 26, display: 'block', marginBottom: 6 }} />
          Nhấn để upload ảnh slide mới
        </div>
      </div>
    </div>
  )
}
