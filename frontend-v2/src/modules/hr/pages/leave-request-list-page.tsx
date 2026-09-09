import { Plus } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { LeaveHandledTab } from '../components/leave-handled-tab'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { LeaveMyRequestsTab } from '../components/leave-my-requests-tab'
import { LeaveToApproveTab } from '../components/leave-to-approve-tab'
import { useLeaveToApprove } from '../hooks/use-leave'
import { LIST_TABS_STICKY } from '../utils/list-sticky'

const TAB_TO_APPROVE = 'to-approve'
const TAB_MINE = 'mine'
const TAB_HANDLED = 'handled'

/**
 * ĐƠN NGHỈ PHÉP — ba tab: việc đang đợi tôi · đơn của tôi · tôi đã duyệt (CR-260).
 *
 * ⚠️ **Tab «Cần tôi duyệt» đứng ĐẦU và được chọn sẵn khi có việc.** Đây là thứ
 * duy nhất trong màn này CHẶN người khác: một tờ đơn nằm chờ chữ ký là một
 * người không biết mình được nghỉ hay không. Đơn của chính mình thì xem lúc nào
 * cũng được.
 *
 * ⚠️ Nhưng chỉ nhảy tab **một lần, khi vừa mở màn**. Tự nhảy mỗi lần số việc đổi
 * thì người đang xem dở đơn của mình bị đá sang tab khác đúng lúc có ai vừa gửi
 * duyệt — và người dùng không hiểu tại sao màn hình tự đổi.
 *
 * Tab đang chọn nằm trên URL để dán được đường dẫn cho nhau và để nút Back của
 * trình duyệt chạy đúng.
 */
export function LeaveRequestListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const [tab, setTab] = useUrlParamState('tab', '')

  const { data: toApprove } = useLeaveToApprove()
  const waitingCount = toApprove?.items.length ?? 0

  //  Dải ghim đầu trang đổ bóng khi có nội dung trôi bên dưới — xem
  //  `list-sticky.ts`. Đo ở `Tabs` vì nó nằm cùng khung cuộn với hai dải.
  const tabsRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(tabsRef)

  //  Tab mặc định: có việc thì mở thẳng hàng đợi, không thì về đơn của mình.
  //  Chờ dữ liệu về rồi mới chốt — chốt trước là luôn rơi vào «Đơn của tôi».
  useEffect(() => {
    if (tab || toApprove === undefined) return
    setTab(waitingCount > 0 ? TAB_TO_APPROVE : TAB_MINE)
  }, [tab, toApprove, waitingCount, setTab])

  //  ⚠️ `fill` (trang cao bằng khung, phần cuộn nằm BÊN TRONG) chỉ bật từ `md`
  //  trở lên — `max-md:h-auto` gỡ `h-full` mà `fill` đặt.
  //
  //  Vì sao: `fill` sinh ra một ô cuộn nằm TRONG trang. Trên màn rộng ô đó cao
  //  gần hết màn hình nên không ai nhận ra, đổi lại thanh công cụ và phân trang
  //  đứng yên. Trên máy 393px thì sau tiêu đề · nút · hai hàng tab · thanh lọc,
  //  ô đó **chỉ còn 304px** — đo trên bản chạy: 3083px danh sách đọc qua một khe
  //  304px, tức hai thẻ một lần. Tệ hơn, đó là cuộn LỒNG: vuốt trúng phần ngoài
  //  khe thì trang không nhúc nhích và người dùng đọc ra là màn hình đơ.
  //
  //  Bỏ `fill` ở khổ hẹp thì danh sách dài tự nhiên và CẢ TRANG cuộn — đúng nếp
  //  mọi ứng dụng điện thoại. Thanh công cụ trôi theo, chấp nhận được: lọc là
  //  việc làm một lần rồi đọc, không phải việc làm liên tục.
  return (
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Đơn nghỉ phép"
        //  ⚠️ Dòng mô tả ẨN trên máy hẹp. Nó là câu GIỚI THIỆU, đọc một lần rồi
        //  thôi — nhưng chiếm hai dòng (~60px) ở đầu MỌI lần mở màn, ngay phía
        //  trên thứ người ta thật sự vào đây để xem. Trên màn rộng thì 60px đó
        //  không lấy chỗ của ai nên vẫn giữ.
        description={
          <span className="max-md:hidden">
            Nộp đơn, duyệt đơn của người khác và theo dõi số ngày phép còn lại.
          </span>
        }
        actions={
          can('leave_request', 'create') ? (
            //  ⚠️ Màn hẹp thì nút chiếm TRỌN hàng — `w-full` chỉ ăn nhờ nhóm nút
            //  của `PageHeader` cũng `max-md:w-full`. Không có vế đó thì nút là
            //  con của một khối co theo nội dung, `width:100%` quy về đúng bề
            //  rộng cũ và câu lệnh không làm gì cả.
            <Button
              className="w-full md:w-auto"
              onClick={() => navigate(appRoutes.hr.leaveRequestNew)}
            >
              <Plus className="size-4" />
              Nộp đơn nghỉ phép
            </Button>
          ) : undefined
        }
      />

      <LeaveSectionTabs />

      {/*  `group` + `data-scrolled` là đường dẫn tín hiệu «trang đã cuộn» xuống
           tới dải ghim nằm sâu bên trong (thanh công cụ do `DataTable` vẽ, tầng
           trang không với tới được bằng prop). Bóng đổ của dải đó đọc thuộc tính
           này — xem `list-sticky.ts`. */}
      <Tabs
        ref={tabsRef}
        value={tab || TAB_MINE}
        onValueChange={setTab}
        data-scrolled={scrolled ? '' : undefined}
        className="group flex min-h-0 flex-1 flex-col"
      >
        {/*  Màn hẹp: dải tab trải hết hàng, chia đều ba phần, và GHIM đỉnh trang
             khi cuộn (xem `LIST_TABS_STICKY`). `TabsList` mặc định `w-fit`, nên
             trên điện thoại ba tab bó vào mép trái và chừa một khoảng trống vô
             nghĩa bên phải — mà đây là chỗ chuyển qua lại nhiều nhất của cả màn,
             mỗi phần rộng thêm là mỗi lần bấm bớt trượt. `min-w-0` trên nút để
             nhãn dài không nong dải ra quá bề ngang. */}
        <div className={LIST_TABS_STICKY}>
        <TabsList className="w-full shrink-0 md:w-fit">
          <TabsTrigger value={TAB_TO_APPROVE} className="min-w-0 px-2 text-xs md:px-3 md:text-sm">
            Cần tôi duyệt
            {/*  Con số chỉ hiện khi KHÁC 0: một huy hiệu «0» đứng cạnh nhãn đọc
                 ra như một cảnh báo, mà nó đang nói "không có gì cả". */}
            {waitingCount > 0 && (
              <Badge className="ml-1.5 border-sky-300 bg-sky-100 text-sky-800 dark:border-sky-700 dark:bg-sky-950 dark:text-sky-200">
                {waitingCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value={TAB_MINE} className="min-w-0 px-2 text-xs md:px-3 md:text-sm">
            Đơn của tôi
          </TabsTrigger>
          <TabsTrigger value={TAB_HANDLED} className="min-w-0 px-2 text-xs md:px-3 md:text-sm">
            Tôi đã duyệt
          </TabsTrigger>
        </TabsList>
        </div>

        {/*  Mỗi tab một `Card` riêng chứ không bọc chung ngoài `Tabs`: bảng chạy
             `fillHeight` nên nó cần đúng một khung cha có chiều cao xác định.

             ⚠️ **`min-w-0` trên `Card` không được bỏ.** `TabsContent` là một hộp
             flex NGANG, mà mọi ô flex mặc định `min-width: auto` — nghĩa là thẻ
             không co xuống dưới bề rộng tự nhiên của thứ nằm trong nó. Bảng này
             khai bề rộng cứng cho từng cột nên bề rộng tự nhiên của nó ~1200px:
             màn hẹp hơn thế thì thẻ phình ra ngoài và CẢ TRANG trượt ngang —
             tiêu đề, nút «Nộp đơn», thanh tab đều trôi sang trái và bị cắt (lỗi
             báo 04/09/2026). Có `min-w-0` thì phần dôi ra quay về đúng chỗ của
             nó: thanh cuộn ngang bên trong bảng. */}
        <TabsContent value={TAB_TO_APPROVE} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
            <LeaveToApproveTab />
          </Card>
        </TabsContent>

        <TabsContent value={TAB_MINE} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
            <LeaveMyRequestsTab />
          </Card>
        </TabsContent>

        <TabsContent value={TAB_HANDLED} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
            <LeaveHandledTab />
          </Card>
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
