import { useSearchParams } from 'react-router-dom'

/**
 * Tham số `?attach=1` của link trợ lý AI gửi (ai-CR-240): mở THẲNG hộp đính tệp của chứng từ.
 *
 * Tệp (hóa đơn, báo giá, phiếu giao) không gửi được qua ứng dụng AI nên kết quả tool trả link màn web kèm tham số này;
 * hàm dựng link ở backend là `assistant/tools/attach_link.build_attach_url`. Link chỉ mở giao diện: người dùng vẫn phải
 * đăng nhập, màn tự kiểm quyền như thường — không có quyền thì không mở hộp.
 */
export const ATTACH_PARAM = 'attach'

/** `true` khi URL hiện tại có `?attach=1`. */
export function useAttachParam(): boolean {
  const [searchParams] = useSearchParams()
  return searchParams.get(ATTACH_PARAM) === '1'
}
