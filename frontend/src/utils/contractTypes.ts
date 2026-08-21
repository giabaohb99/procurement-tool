// Loại hợp đồng — tầng hiển thị của `backend/app/core/contract_types.py` (CR-118).
//
// Từ CR-118, `tab_contract.contract_type` lưu MÃ tiếng Anh (`purchase`, `principle`…)
// chứ không lưu chữ tiếng Việt nữa. Trước đó mỗi màn tự khai một bộ khác nhau —
// `cruds.tsx` 3 giá trị, `ContractDetail.tsx` 5, dữ liệu thật thì lưu bộ thứ tư —
// nên bộ lọc "Loại HĐ" lọc ra 0 dòng còn ô chọn mở lên thì trống.
export const CONTRACT_TYPES = [
  { value: 'purchase', label: 'Hợp đồng mua bán' },
  { value: 'principle', label: 'Hợp đồng nguyên tắc' },
  { value: 'economic', label: 'Hợp đồng kinh tế' },
  { value: 'template', label: 'Hợp đồng khuôn mẫu' },
  { value: 'transport', label: 'Hợp đồng vận chuyển' },
  { value: 'service', label: 'Hợp đồng dịch vụ' },
  { value: 'other', label: 'Khác' },
]

const LABEL: Record<string, string> = Object.fromEntries(CONTRACT_TYPES.map((t) => [t.value, t.label]))

/** Nhãn tiếng Việt của một mã loại HĐ. Mã lạ thì trả nguyên giá trị — dữ liệu cũ
 *  chưa chạy migration vẫn phải đọc được, thà hiện chữ cũ còn hơn hiện ô trống. */
export const contractTypeLabel = (v?: string | null) => (v ? LABEL[v] || v : '')
