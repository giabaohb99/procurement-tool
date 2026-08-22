/**
 * Loại hợp đồng — tầng HIỂN THỊ của `backend/app/core/contract_types.py` (CR-118).
 *
 * Từ CR-118, `tab_contract.contract_type` lưu MÃ tiếng Anh (`purchase`, `principle`…);
 * tiếng Việt chỉ còn ở đây. Bảng danh sách và chip vẽ đồng bộ nên không chờ được API,
 * vì vậy phải có bản sao tĩnh này.
 *
 * B-02: bản sao đó KHÔNG còn chép tay. Nó lấy từ `@/shared/constants/statuses`, tệp do
 * `backend/scripts/gen_status_ts.py` sinh ra từ chính sổ đăng ký Python — thêm một loại
 * hợp đồng ở backend mà quên vá đây thì trước kia im lặng, giờ thì lệch tệp sinh và
 * cổng `--check` bắt được.
 *
 * ⚠️ Ô CHỌN trên form thì KHÔNG dùng bản sao này — nó nạp thẳng từ
 * `GET /api/contracts/meta/types`. Lý do: nhãn lệch chỉ là hiển thị xấu, còn THIẾU một
 * mã trong danh sách chọn là người dùng không lập được loại hợp đồng đó, mà gửi mã lạ
 * lên thì backend trả 422.
 */
import { CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'

/** Dùng cho ô lọc (bộ lọc điều kiện chỉ nhận options tĩnh). */
export const CONTRACT_TYPE_OPTIONS = CONTRACT_TYPE.map(({ value, label }) => ({ value, label }))

/**
 * Nhãn tiếng Việt của một mã loại hợp đồng.
 *
 * Mã lạ thì TRẢ NGUYÊN giá trị chứ không trả rỗng: dữ liệu cũ chưa kịp đổi (hoặc bản
 * ghi do nơi khác ghi vào) vẫn phải đọc được, thà hiện chữ tiếng Việt cũ còn hơn hiện
 * một ô trống làm người dùng tưởng mất dữ liệu.
 */
export function contractTypeLabel(value?: string | null): string {
  const v = (value ?? '').trim()
  if (!v) return ''
  return labelOf(CONTRACT_TYPE, v) || v
}
