import { useQuery } from '@tanstack/react-query'
import { Bell, CheckSquare, LifeBuoy, Palette, User } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { EmailNotificationCard } from '@/app/components/profile/email-notification-card'
import { ProfileIdentityCard } from '@/app/components/profile/profile-identity-card'
import { ProfileHrDetails } from '@/app/components/profile/profile-hr-details'
import { ProfileInfoCard } from '@/app/components/profile/profile-info-card'
import { ProfileNotificationsTab } from '@/app/components/profile/profile-notifications-tab'
import { ProfileTasksTab } from '@/app/components/profile/profile-tasks-tab'
import { ProfileTicketsTab } from '@/app/components/profile/profile-tickets-tab'
import { SignatureCard } from '@/app/components/profile/signature-card'
import { AuditTimeline } from '@/shared/audit'
import { authService } from '@/core/auth/auth-service'
import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { useMyEmployee } from '@/modules/hr/hooks/use-employees'
import { queryKeys } from '@/shared/constants/query-keys'
import { useNotifications } from '@/shared/notifications/use-notifications'
import { ThemePresetPicker } from '@/shared/theme/theme-preset-picker'
import { Badge } from '@/shared/ui/badge'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { Skeleton } from '@/shared/ui/skeleton'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'

/**
 * TRANG CÁ NHÂN — hồ sơ của chính người đang đăng nhập.
 *
 * Gồm dải tab chuẩn:
 * - Tab "Thông tin cá nhân": Xem hồ sơ, đổi chữ ký, đổi mật khẩu.
 * - Tab "Việc cần làm": Việc đang chờ xử lý (chứng từ chờ duyệt, YCMH, YCBG, ĐMH,
 *   giao trễ, công nợ) — CR-215 gom luôn "Chờ tôi duyệt" vào đây.
 * - Tab "Thông báo": Bản đầy đủ của chuông thông báo (thay trang /notifications cũ).
 * - Tab "Yêu cầu hỗ trợ của tôi": Các phiếu hỗ trợ người dùng đã gửi hệ thống.
 */
export function ProfilePage() {
  const { user, setUser } = useAuth()
  const { can } = usePermission()
  const [searchParams, setSearchParams] = useSearchParams()
  const [taskCount, setTaskCount] = useState<number>(0)
  const [ticketCount, setTicketCount] = useState<number>(0)

  const canReadTickets = can('ticket', 'read')

  // Số chưa đọc dùng chung cache với cái chuông (poll 20s) — không đợi mở tab.
  const { data: bellData } = useNotifications(false)
  const unreadCount = bellData?.unread ?? 0

  const rawTab = searchParams.get('tab')
  const activeTab =
    rawTab === 'tasks'
      ? 'tasks'
      : rawTab === 'notifications'
        ? 'notifications'
        : rawTab === 'appearance'
          ? 'appearance'
          : rawTab === 'tickets' && canReadTickets
            ? 'tickets'
            : 'info'

  const handleTabChange = (val: string) => {
    setSearchParams(val === 'info' ? {} : { tab: val }, { replace: true })
  }

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: () => authService.me(),
  })

  useEffect(() => {
    if (data) setUser(data)
  }, [data, setUser])

  const profile = data ?? user

  //  Hồ sơ nhân sự đầy đủ (hơn 30 trường) — `/api/auth/me` chỉ trả bộ rút
  //  gọn đủ dựng menu và chữ ký, không có ngày sinh / ngân hàng / giấy tờ.
  const { data: myEmployee } = useMyEmployee()

  return (
    <PageContainer className="mx-auto w-full max-w-5xl">
      <PageHeader
        title="Trang cá nhân"
        description="Thông tin tài khoản, mật khẩu, chữ ký, việc cần xử lý và yêu cầu hỗ trợ"
      />

      {isError && !profile ? (
        <ErrorState
          title="Không tải được hồ sơ"
          description="Máy chủ chưa trả về thông tin tài khoản. Hãy thử lại sau ít phút."
        >
          <button
            type="button"
            onClick={() => void refetch()}
            className="text-sm font-medium text-primary hover:underline"
          >
            Tải lại
          </button>
        </ErrorState>
      ) : (
        <div className="space-y-6">
          <ProfileIdentityCard profile={profile} />

          <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-4">
            {/*  ⚠️ Dải này TỪNG là `TabsList` nền xám khai thêm `flex-wrap`, và đó
                 là một sự kết hợp hỏng: `TabsList` của shadcn ghim `h-9`, nên khi
                 năm nhãn tiếng Việt xuống thành ba hàng (đo ở 390px: cần 90px,
                 ô chỉ cao 36px) thì hai hàng dưới TRÀN RA NGOÀI ô và bị thẻ nội
                 dung bên dưới che mất — tab «Thông báo» và «Giao diện» không bấm
                 được. Cuộn ngang thay cho xuống hàng cũng là lối chung của các
                 màn nhiều tab khác (chi tiết Văn thư, chi tiết CRUD). */}
            {/*  ⚠️ `listClassName` xử lý dải 768–805px — chỗ `max-md:*` vừa tắt
                 (dải về nền xám, hết cuộn ngang) mà khung vẫn chưa đủ rộng. Đo ở
                 768px: năm nhãn cần 773px, khung chỉ có 736px, nên tab «Giao
                 diện» rơi ra ngoài mép phải và KHÔNG có cách nào chạm tới — không
                 cuộn, không mũi tên. Cho xuống hàng là xong, nhưng phải gỡ luôn
                 `h-9` của `TabsList` và `h-[calc(100%-1px)]` của từng tab: giữ
                 chúng thì hàng thứ hai tràn ra ngoài ô và bị che, đúng lỗi cũ. */}
            <ScrollableTabsList
              value={activeTab}
              className="mb-2"
              //  `md:justify-start`: `TabsList` canh giữa, nên hàng thứ hai chỉ
              //  có một tab thì nó đứng chính giữa, rời hẳn khỏi hàng trên và
              //  đọc ra như một nút lạc chứ không như tab tiếp theo.
              listClassName="md:h-auto md:flex-wrap md:justify-start md:[&_[data-slot=tabs-trigger]]:h-8"
            >
              <TabsTrigger value="info" className={cn('gap-2', TAB_TRIGGER_UNDERLINE)}>
                <User className="size-4" />
                <span>Thông tin cá nhân</span>
              </TabsTrigger>
              <TabsTrigger value="tasks" className={cn('gap-2', TAB_TRIGGER_UNDERLINE)}>
                <CheckSquare className="size-4" />
                <span>Việc cần làm</span>
                {taskCount > 0 && (
                  <Badge variant="destructive" className="h-4 px-1.5 text-[10px]">
                    {taskCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="notifications" className={cn('gap-2', TAB_TRIGGER_UNDERLINE)}>
                <Bell className="size-4" />
                <span>Thông báo</span>
                {unreadCount > 0 && (
                  <Badge variant="destructive" className="h-4 px-1.5 text-[10px]">
                    {unreadCount}
                  </Badge>
                )}
              </TabsTrigger>
              {canReadTickets && (
                <TabsTrigger value="tickets" className={cn('gap-2', TAB_TRIGGER_UNDERLINE)}>
                  <LifeBuoy className="size-4" />
                  <span>Yêu cầu hỗ trợ của tôi</span>
                  {ticketCount > 0 && (
                    <Badge variant="secondary" className="h-4 px-1.5 text-[10px]">
                      {ticketCount}
                    </Badge>
                  )}
                </TabsTrigger>
              )}
              <TabsTrigger value="appearance" className={cn('gap-2', TAB_TRIGGER_UNDERLINE)}>
                <Palette className="size-4" />
                <span>Giao diện</span>
              </TabsTrigger>
            </ScrollableTabsList>

            <TabsContent value="info" className="space-y-6">
              {isPending && !profile ? (
                <div className="grid gap-4 lg:grid-cols-2">
                  <Skeleton className="h-64" />
                  <Skeleton className="h-64" />
                </div>
              ) : (
                profile && (
                  <>
                    {/* Hàng 1: 2 cột cao BẰNG NHAU (items-stretch). Cột 1 xếp
                        [Hồ sơ nhân sự] trên + [Tài khoản] dưới; cột 2 là [Chữ ký]
                        kéo cao đầy cột. */}
                    {/*  ⚠️ `min-w-0` ở HAI Ô LƯỚI là bắt buộc, không phải dọn dẹp.
                         Ô của lưới mặc định `min-width: auto`, tức KHÔNG co xuống
                         dưới bề rộng nội dung tối thiểu — mà các dòng hồ sơ dùng
                         `truncate` (= `white-space: nowrap`), nên bề rộng tối
                         thiểu của chúng là TOÀN BỘ chuỗi chưa cắt. Đo ở 390px:
                         dòng «Công ty / Pháp nhân» đòi 418px, kéo cả cột lên
                         452px trong khi chỗ có là 358px — thẻ tràn khỏi màn và
                         `truncate` không bao giờ có dịp cắt chữ. */}
                    <div className="grid items-stretch gap-4 lg:grid-cols-2">
                      <div className="flex min-w-0 flex-col gap-4">
                        <ProfileInfoCard profile={profile} />
                      </div>
                      <div className="flex min-w-0 flex-col gap-4">
                        <SignatureCard signature={profile.signature} />
                        {/* bao-CR-349 — công tắc email thông báo của chính mình.
                            Xếp dưới Chữ ký để hai cột cân nhau; đây cũng là cửa
                            người dùng TỰ tắt, ba cửa còn lại là của quản trị. */}
                        <EmailNotificationCard value={profile.notify_email} />
                      </div>
                    </div>

                    {/*  HỒ SƠ NHÂN SỰ ĐẦY ĐỦ (duoc-CR-378) — sáu khối chỉ xem,
                         đọc từ `/api/employees/me`. Trước đó trang này chỉ có 7 ô
                         lấy từ phiên đăng nhập, trong khi hồ sơ thật có hơn 30
                         trường: người dùng muốn soát lại ngày sinh hay số tài
                         khoản nhận lương của CHÍNH MÌNH thì không có chỗ nào xem.

                         Đặt NGOÀI lưới phía trên và tự dựng lưới riêng — xem ghi
                         chú trong `ProfileHrDetails`.

                         `myEmployee` rỗng khi tài khoản chưa gắn hồ sơ nhân sự
                         (admin, tài khoản hệ thống): không dựng khối nào, và thẻ
                         «Hồ sơ nhân sự» phía trên đã có sẵn câu nhắc liên hệ bộ
                         phận Nhân sự. */}
                    {myEmployee && <ProfileHrDetails employee={myEmployee} />}

                    {/*  ⚠️ Gọi TRẦN, đừng bọc `FormCard`. `AuditTimeline` tự dựng
                         `Card` kèm tiêu đề «Lịch sử thao tác» của chính nó, nên
                         bọc thêm là **thẻ trong thẻ, tiêu đề in hai lần** — hai
                         khung viền lồng nhau còn ăn thêm hai lớp đệm, ở khổ điện
                         thoại thì thấy rõ ngay. Mọi màn khác đều gọi trần. */}
                    <AuditTimeline entity="user" entityId={profile.id} />
                  </>
                )
              )}
            </TabsContent>

            <TabsContent value="tasks" className="space-y-4">
              <ProfileTasksTab onCountChange={setTaskCount} />
            </TabsContent>

            <TabsContent value="notifications" className="space-y-4">
              <ProfileNotificationsTab />
            </TabsContent>

            {canReadTickets && (
              <TabsContent value="tickets" className="space-y-4">
                <ProfileTicketsTab onCountChange={setTicketCount} />
              </TabsContent>
            )}

            {/* Cùng một bộ chọn với phân hệ Giao diện — chỉ khác số cột, vì tab
                này hẹp hơn (khung hồ sơ giới hạn `max-w-5xl`). */}
            <TabsContent value="appearance" className="space-y-4">
              <ThemePresetPicker columnsClassName="sm:grid-cols-3 lg:grid-cols-4" />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </PageContainer>
  )
}
