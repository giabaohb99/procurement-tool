import { toast } from './toast'

/**
 * Ô CHỈ ĐỌC nhưng CHO COPY (CR-108, phiếu hỗ trợ TK19082604).
 *
 * Ô `<input disabled>` và react-select ở trạng thái disabled đều không bôi đen được, nên
 * người dùng nhìn thấy mã hàng mà không lấy ra được để tra cứu. Ở đây trả về chữ thường —
 * bôi đen thoải mái — kèm một nút copy cho nhanh.
 */
export default function CopyText({ value, title, style }: { value?: string; title?: string; style?: React.CSSProperties }) {
  const text = (value || '').trim()
  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Đã copy')
    } catch {
      toast.error('Trình duyệt không cho copy — hãy bôi đen rồi Ctrl+C')
    }
  }
  return (
    <div className="copy-text" title={title} style={style}>
      <span className="copy-text-value">{text || '—'}</span>
      {text && (
        <button type="button" className="icon-btn copy-text-btn" title="Copy mã hàng" onClick={copy}>
          <i className="ti ti-copy" style={{ fontSize: 15 }} />
        </button>
      )}
    </div>
  )
}
