import { useNavigate } from 'react-router-dom'

/** Màn hình khi mở chi tiết một bản ghi không tồn tại (404) hoặc không có quyền xem (403).
 * Dùng chung cho tất cả trang chi tiết để tránh render form trống gây hiểu lầm. */
export default function NotFound({
  title = 'Không tìm thấy',
  message = 'Bản ghi bạn tìm không tồn tại hoặc bạn không có quyền truy cập.',
  backTo,
}: { title?: string; message?: string; backTo?: string }) {
  const navigate = useNavigate()
  return (
    <div className="card" style={{ padding: 48, textAlign: 'center', color: 'var(--muted)' }}>
      <i className="ti ti-file-off" style={{ fontSize: 42, color: '#cbd5e1' }} />
      <div style={{ marginTop: 12, fontSize: 16, color: 'var(--navy)', fontWeight: 700 }}>{title}</div>
      <div style={{ marginTop: 6, fontSize: 13.5, maxWidth: 420, marginInline: 'auto' }}>{message}</div>
      <button className="btn" style={{ marginTop: 18 }} onClick={() => (backTo ? navigate(backTo) : navigate(-1))}>
        <i className="ti ti-arrow-left" /> Quay lại
      </button>
    </div>
  )
}
