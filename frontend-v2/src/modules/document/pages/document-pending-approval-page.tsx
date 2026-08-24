import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ApprovalInboxTable } from '../components/approval-inbox-table'

/**
 * VĂN BẢN ĐANG CHỜ TÔI DUYỆT — và những cái tôi vừa duyệt xong, trong MỘT bảng.
 *
 * Khác «Việc của tôi» cũ ở phân hệ Phê duyệt (đã xóa) ở chỗ **chỉ có văn bản**:
 * người làm văn thư đứng trong phân hệ Văn bản cả ngày, bắt họ nhảy sang một
 * phân hệ khác để biết mình còn phải ký gì là lý do người dùng bảo *"có đâu nè"*.
 *
 * **Một bảng, không phải hai tab.** Bản trước tách tab «Chờ tôi duyệt» /
 * «Đã duyệt gần đây»: cùng một câu hỏi ("văn bản nào qua tay tôi") ở hai thời
 * điểm, mà phải bấm thêm một cú mới biết mình vừa ký cái gì. Nay việc chưa làm
 * xếp trên, việc đã làm xếp dưới, phân biệt bằng huy hiệu ở cột đầu.
 */
export function DocumentPendingApprovalPage() {
  return (
    <PageContainer fill>
      <PageHeader
        title="Chờ tôi duyệt"
        description="Bấm vào một dòng để mở văn bản ra đọc rồi duyệt ngay tại đó. Việc đã duyệt nằm phía dưới."
      />

      <ApprovalInboxTable />
    </PageContainer>
  )
}
