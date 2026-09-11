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
    //  ⚠️ `fill` (trang cao bằng khung, phần cuộn nằm BÊN TRONG) chỉ bật từ `md`
    //  trở lên — `max-md:h-auto` gỡ `h-full` mà `fill` đặt.
    //
    //  Vì sao: `fill` sinh ra một ô cuộn nằm TRONG trang. Trên màn rộng ô đó cao
    //  gần hết màn hình nên không ai nhận ra, đổi lại thanh công cụ đứng yên.
    //  Trên máy 390px thì sau tiêu đề và thanh công cụ ba hàng, ô đó chỉ còn hơn
    //  400px — danh sách đọc qua một khe hẹp, mà đó lại là cuộn LỒNG: vuốt trúng
    //  phần ngoài khe thì trang không nhúc nhích và người dùng đọc ra là màn hình
    //  đơ. Bỏ `fill` ở khổ hẹp thì CẢ TRANG cuộn — đúng nếp mọi ứng dụng điện
    //  thoại — và thanh công cụ ở lại bằng `LIST_TOOLBAR_STICKY_TOP`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Chờ tôi duyệt"
        //  ⚠️ Dòng mô tả ẨN trên máy hẹp. Nó là câu GIỚI THIỆU, đọc một lần rồi
        //  thôi — nhưng chiếm hai dòng (~60px) ở đầu MỌI lần mở màn, ngay phía
        //  trên hàng đợi việc mà người ta vào đây để xem. Thứ nó dặn («bấm vào
        //  một dòng để mở ra duyệt») thì mũi tên ở mép phải mỗi thẻ đã nói rồi.
        description={
          <span className="max-md:hidden">
            Bấm vào một dòng để mở văn bản ra đọc rồi duyệt ngay tại đó. Việc đã duyệt nằm phía
            dưới.
          </span>
        }
      />

      <ApprovalInboxTable />
    </PageContainer>
  )
}
