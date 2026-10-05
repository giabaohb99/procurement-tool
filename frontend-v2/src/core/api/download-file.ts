import { httpClient } from './http-client'

/**
 * Rút tên tệp từ header `Content-Disposition` của response tải xuống — dạng
 * `attachment; filename="ten.xlsx"` (vd `app/core/export_xlsx.py`) hoặc kèm cả
 * `filename*=UTF-8''ten.xlsx` (RFC 5987, vd tải lại tệp GTT02 ở
 * `customs/controller.py`). Ưu tiên `filename*` vì nó chịu được tên có dấu;
 * `filename` thường chỉ an toàn với tên ASCII.
 *
 * Trả `undefined` khi header rỗng hoặc không có tên — nơi gọi tự có tên mặc định.
 */
export function filenameFromContentDisposition(
  disposition: string | undefined | null,
): string | undefined {
  if (!disposition) return undefined
  const starMatch = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(disposition)
  if (starMatch) {
    try {
      return decodeURIComponent(starMatch[1].trim())
    } catch {
      //  %-encoding hỏng (server gửi sai) — rơi xuống nhánh `filename` thường.
    }
  }
  const plainMatch = /filename\s*=\s*"?([^";]+)"?/i.exec(disposition)
  return plainMatch?.[1]?.trim() || undefined
}

/**
 * Tải một tệp qua đường CÓ KIỂM QUYỀN rồi lưu xuống máy.
 *
 * Vì sao không dùng thẳng `<a href={file.url}>`: `url` là đường đọc thẳng từ kho
 * lưu trữ, không đi qua bất kỳ lớp kiểm nào — ai cầm được chuỗi đó đều mở được,
 * kể cả người chưa đăng nhập. Còn `<a href="/api/attachments/1/download">` thì
 * trình duyệt điều hướng cả trang nên **không gắn được token Bearer**, đi tới
 * nơi là ăn 401.
 *
 * Nên phải tải bằng chính `httpClient` (đã có interceptor gắn token và tự làm
 * mới token khi hết hạn), rồi tự dựng liên kết tạm trong bộ nhớ để lưu file.
 *
 * `params` để màn danh sách gửi kèm bộ lọc / sắp xếp / cột đang hiện khi xuất
 * Excel — thiếu nó thì bấm "Xuất Excel" sau khi lọc vẫn ra file toàn bộ dữ liệu,
 * khác hẳn thứ người dùng đang nhìn trên bảng.
 *
 * `filename` chỉ là tên DỰ PHÒNG: nếu backend trả `Content-Disposition` kèm tên
 * (vd tên có ngày giờ xuất, hoặc tên khác theo phạm vi xuất), tên đó thắng — xem
 * `exportCustomsPesticides` (`thuoc-bvtv-toan-bo-*.xlsx` / `thuoc-bvtv-trang-*.xlsx`).
 */
export async function downloadFile(
  url: string,
  filename: string,
  params?: Record<string, unknown>,
): Promise<void> {
  const response = await httpClient.get<Blob>(url, { responseType: 'blob', params })
  const disposition = response.headers['content-disposition']
  const servedFilename = filenameFromContentDisposition(
    typeof disposition === 'string' ? disposition : undefined,
  )

  const objectUrl = URL.createObjectURL(response.data)
  try {
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = servedFilename ?? filename
    //  Firefox đòi thẻ phải nằm trong tài liệu thì `click()` mới ăn.
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  } finally {
    //  Không thu hồi thì blob nằm lại trong bộ nhớ tới khi đóng tab — vài tệp
    //  30MB là thấy ngay.
    URL.revokeObjectURL(objectUrl)
  }
}
