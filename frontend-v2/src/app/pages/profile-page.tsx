import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { ProfileAiConnectSection } from '@/app/components/profile/profile-ai-connect-section'
import { ProfileAiKeyTab } from '@/app/components/profile/profile-ai-key-tab'
import { ProfileChangesTab } from '@/app/components/profile/profile-changes-tab'
import { ProfileDevicesTab } from '@/app/components/profile/profile-devices-tab'
import { ProfileIdentityCard } from '@/app/components/profile/profile-identity-card'
import { ProfileInfoSection } from '@/app/components/profile/profile-info-section'
import { ProfileLaborContractsTab } from '@/app/components/profile/profile-labor-contracts-tab'
import { ProfileLoginHistoryTab } from '@/app/components/profile/profile-login-history-tab'
import { ProfileMemoryTab } from '@/app/components/profile/profile-memory-tab'
import { ProfilePasswordCard } from '@/app/components/profile/profile-password-card'
import {
  DEFAULT_PROFILE_SECTION,
  findProfileSection,
  listVisibleProfileGroups,
  resolveProfileSection,
  type ProfileSectionKey,
} from '@/app/components/profile/profile-sections'
import { ProfileSettingsNav } from '@/app/components/profile/profile-settings-nav'
import { ProfileWorkDecisionsTab } from '@/app/components/profile/profile-work-decisions-tab'
import { ProfileWorkHistoryTab } from '@/app/components/profile/profile-work-history-tab'
import { ProfileNotificationsTab } from '@/app/components/profile/profile-notifications-tab'
import { ProfileTasksTab } from '@/app/components/profile/profile-tasks-tab'
import { ProfileTelegramTab } from '@/app/components/profile/profile-telegram-tab'
import { ProfileTicketsTab } from '@/app/components/profile/profile-tickets-tab'
import { authService } from '@/core/auth/auth-service'
import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { useMyEmployee } from '@/modules/hr/hooks/use-employees'
import { queryKeys } from '@/shared/constants/query-keys'
import { useNotifications } from '@/shared/notifications/use-notifications'
import { ThemePresetPicker } from '@/shared/theme/theme-preset-picker'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'

/**
 * TRANG CÁ NHÂN — hồ sơ của chính người đang đăng nhập.
 *
 * Bố cục trang cài đặt có THANH BÊN TRÁI, 4 nhóm (P0 doc 21 §6.5 + §7.1, thay dải 13 tab ngang tràn hàng):
 * - Hồ sơ: Thông tin cá nhân (`ProfileInfoSection`: quỹ phép, lương, hồ sơ, ca, chữ ký, email thông báo) · Quá trình công tác · Quyết định bổ
 *   nhiệm — hai mục sau CHỈ ĐỌC, ẩn khi tài khoản chưa gắn hồ sơ nhân sự (`employee_id = 0`, đại ca chốt 03/10/2026).
 * - Việc của tôi: Việc cần làm (CR-215 gom cả "Chờ tôi duyệt") · Thông báo (bản đầy đủ của chuông) · Yêu cầu hỗ trợ
 *   (gác `ticket.read`).
 * - Trợ lý AI của tôi: Kết nối AI riêng (ĐẦU TIÊN — đường chính từ 17/10, tách khối MCP khỏi tab Khóa AI) · Khóa
 *   model AI · Liên kết Telegram · Bot nhớ gì về tôi (ai-CR-138) · Bot vừa làm gì (ai-CR-185).
 * - Bảo mật & hiển thị: Đổi mật khẩu · Thiết bị của tôi (bao-CR-395) · Lịch sử đăng nhập (bao-CR-400) · Giao diện.
 *
 * Đường dẫn giữ từng mục ở `?tab=` và mọi tên tab cũ vẫn mở đúng chỗ — luật đọc nằm ở `profile-sections.ts`.
 * Chỉ dời và đổi tên giao diện: không đổi API, không đổi dữ liệu.
 */
export function ProfilePage() {
  const { user, setUser } = useAuth()
  const { can } = usePermission()
  const [searchParams, setSearchParams] = useSearchParams()
  const [taskCount, setTaskCount] = useState<number>(0)
  const [ticketCount, setTicketCount] = useState<number>(0)

  const canReadTickets = can('ticket', 'read')

  // Số chưa đọc dùng chung cache với cái chuông (poll 20s) — không đợi mở mục.
  const { data: bellData } = useNotifications(false)
  const unreadCount = bellData?.unread ?? 0

  //  Hồ sơ nhân sự đầy đủ (hơn 30 trường) — `/api/auth/me` chỉ trả bộ rút gọn đủ dựng menu và chữ ký, không có
  //  ngày sinh / ngân hàng / giấy tờ. Lấy lên ĐẦU hàm (trước `active`) vì hai mục Quá trình công tác / Quyết định
  //  bổ nhiệm gác theo cờ này — tài khoản chưa gắn hồ sơ (admin, tài khoản hệ thống) thì KHÔNG bày hai mục đó ra,
  //  cùng luật với `ProfileLeaveCard`.
  const { data: myEmployee } = useMyEmployee()
  const hasEmployeeProfile = Boolean(myEmployee)

  const access = { hasEmployeeProfile, canReadTickets }
  const groups = listVisibleProfileGroups(access)
  const active = resolveProfileSection(searchParams.get('tab'), access)
  const { group: activeGroup, section: activeSection } = findProfileSection(active)

  const handleSelect = (key: ProfileSectionKey) => {
    setSearchParams(key === DEFAULT_PROFILE_SECTION ? {} : { tab: key }, { replace: true })
  }

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: () => authService.me(),
  })

  useEffect(() => {
    if (data) setUser(data)
  }, [data, setUser])

  const profile = data ?? user

  function renderInfo() {
    if (isPending && !profile) {
      return (
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      )
    }
    //  Bố cục của mục nằm ở `ProfileInfoSection` (duoc-CR-766).
    return profile ? <ProfileInfoSection profile={profile} employee={myEmployee} /> : null
  }

  //  Mỗi lúc chỉ dựng ĐÚNG một mục (giống Radix Tabs cũ không mount tab ẩn): mục nào tự gọi API riêng thì chỉ gọi
  //  khi được mở. Hai số đếm Việc cần làm / Yêu cầu hỗ trợ vì thế chỉ có sau khi mở mục đó một lần — như bản tab cũ.
  function renderSection(key: ProfileSectionKey) {
    switch (key) {
      case 'info':
        return renderInfo()
      case 'work-history':
        return <ProfileWorkHistoryTab />
      case 'decisions':
        return <ProfileWorkDecisionsTab />
      case 'labor-contracts':
        return <ProfileLaborContractsTab />
      case 'tasks':
        return <ProfileTasksTab onCountChange={setTaskCount} />
      case 'notifications':
        return <ProfileNotificationsTab />
      case 'tickets':
        return <ProfileTicketsTab onCountChange={setTicketCount} />
      case 'ai-connect':
        return <ProfileAiConnectSection />
      case 'ai-key':
        return <ProfileAiKeyTab />
      case 'telegram':
        return <ProfileTelegramTab />
      case 'bot-memory':
        return <ProfileMemoryTab />
      case 'bot-changes':
        return <ProfileChangesTab />
      case 'password':
        return <ProfilePasswordCard />
      case 'devices':
        return <ProfileDevicesTab />
      case 'login-history':
        return <ProfileLoginHistoryTab />
      case 'appearance':
        //  Cùng một bộ chọn với phân hệ Giao diện — chỉ khác số cột, vì cột nội dung hẹp hơn (có thanh bên).
        return <ThemePresetPicker columnsClassName="sm:grid-cols-3 lg:grid-cols-4" />
    }
  }

  return (
    <PageContainer className="mx-auto w-full max-w-6xl">
      <PageHeader
        title="Trang cá nhân"
        description="Hồ sơ, việc của bạn, trợ lý AI, bảo mật và giao diện"
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

          {/*  `md:items-start` + `sticky` cho thanh bên đứng yên khi cuộn nội dung dài (mục Thông tin cá nhân).
               `min-w-0` ở cột nội dung là BẮT BUỘC: con của flex mặc định `min-width: auto`, nên một dòng `truncate`
               dài trong hồ sơ đẩy cột tràn khỏi khung (cùng lỗi đã đo ở lưới hồ sơ, xem chú thích bên trong). */}
          <div className="flex flex-col gap-6 md:flex-row md:items-start">
            <ProfileSettingsNav
              groups={groups}
              active={active}
              onSelect={handleSelect}
              badges={{
                tasks: { count: taskCount, variant: 'destructive' },
                notifications: { count: unreadCount, variant: 'destructive' },
                tickets: { count: ticketCount, variant: 'secondary' },
              }}
              className="md:sticky md:top-4 md:w-56 md:shrink-0"
            />
            <section aria-labelledby="profile-section-title" className="min-w-0 flex-1 space-y-4">
              <div>
                <p className="text-xs text-muted-foreground">{activeGroup.label}</p>
                <h2 id="profile-section-title" className="text-lg font-semibold">
                  {activeSection.label}
                </h2>
              </div>
              {renderSection(active)}
            </section>
          </div>
        </div>
      )}
    </PageContainer>
  )
}
