import { Inbox, Plus, Send } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { IncomingDocumentsTab } from '../components/incoming-documents-tab'
import { OutgoingDocumentsTab } from '../components/outgoing-documents-tab'

const DEN = 'incoming'
const DI = 'outgoing'

const MO_TA: Record<string, string> = {
  [DEN]: 'Văn bản mà bạn nằm trong phạm vi áp dụng — không phải mọi văn bản bạn đọc được.',
  [DI]: 'Số hiệu do hệ cấp khi văn bản được duyệt — không ai gõ tay.',
}

/**
 * MÀN VĂN BẢN — hai tab «Văn bản đến» và «Văn bản đi».
 *
 * Gộp từ hai mục menu cũ («Văn bản» và «Áp dụng cho tôi»): người dùng không nghĩ
 * theo kiểu "danh sách nào" mà nghĩ theo **hướng của văn bản** — cái tôi phải
 * làm theo, và cái đơn vị mình phát ra.
 *
 * ⚠️ Mô hình dữ liệu KHÔNG có cột hướng (đến / đi), và **cố ý không thêm**: hai
 * hướng ở đây chính là hai màn cũ, phân biệt bằng **nguồn dữ liệu**. Tab đến hỏi
 * `/api/documents/applies-to-me` (văn bản tôi phải làm theo — màn "Áp dụng cho
 * tôi" cũ), tab đi hỏi `/api/documents` (màn "Văn bản" cũ). Nghĩa là một văn bản
 * nằm được ở cả hai tab — đúng thực tế: văn bản đơn vị mình ban hành thì chính
 * mình cũng phải làm theo.
 *
 * **Mặc định là tab đi** vì nó chính là màn «Văn bản» cũ: mục menu không đổi
 * nghĩa, và mọi đường quay lại danh sách sau khi tạo / sửa / xóa vẫn về đúng chỗ
 * văn bản vừa đụng tới đang nằm.
 *
 * Đổi tab thì **xóa sạch tham số trên URL** trừ chính `tab`: hai tab dùng hai bộ
 * lọc khác nhau (`document-list-filter-fields` / `document-applied-filter-fields`),
 * để sót lại điều kiện của tab kia là bảng lọc theo một trường nó không có.
 */
export function DocumentListPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()

  //  Nhân sự thường KHÔNG có quyền `document.read` — họ chỉ được xem «Văn bản
  //  đến» (`/api/documents/applies-to-me`, backend mở cho mọi tài khoản đăng
  //  nhập). Tab «Văn bản đi» gọi `/api/documents` (gác `document.read`), nên khi
  //  thiếu quyền phải ẩn HẲN cả nút tab lẫn nội dung — Radix mount sẵn mọi
  //  `TabsContent`, để lại là component con vẫn gọi API và ăn 403.
  const xemDuocVanBanDi = can('document', 'read')
  const tab = !xemDuocVanBanDi ? DEN : searchParams.get('tab') === DEN ? DEN : DI

  function doiTab(next: string) {
    setSearchParams(next === DI ? {} : { tab: next }, { replace: true })
  }

  return (
    <Tabs value={tab} onValueChange={doiTab} className="flex h-full min-h-0 flex-col">
      <PageContainer fill>
        <PageHeader
          title="Văn bản"
          description={MO_TA[tab]}
          actions={
            //  «Tạo văn bản» đứng ở đầu trang cho cả hai tab: soạn một văn bản
            //  mới là việc bắt đầu từ đây bất kể đang đứng ở tab nào. Còn
            //  «Export» thì nằm trong thanh công cụ của tab đi, vì nó xuất
            //  đúng bộ điều kiện đang lọc ở đó.
            <PermissionGate entity="document" action="create">
              <Button onClick={() => navigate(appRoutes.document.documentNew)}>
                <Plus className="size-4" />
                Tạo văn bản
              </Button>
            </PermissionGate>
          }
        />

        {/*  Chỉ dựng thanh tab khi có cả hai tab. Người chỉ xem được «Văn bản
             đến» thì một tab đơn độc trông như lỗi — bỏ hẳn, tiêu đề trang đã
             nói rõ đang xem gì. */}
        {xemDuocVanBanDi && (
          <TabsList className="mb-3 self-start">
            <TabsTrigger value={DEN}>
              <Inbox className="size-4" />
              Văn bản đến
            </TabsTrigger>
            <TabsTrigger value={DI}>
              <Send className="size-4" />
              Văn bản đi
            </TabsTrigger>
          </TabsList>
        )}

        {/*  `TabsContent` phải tự là cột flex co được, nếu không `Card flex-1`
             bên trong không có gì để bám và bảng tụt về chiều cao nội dung. */}
        <TabsContent value={DEN} className="mt-0 flex min-h-0 flex-1 flex-col">
          <IncomingDocumentsTab />
        </TabsContent>

        {xemDuocVanBanDi && (
          <TabsContent value={DI} className="mt-0 flex min-h-0 flex-1 flex-col">
            <OutgoingDocumentsTab />
          </TabsContent>
        )}
      </PageContainer>
    </Tabs>
  )
}
