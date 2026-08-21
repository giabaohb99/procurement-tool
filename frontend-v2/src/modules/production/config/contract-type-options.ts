/**
 * Loại hợp đồng — tầng HIỂN THỊ của `backend/app/core/contract_types.py` (CR-118).
 *
 * Từ CR-118, `tab_contract.contract_type` lưu MÃ tiếng Anh (`purchase`, `principle`…);
 * tiếng Việt chỉ còn ở đây. Bảng danh sách và chip vẽ đồng bộ nên không chờ được API,
 * vì vậy phải có bản sao tĩnh này.
 *
 * ⚠️ Ô CHỌN trên form thì KHÔNG dùng bản sao này — nó nạp thẳng từ
 * `GET /api/contracts/meta/types`. Lý do: nhãn lệch chỉ là hiển thị xấu, còn THIẾU một
 * mã trong danh sách chọn là người dùng không lập được loại hợp đồng đó, mà gửi mã lạ
 * lên thì backend trả 422.
 */
const CONTRACT_TYPE_LABEL: Record<string, string> = {
  purchase: 'Hợp đồng mua bán',
  principle: 'Hợp đồng nguyên tắc',
  economic: 'Hợp đồng kinh tế',
  template: 'Hợp đồng khuôn mẫu',
  transport: 'Hợp đồng vận chuyển',
  service: 'Hợp đồng dịch vụ',
  other: 'Khác',
}

/** Dùng cho ô lọc (bộ lọc điều kiện chỉ nhận options tĩnh). */
export const CONTRACT_TYPE_OPTIONS = Object.entries(CONTRACT_TYPE_LABEL).map(
  ([value, label]) => ({ value, label }),
)

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
  return CONTRACT_TYPE_LABEL[v] ?? v
}
