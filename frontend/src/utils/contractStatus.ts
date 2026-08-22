// Đối tượng / Trạng thái / Tình trạng hạn của Hợp đồng — tầng hiển thị của
// `backend/app/core/status_codes.py` (B-02, xem `doc/erp/15-do-be-tong-nen-v2.md`).
//
// Từ B-02, `tab_contract.party_type` và `.status` lưu MÃ tiếng Anh; `expiry` do backend
// tính cũng trả về mã. Chữ tiếng Việt chỉ còn ở đây và ở `*_label` mà API gửi kèm.
//
// ⚠️ Bản này CHÉP TAY, cố ý. `frontend/` đã đóng băng (D-026) nên không được nối vào
// `backend/scripts/gen_status_ts.py` — bộ sinh chỉ ghi cho `frontend-v2/`. Đây là bản
// vá cho sống, giữ màn Hợp đồng cũ chạy đúng tới ngày tắt `frontend/`; thêm mã mới thì
// sửa ở Python trước, rồi mới ngó lại đây.
export const CONTRACT_PARTY_TYPES = [
  { value: 'supplier', label: 'Nhà cung cấp' },
  { value: 'customer', label: 'Khách hàng' },
  { value: 'other', label: 'Khác' },
]

export const CONTRACT_STATUSES = [
  { value: 'active', label: 'Hiệu lực' },
  { value: 'expired', label: 'Hết hạn' },
  { value: 'liquidated', label: 'Thanh lý' },
  { value: 'cancelled', label: 'Hủy' },
]

// Thứ tự "cần xử lý trước": hết hạn lên đầu.
export const CONTRACT_EXPIRY_STATES = [
  { value: 'expired', label: 'Hết hạn' },
  { value: 'expiring_soon', label: 'Sắp hết hạn' },
  { value: 'valid', label: 'Còn hạn' },
]

const mkLabel = (opts: { value: string; label: string }[]) => {
  const m: Record<string, string> = Object.fromEntries(opts.map((o) => [o.value, o.label]))
  // Mã lạ thì trả NGUYÊN giá trị — dữ liệu chưa chạy migration vẫn phải đọc được,
  // thà hiện chữ tiếng Việt cũ còn hơn hiện ô trống làm người dùng tưởng mất dữ liệu.
  return (v?: string | null) => (v ? m[v] || v : '')
}

export const partyTypeLabel = mkLabel(CONTRACT_PARTY_TYPES)
export const contractStatusLabel = mkLabel(CONTRACT_STATUSES)
export const contractExpiryLabel = mkLabel(CONTRACT_EXPIRY_STATES)
