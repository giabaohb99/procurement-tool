import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'

import { authService } from '@/core/auth/auth-service'
import { useAuth } from '@/core/auth/use-auth'
import { ChangePasswordCard } from '@/app/components/profile/change-password-card'
import { ProfileIdentityCard } from '@/app/components/profile/profile-identity-card'
import { ProfileInfoCard } from '@/app/components/profile/profile-info-card'
import { SignatureCard } from '@/app/components/profile/signature-card'
import { queryKeys } from '@/shared/constants/query-keys'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'

/**
 * TRANG CÁ NHÂN — hồ sơ của chính người đang đăng nhập.
 *
 * Đứng ở tầng chung (`/me`, khung launcher) chứ không thuộc phân hệ nào: tài
 * khoản là của người dùng, không phải của Thu mua hay Nhân sự.
 *
 * Vẫn gọi lại `/api/auth/me` dù store đã có sẵn người dùng: bản trong store là
 * ảnh chụp lúc đăng nhập, phòng ban / chức danh / vai trò có thể đã được Nhân sự
 * sửa từ hôm qua. Kết quả mới được ghi ngược vào store để menu tài khoản và các
 * phiếu in dùng chung một nguồn.
 */
export function ProfilePage() {
  const { user, setUser } = useAuth()

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: () => authService.me(),
  })

  useEffect(() => {
    if (data) setUser(data)
    // `setUser` lấy từ zustand nên giữ nguyên tham chiếu; chỉ chạy lại khi có
    // dữ liệu mới thật sự.
  }, [data, setUser])

  // Trong lúc chờ mạng vẫn dựng được thẻ danh tính từ bản trong store — người
  // dùng thấy tên mình ngay, không phải nhìn khung xám toàn trang.
  const profile = data ?? user

  return (
    <PageContainer className="mx-auto w-full max-w-5xl">
      <PageHeader
        title="Trang cá nhân"
        description="Thông tin tài khoản, mật khẩu và chữ ký dùng cho phiếu in"
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
        <div className="flex flex-col gap-4">
          <ProfileIdentityCard profile={profile} />

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
        </div>
      )}
    </PageContainer>
  )
}
