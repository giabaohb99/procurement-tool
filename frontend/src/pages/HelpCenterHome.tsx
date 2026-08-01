import { useOutletContext } from 'react-router-dom'

import type { HelpOutletContext } from '../layouts/HelpLayout'

// Trang chủ /hdsd — giới thiệu cách tra cứu tài liệu.

export default function HelpCenterHome() {
  const { canEdit, tree } = useOutletContext<HelpOutletContext>()

  return (
    <div style={{ padding: '32px 48px 64px', maxWidth: 900, margin: '0 auto', color: 'var(--navy)' }}>
      <h1 style={{ fontSize: 32, fontWeight: 700, lineHeight: 1.4, marginTop: 0, marginBottom: 24,
                   borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
        Trung tâm Hướng dẫn Sử dụng
      </h1>

      <div style={{ fontSize: 15.5, lineHeight: 1.75 }}>
        <p style={{ marginBottom: 16 }}>
          Chào mừng bạn đến với hệ thống Hướng dẫn sử dụng. Tại đây cung cấp toàn bộ tài liệu, quy trình
          và giải đáp thắc mắc để bạn thao tác dễ dàng trên phần mềm mua hàng.
        </p>

        <h3 style={{ fontSize: 19, fontWeight: 600, marginTop: 32, marginBottom: 12 }}>
          Cách tra cứu tài liệu
        </h3>
        <ul style={{ paddingLeft: 24, marginBottom: 24 }}>
          <li style={{ marginBottom: 8 }}>
            <strong>Duyệt theo danh mục:</strong> Thanh bên trái nhóm tài liệu theo từng bước của quy
            trình (Yêu cầu mua hàng → Khảo sát giá → Đơn mua hàng → Nhận hàng → Công nợ → Yêu cầu thanh toán).
          </li>
          <li style={{ marginBottom: 8 }}>
            <strong>Mở rộng thư mục:</strong> Bấm mũi tên cạnh tên thư mục để xem các bài viết chi tiết bên trong.
          </li>
          <li style={{ marginBottom: 8 }}>
            <strong>Tìm kiếm nhanh:</strong> Dùng ô "Tìm kiếm tài liệu" ở góc trên bên phải để tra theo
            tiêu đề hoặc nội dung bài viết.
          </li>
        </ul>

        <div style={{ background: '#f8fafc', borderRadius: 12, padding: 20, border: '1px solid var(--border)',
                      display: 'flex', gap: 16, alignItems: 'flex-start' }}>
          <i className="ti ti-bulb" style={{ fontSize: 24, color: 'var(--amber)' }} />
          <div>
            <strong style={{ display: 'block', marginBottom: 4, fontSize: 15.5 }}>
              {tree.length === 0 ? 'Chưa có tài liệu nào' : 'Bắt đầu ngay'}
            </strong>
            <span style={{ color: 'var(--muted)' }}>
              {tree.length === 0
                ? (canEdit
                    ? 'Bấm nút "Thêm mục gốc" ở góc trên bên trái để tạo bài viết đầu tiên.'
                    : 'Quản trị viên chưa đăng tài liệu hướng dẫn. Vui lòng quay lại sau.')
                : 'Hãy chọn một bài viết ở cột bên trái để bắt đầu khám phá hệ thống.'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
