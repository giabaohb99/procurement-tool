// Hằng số + badge dùng chung cho phân hệ Phiếu hỗ trợ.
// Tách khỏi trang danh sách để tab ở Trang cá nhân, màn quản lý và popup tạo phiếu
// cùng dùng một nguồn, không import chéo giữa các page.
// Đồng bộ với backend: app/modules/ticket/service.py

export const TICKET_STATUS: Record<string, { label: string; bg: string; color: string }> = {
  open: { label: 'Mới', bg: '#eff6ff', color: '#1d4ed8' },
  in_progress: { label: 'Đang xử lý', bg: '#fff7ed', color: '#c2410c' },
  answered: { label: 'Đã trả lời', bg: '#ecfdf5', color: '#047857' },
  closed: { label: 'Đã đóng', bg: '#f1f5f9', color: '#64748b' },
}

export const TICKET_PRIORITY: Record<string, { label: string; bg: string; color: string }> = {
  low: { label: 'Thấp', bg: '#f1f5f9', color: '#64748b' },
  normal: { label: 'Trung bình', bg: '#eff6ff', color: '#2563eb' },
  high: { label: 'Cao', bg: '#fff7ed', color: '#c2410c' },
  urgent: { label: 'Khẩn', bg: '#fef2f2', color: '#dc2626' },
}

// Bộ phận / nhóm chỉ là nhãn phân loại (định tuyến tập trung về 1 nhóm Hỗ trợ)
export const TICKET_DEPARTMENTS = [
  'Kỹ thuật / Phần mềm',
  'Tài khoản & Đăng nhập',
  'Quy trình mua hàng',
  'Dữ liệu & Báo cáo',
  'Khác',
]

export const TICKET_STATUS_TABS: { key: string; label: string }[] = [
  { key: '', label: 'Tất cả' },
  { key: 'open', label: 'Mới' },
  { key: 'in_progress', label: 'Đang xử lý' },
  { key: 'answered', label: 'Đã trả lời' },
  { key: 'closed', label: 'Đã đóng' },
]

export type Ticket = {
  id: number; code: string; subject: string; department: string
  priority: string; priority_label: string
  status: string; status_label: string
  requester_id: number; requester_name: string
  assignee_id: number; assignee_name: string
  origin_url?: string
  created_at: string; updated_at: string; closed_at?: string
}

export function StatusBadge({ status }: { status: string }) {
  const c = TICKET_STATUS[status] || { label: status, bg: '#f1f5f9', color: '#64748b' }
  return (
    <span className="badge" style={{ background: c.bg, color: c.color, fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 999 }}>
      {c.label}
    </span>
  )
}

export function PriorityBadge({ priority }: { priority: string }) {
  const c = TICKET_PRIORITY[priority] || { label: priority, bg: '#f1f5f9', color: '#64748b' }
  return (
    <span className="badge" style={{ background: c.bg, color: c.color, fontSize: 11.5, fontWeight: 700, padding: '2px 9px', borderRadius: 999 }}>
      {c.label}
    </span>
  )
}
