import { History, Inbox } from 'lucide-react'

import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { PendingApprovalTable } from '../components/pending-approval-table'
import { RecentDecisionsTable } from '../components/recent-decisions-table'
import { useMyDocumentTasks } from '../hooks/use-my-document-approvals'

/**
 * VĂN BẢN ĐANG CHỜ TÔI DUYỆT — và những cái tôi vừa duyệt xong.
 *
 * Khác «Việc của tôi» cũ ở phân hệ Phê duyệt (đã xóa) hai điểm, cả hai đều cố ý:
 *
 * 1. **Chỉ có văn bản.** Người làm văn thư đứng trong phân hệ Văn bản cả ngày;
 *    bắt họ nhảy sang một phân hệ khác để biết mình còn phải ký gì là lý do
 *    người dùng bảo *"có đâu nè"*.
 * 2. **Không có nút duyệt trên dòng.** Bấm vào dòng là mở chính văn bản ra —
 *    duyệt tại đó, sau khi đã đọc. Bày nút bấm ngay trên danh sách là mời người
 *    ta ký một thứ chỉ nhìn thấy mỗi cái tiêu đề.
 *
 * **Hai TAB, không phải hai khối chồng nhau.** Bản trước xếp chồng: mỗi bảng
 * chỉ còn nửa màn hình, cả hai cùng cụt, và bảng dưới có thanh công cụ riêng
 * nên nhìn như hai trang dán lại. Tab ở đây chia **tập dữ liệu** (việc chưa làm
 * / việc đã làm) chứ không phải một ô lọc — đúng chỗ dùng tab theo
 * `docs/ui/table.md` mục 3, và đặt giữa `PageHeader` với `Card`.
 *
 * Tab đang mở nằm trên URL (`?tab=`) để còn gửi đường dẫn cho nhau và bấm quay
 * lại không nhảy về tab đầu.
 */
export function DocumentPendingApprovalPage() {
  const [tab, setTab] = useUrlParamState('tab', 'pending')
  //  Đọc lại hộp việc đã nạp sẵn cho nút trên thanh trên — chỉ để hiện SỐ trên
  //  nhãn tab, không thêm vòng gọi nào.
  const { items } = useMyDocumentTasks()

  return (
    <Tabs value={tab} onValueChange={setTab} className="flex h-full min-h-0 flex-col">
      <PageContainer fill>
        <PageHeader
          title="Chờ tôi duyệt"
          description="Bấm vào một dòng để mở văn bản ra đọc rồi duyệt ngay tại đó."
        />

        <TabsList className="mb-3 self-start">
          <TabsTrigger value="pending">
            <Inbox className="size-4" />
            Chờ tôi duyệt
            {/* Số chỉ hiện khi có việc — số 0 nằm mãi trên nhãn dạy người dùng
                bỏ qua chỗ đó, rồi hôm nó thành 3 thì mắt cũng lướt qua luôn. */}
            {items.length > 0 && (
              <span className="ml-1 rounded-full bg-primary px-1.5 text-[0.6875rem] font-semibold text-primary-foreground">
                {items.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="done">
            <History className="size-4" />
            Đã duyệt gần đây
          </TabsTrigger>
        </TabsList>

        {/*  `TabsContent` phải tự là cột flex co được, nếu không `Card flex-1`
             bên trong không có gì để bám và bảng tụt về chiều cao nội dung. */}
        <TabsContent value="pending" className="mt-0 flex min-h-0 flex-1 flex-col">
          <PendingApprovalTable />
        </TabsContent>

        <TabsContent value="done" className="mt-0 flex min-h-0 flex-1 flex-col">
          <RecentDecisionsTable />
        </TabsContent>
      </PageContainer>
    </Tabs>
  )
}
