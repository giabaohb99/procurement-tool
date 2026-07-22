import { useRef, useState } from 'react'

// Vùng kéo-thả / bấm chọn file dùng chung (popup upload chứng từ, đính kèm dòng khảo sát…).
// Chuyển FileList thành File[] tĩnh ngay lập tức trước khi reset input.value để tránh bị xóa rỗng bởi React async event batching.
type Props = {
  onFiles: (files: File[]) => void
  accept?: string
  hint?: string   // dòng mô tả nhỏ dưới (vd "PDF, ảnh, Excel…")
}

export default function FileDropzone({ onFiles, accept, hint }: Props) {
  const ref = useRef<HTMLInputElement | null>(null)
  const [drag, setDrag] = useState(false)

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList || !fileList.length) return
    const arr = Array.from(fileList) // Ép kiểu sang File[] mảng JS tĩnh ngay lập tức
    onFiles(arr)
  }

  return (
    <div
      onClick={() => ref.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDrag(false)
        if (e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files)
      }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4,
        padding: '16px 12px', borderRadius: 10, cursor: 'pointer', textAlign: 'center',
        border: `2px dashed ${drag ? 'var(--teal)' : 'var(--border)'}`,
        background: drag ? 'rgba(0,174,239,.06)' : '#fafafa', transition: 'all .12s',
      }}>
      <i className="ti ti-cloud-upload" style={{ fontSize: 24, color: drag ? 'var(--teal)' : 'var(--muted)' }} />
      <div style={{ fontSize: 13, color: 'var(--navy)' }}>Kéo thả hoặc <span style={{ color: 'var(--teal)', textDecoration: 'underline' }}>bấm chọn file</span></div>
      {hint && <div style={{ fontSize: 11.5, color: 'var(--muted)' }}>{hint}</div>}
      <input
        ref={ref}
        type="file"
        multiple
        accept={accept}
        style={{ display: 'none' }}
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => {
          handleFiles(e.target.files)
          e.target.value = ''
        }}
      />
    </div>
  )
}
