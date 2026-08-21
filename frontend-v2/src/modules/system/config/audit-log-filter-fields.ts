import type { FilterFieldDefinition } from '@/shared/conditional-filter'

export const AUDIT_LOG_FILTER_FIELDS: FilterFieldDefinition[] = [
  {
    name: 'entity',
    label: 'Đối tượng (Entity)',
    type: 'select',
    options: [
      { value: 'product', label: 'Sản phẩm & Vật tư (product)' },
      { value: 'contract', label: 'Hợp đồng (contract)' },
      { value: 'supplier', label: 'Nhà cung cấp (supplier)' },
      { value: 'purchase_request', label: 'Yêu cầu mua hàng (purchase_request)' },
      { value: 'purchase_order', label: 'Đơn mua hàng (purchase_order)' },
      { value: 'payable', label: 'Công nợ (payable)' },
      { value: 'payment_request', label: 'Yêu cầu thanh toán (payment_request)' },
      { value: 'user', label: 'Tài khoản người dùng (user)' },
      { value: 'role', label: 'Vai trò (role)' },
      { value: 'setting', label: 'Cấu hình hệ thống (setting)' },
      { value: 'document', label: 'Văn bản (document)' },
      { value: 'ticket', label: 'Phiếu hỗ trợ (ticket)' },
    ],
  },
  {
    name: 'action',
    label: 'Hành động',
    type: 'select',
    options: [
      { value: 'create', label: 'Tạo mới (create)' },
      { value: 'update', label: 'Cập nhật (update)' },
      { value: 'delete', label: 'Xóa (delete)' },
      { value: 'submitted', label: 'Gửi duyệt (submitted)' },
      { value: 'approved', label: 'Đã duyệt (approved)' },
      { value: 'rejected', label: 'Từ chối (rejected)' },
      { value: 'paid', label: 'Ghi nhận chi (paid)' },
      { value: 'cancelled', label: 'Hủy (cancelled)' },
    ],
  },
  {
    name: 'from_date',
    label: 'Từ ngày',
    type: 'date',
  },
  {
    name: 'to_date',
    label: 'Đến ngày',
    type: 'date',
  },
  {
    name: 'search',
    label: 'Từ khóa chi tiết',
    type: 'text',
  },
]
