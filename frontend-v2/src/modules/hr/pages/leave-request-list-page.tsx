import { Plus } from 'lucide-react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { LeaveHandledTab } from '../components/leave-handled-tab'
import { LeaveMyRequestsTab } from '../components/leave-my-requests-tab'
import { LeaveToApproveTab } from '../components/leave-to-approve-tab'
import { useLeaveToApprove } from '../hooks/use-leave'

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

  //  Tab mặc định: có việc thì mở thẳng hàng đợi, không thì về đơn của mình.
  //  Chờ dữ liệu về rồi mới chốt — chốt trước là luôn rơi vào «Đơn của tôi».
  useEffect(() => {
    if (tab || toApprove === undefined) return
    setTab(waitingCount > 0 ? TAB_TO_APPROVE : TAB_MINE)
  }, [tab, toApprove, waitingCount, setTab])

  return (
    <PageContainer fill>
      <PageHeader
        title="Đơn nghỉ phép"
        description="Nộp đơn, duyệt đơn của người khác và theo dõi số ngày phép còn lại."
        actions={
          can('leave_request', 'create') ? (
            <Button onClick={() => navigate(appRoutes.hr.leaveRequestNew)}>
              <Plus className="size-4" />
              Nộp đơn nghỉ phép
            </Button>
          ) : undefined
        }
      />

      <Tabs
        value={tab || TAB_MINE}
        onValueChange={setTab}
        className="flex min-h-0 flex-1 flex-col"
      >
        <TabsList>
          <TabsTrigger value={TAB_TO_APPROVE}>
            Cần tôi duyệt
            {/*  Con số chỉ hiện khi KHÁC 0: một huy hiệu «0» đứng cạnh nhãn đọc
                 ra như một cảnh báo, mà nó đang nói "không có gì cả". */}
            {waitingCount > 0 && (
              <Badge className="ml-1.5 border-sky-300 bg-sky-100 text-sky-800 dark:border-sky-700 dark:bg-sky-950 dark:text-sky-200">
                {waitingCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value={TAB_MINE}>Đơn của tôi</TabsTrigger>
          <TabsTrigger value={TAB_HANDLED}>Tôi đã duyệt</TabsTrigger>
        </TabsList>

        {/*  Mỗi tab một `Card` riêng chứ không bọc chung ngoài `Tabs`: bảng chạy
             `fillHeight` nên nó cần đúng một khung cha có chiều cao xác định. */}
        <TabsContent value={TAB_TO_APPROVE} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 flex-1 flex-col p-4">
            <LeaveToApproveTab />
          </Card>
        </TabsContent>

        <TabsContent value={TAB_MINE} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 flex-1 flex-col p-4">
            <LeaveMyRequestsTab />
          </Card>
        </TabsContent>

        <TabsContent value={TAB_HANDLED} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 flex-1 flex-col p-4">
            <LeaveHandledTab />
          </Card>
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
