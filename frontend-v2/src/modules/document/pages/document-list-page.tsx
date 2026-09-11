import { Inbox, Plus, Send } from 'lucide-react'
import { useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
//  ⚠️ Mượn từ phân hệ Nhân sự, KHÔNG chép chuỗi sang đây: hai dải ghim dùng một
//  hệ mốc `top` cộng dồn, bản chép sẽ lệch đúng vào ngày ai đó sửa chiều cao dải
//  tab ở một chỗ — và lệch kiểu đó chỉ lộ ra khi cuộn. `shared/crud` cũng đang
//  nhập từ đấy; chỗ đúng của tệp này là `shared/`, xem ghi chú ở cuối CR.
import { LIST_TABS_STICKY } from '@/modules/hr/utils/list-sticky'
import { appRoutes } from '@/shared/constants/app-routes'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { IncomingDocumentsTab } from '../components/incoming-documents-tab'
import { OutgoingDocumentsTab } from '../components/outgoing-documents-tab'

const DEN = 'incoming'
const DI = 'outgoing'

const DESCRIPTIONS: Record<string, string> = {
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
  const canViewOutgoing = can('document', 'read')
  const tab = !canViewOutgoing ? DEN : searchParams.get('tab') === DEN ? DEN : DI

  function changeTab(next: string) {
    setSearchParams(next === DI ? {} : { tab: next }, { replace: true })
  }

  //  Dải ghim đầu trang chỉ đổ bóng khi có nội dung trôi bên dưới — xem
  //  `list-sticky.ts`. Đo ở `Tabs` vì nó nằm cùng khung cuộn với hai dải.
  const tabsRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(tabsRef)

  //  ⚠️ `fill` (trang cao bằng khung, phần cuộn nằm BÊN TRONG) chỉ bật từ `md`
  //  trở lên — `max-md:h-auto` gỡ `h-full` mà `fill` đặt.
  //
  //  Vì sao: `fill` sinh một ô cuộn nằm TRONG trang. Trên màn rộng ô đó cao gần
  //  hết màn hình nên không ai nhận ra, đổi lại thanh công cụ và phân trang đứng
  //  yên. Trên máy 390px thì sau tiêu đề · nút · dải tab · hai hàng lọc, ô đó
  //  chỉ còn ~480px cho 20 thẻ cao 121px — tức đọc 2400px qua một khe bốn thẻ.
  //  Tệ hơn, đó là cuộn LỒNG: vuốt trúng phần ngoài khe thì trang không nhúc
  //  nhích và người dùng đọc ra là màn hình đơ.
  //
  //  Bỏ `fill` ở khổ hẹp thì danh sách dài tự nhiên và CẢ TRANG cuộn — đúng nếp
  //  mọi ứng dụng điện thoại; dải tab và thanh công cụ ghim lại để bù.
  return (
    <Tabs
      ref={tabsRef}
      value={tab}
      onValueChange={changeTab}
      data-scrolled={scrolled ? '' : undefined}
      //  `group` + `data-scrolled` là đường dẫn tín hiệu «trang đã cuộn» xuống
      //  dải ghim nằm sâu bên trong (thanh công cụ do `DataTable` vẽ, tầng trang
      //  không với tới được bằng prop).
      className="group flex h-full min-h-0 flex-col max-md:h-auto"
    >
      <PageContainer fill className="max-md:h-auto">
        <PageHeader
          title="Văn bản"
          //  ⚠️ Dòng mô tả ẩn dưới 768px: hai câu này là chú thích nghiệp vụ đọc
          //  một lần rồi thôi, mà ở 390px chúng ngắt thành hai dòng và đẩy cả
          //  dải tab + thanh công cụ xuống thêm ~48px — chỗ đó là chỗ của danh
          //  sách. Cùng luật với `ModuleDashboard` (nó tự làm; trang này dựng
          //  tay `PageContainer` + `PageHeader` nên phải khai).
          description={<span className="max-md:hidden">{DESCRIPTIONS[tab]}</span>}
          //  Khổ hẹp: nút chính trải hết hàng. `PageHeader` chỉ mở đường bằng
          //  `max-md:w-full` cho CỤM nút — bản thân nút vẫn co theo chữ nên nếu
          //  không ép thì nó dán mép phải với một khoảng trống dài bên trái.
          actionsClassName="max-md:[&>button]:flex-1"
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
             nói rõ đang xem gì.

             ⚠️ Khổ hẹp: dải tab GHIM đỉnh khung cuộn (`LIST_TABS_STICKY`) và
             trải hết hàng, chia đôi. `TabsList` mặc định `w-fit` nên hai tab bó
             vào mép trái, chừa một khoảng trống vô nghĩa bên phải — mà đây là
             chỗ chuyển qua lại nhiều nhất của cả màn.

             ⚠️ `max-md:mb-0`: khoảng hở dưới dải ghim phải là ĐỆM của chính dải
             (`pb-2` trong `LIST_TABS_STICKY`), không được là lề của `TabsList` —
             lề nằm NGOÀI hộp được tô nền nên thẻ cuộn qua sẽ hiện một vạch chữ
             cụt ngay dưới dải. Cùng bài học với `mb-0 + pb-3` của thanh công cụ. */}
        {canViewOutgoing && (
          <div className={LIST_TABS_STICKY}>
            <TabsList className="mb-3 w-full shrink-0 max-md:mb-0 md:w-fit">
              <TabsTrigger value={DEN} className="min-w-0">
                <Inbox className="size-4" />
                Văn bản đến
              </TabsTrigger>
              <TabsTrigger value={DI} className="min-w-0">
                <Send className="size-4" />
                Văn bản đi
              </TabsTrigger>
            </TabsList>
          </div>
        )}

        {/*  `TabsContent` phải tự là cột flex co được, nếu không `Card flex-1`
             bên trong không có gì để bám và bảng tụt về chiều cao nội dung. */}
        <TabsContent value={DEN} className="mt-0 flex min-h-0 flex-1 flex-col">
          <IncomingDocumentsTab />
        </TabsContent>

        {canViewOutgoing && (
          <TabsContent value={DI} className="mt-0 flex min-h-0 flex-1 flex-col">
            <OutgoingDocumentsTab />
          </TabsContent>
        )}
      </PageContainer>
    </Tabs>
  )
}
