import { httpClient } from './http-client'

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
 */
export async function downloadFile(url: string, filename: string): Promise<void> {
  const response = await httpClient.get<Blob>(url, { responseType: 'blob' })

  const objectUrl = URL.createObjectURL(response.data)
  try {
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = filename
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
