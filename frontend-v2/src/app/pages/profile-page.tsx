import { useQuery } from '@tanstack/react-query'
import { Bell, CheckSquare, LifeBuoy, Palette, User } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { ChangePasswordCard } from '@/app/components/profile/change-password-card'
import { ProfileIdentityCard } from '@/app/components/profile/profile-identity-card'
import { ProfileInfoCard } from '@/app/components/profile/profile-info-card'
import { ProfileNotificationsTab } from '@/app/components/profile/profile-notifications-tab'
import { ProfileTasksTab } from '@/app/components/profile/profile-tasks-tab'
import { ProfileTicketsTab } from '@/app/components/profile/profile-tickets-tab'
import { SignatureCard } from '@/app/components/profile/signature-card'
import { authService } from '@/core/auth/auth-service'
import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'
import { useNotifications } from '@/shared/notifications/use-notifications'
import { ThemePresetPicker } from '@/shared/theme/theme-preset-picker'
import { Badge } from '@/shared/ui/badge'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'

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
            <TabsList className="mb-2 flex-wrap">
              <TabsTrigger value="info" className="gap-2">
                <User className="size-4" />
                <span>Thông tin cá nhân</span>
              </TabsTrigger>
              <TabsTrigger value="tasks" className="gap-2">
                <CheckSquare className="size-4" />
                <span>Việc cần làm</span>
                {taskCount > 0 && (
                  <Badge variant="destructive" className="h-4 px-1.5 text-[10px]">
                    {taskCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="notifications" className="gap-2">
                <Bell className="size-4" />
                <span>Thông báo</span>
                {unreadCount > 0 && (
                  <Badge variant="destructive" className="h-4 px-1.5 text-[10px]">
                    {unreadCount}
                  </Badge>
                )}
              </TabsTrigger>
              {canReadTickets && (
                <TabsTrigger value="tickets" className="gap-2">
                  <LifeBuoy className="size-4" />
                  <span>Yêu cầu hỗ trợ của tôi</span>
                  {ticketCount > 0 && (
                    <Badge variant="secondary" className="h-4 px-1.5 text-[10px]">
                      {ticketCount}
                    </Badge>
                  )}
                </TabsTrigger>
              )}
              <TabsTrigger value="appearance" className="gap-2">
                <Palette className="size-4" />
                <span>Giao diện</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="info" className="space-y-6">
              {isPending && !profile ? (
                <div className="grid gap-4 lg:grid-cols-2">
                  <Skeleton className="h-64" />
                  <Skeleton className="h-64" />
                </div>
              ) : (
                <div className="grid items-start gap-4 lg:grid-cols-2">
                  <div className="flex flex-col gap-4">
                    {profile && <ProfileInfoCard profile={profile} />}
                  </div>
                  <div className="flex flex-col gap-4">
                    <SignatureCard signature={profile?.signature} />
                    <ChangePasswordCard />
                  </div>
                </div>
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
