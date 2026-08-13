import { useEffect } from 'react'

/**
 * Đặt tên file mặc định cho hộp thoại In / Lưu PDF.
 *
 * Trình duyệt (và các máy in ảo kiểu Foxit / Microsoft Print to PDF) lấy `document.title`
 * làm tên file gợi ý, nên mọi phiếu in đều ra "Thu Mua Tool.pdf" — người dùng phải gõ tay
 * tên cho từng phiếu. Đổi `document.title` của tab in là cách DUY NHẤT tác động được:
 * hộp thoại lưu do hệ điều hành vẽ, trang web không với tới.
 *
 * Trả lại tiêu đề cũ khi rời trang: phiếu in thường mở ở tab riêng nên không quan trọng,
 * nhưng nếu về sau nhúng vào tab chính thì tiêu đề không bị kẹt lại.
 */
export function usePrintTitle(ten: string) {
  useEffect(() => {
    if (!ten) return
    const cu = document.title
    document.title = ten
    return () => { document.title = cu }
  }, [ten])
}

/**
 * Tên file phiếu in: `<mã chứng từ>-DDMMYYYY`, ví dụ `PO00003-03082026`.
 *
 * `ngay` là chuỗi `YYYY-MM-DD` lấy thẳng từ API (cột ngày trong DB là chuỗi, không phải
 * datetime). Thiếu mã hoặc thiếu ngày thì bỏ phần đó đi chứ không chèn chuỗi rỗng để tránh
 * ra tên kiểu `-03082026` hay `PO00003-`.
 *
 * Lọc ký tự Windows cấm đặt tên file (\ / : * ? " < > |): mã chứng từ do người dùng nhập
 * tay (mã Misa của đơn cũ) nên không loại trừ khả năng có dấu gạch chéo.
 */
export function tenFileIn(ma?: string | null, ngay?: string | null): string {
  const [y, m, d] = String(ngay || '').slice(0, 10).split('-')
  const ddmmyyyy = y && m && d ? `${d}${m}${y}` : ''
  return [String(ma || '').trim(), ddmmyyyy]
    .filter(Boolean)
    .join('-')
    .replace(/[\\/:*?"<>|]/g, '-')
}
