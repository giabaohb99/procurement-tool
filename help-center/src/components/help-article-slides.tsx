import { Trash2, Upload } from 'lucide-react'
import { toast } from 'sonner'

import { api } from '@/api/client'
import { askConfirm } from '@/components/confirm-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

// Slide ảnh hướng dẫn từng bước của 1 bài viết.
// - HelpSlideGallery: chế độ xem (cuộn ngang, snap từng bước)
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
    <div className="mt-12 border-t pt-8">
      <h2 className="mb-6 text-center text-xl font-bold text-navy">Hướng dẫn từng bước</h2>
      <div className="flex snap-x snap-mandatory gap-5 overflow-x-auto pb-5">
        {slides.map((slide, index) => (
          <figure
            key={slide.id}
            className="m-0 flex w-[85%] shrink-0 snap-center flex-col overflow-hidden rounded-md border bg-card md:w-[70%]"
          >
            <div className="relative grid min-h-[15rem] place-items-center bg-muted">
              <img src={slide.image_url} alt={`Bước ${index + 1}`} loading="lazy"
                   className="max-h-[31rem] max-w-full object-contain" />
              <Badge className="absolute left-4 top-4">Bước {index + 1}</Badge>
            </div>
            {slide.caption && (
              <figcaption className="border-t bg-muted/40 px-5 py-3.5 text-[15px] text-navy">
                {slide.caption}
              </figcaption>
            )}
          </figure>
        ))}
      </div>
    </div>
  )
}

export function HelpSlideManager({
  articleId, slides, onChange,
}: {
  articleId: string
  slides: HelpSlide[]
  onChange: () => void
}) {
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
    <div className="mt-8 border-t pt-6">
      <h3 className="mb-4 text-lg font-semibold text-navy">Quản lý slide hướng dẫn</h3>
      <div className="flex flex-col gap-3">
        {slides.map((slide, index) => (
          <div key={slide.id} className="flex items-center gap-4 rounded-md border bg-card p-3">
            <img src={slide.image_url} alt="" className="size-[6.25rem] w-[9.375rem] shrink-0 rounded-lg object-cover" />
            <div className="min-w-0 flex-1">
              <Input
                defaultValue={slide.caption || ''}
                placeholder="Nhập ghi chú cho ảnh này..."
                onBlur={(e) => handleCaption(slide, e.target.value)}
                className="mb-1.5"
              />
              <small className="text-muted-foreground">Slide #{index + 1}</small>
            </div>
            <Button variant="outline" size="icon" title="Xóa slide"
                    className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => handleDelete(slide.id)}>
              <Trash2 className="size-4" />
            </Button>
          </div>
        ))}

        <button
          type="button"
          onClick={handleUpload}
          className="flex flex-col items-center gap-1.5 rounded-md border border-dashed bg-secondary p-6 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-primary"
        >
          <Upload className="size-6" />
          Nhấn để upload ảnh slide mới
        </button>
      </div>
    </div>
  )
}
