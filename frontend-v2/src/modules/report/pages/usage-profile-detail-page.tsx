import { useParams } from 'react-router-dom'

import { extractErrorMessage } from '@/core/api'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'

import { UsageAiSection } from '../components/usage-profile/usage-ai-section'
import { UsageProfileHeaderCard } from '../components/usage-profile/usage-profile-header-card'
import { UsageProfileNoticeBanner } from '../components/usage-profile/usage-profile-notice-banner'
import { UsageProficiencySection } from '../components/usage-profile/usage-proficiency-section'
import { UsageResponseSection } from '../components/usage-profile/usage-response-section'
import { UsageRhythmSection } from '../components/usage-profile/usage-rhythm-section'
import { UsageScreensSection } from '../components/usage-profile/usage-screens-section'
import { UsageSecuritySection } from '../components/usage-profile/usage-security-section'
import { UsageStyleLabelsSection } from '../components/usage-profile/usage-style-labels-section'
import { UsageTaskSection } from '../components/usage-profile/usage-task-section'
import { useUsageProfile } from '../hooks/use-usage-profile'
import { USAGE_WEEK_OPTIONS } from '../utils/usage-profile-helpers'

const DEFAULT_WEEKS = 8

/** Hồ sơ cách làm việc MỘT người — chỉ ghép khối, mỗi khối một tệp trong `components/usage-profile/`. */
export function UsageProfileDetailPage() {
  const { userId } = useParams()
  const [weeksParam, setWeeksParam] = useUrlParamState('weeks', String(DEFAULT_WEEKS))
  const weeks = (USAGE_WEEK_OPTIONS as readonly number[]).includes(Number(weeksParam)) ? Number(weeksParam) : DEFAULT_WEEKS
  const id = Number(userId)
  const { data, isLoading, isError, error } = useUsageProfile(id, weeks)

  if (!Number.isInteger(id) || id <= 0 || isError) {
    return (
      <ErrorState
        title="Không mở được hồ sơ"
        description={isError ? extractErrorMessage(error) : 'Mã người dùng không hợp lệ.'}
      />
    )
  }
  if (isLoading || !data) {
    return (
      <PageContainer className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
      </PageContainer>
    )
  }

  const { latest } = data
  return (
    <PageContainer className="space-y-4">
      <UsageProfileNoticeBanner />
      <UsageProfileHeaderCard profile={data} weeks={weeks} onWeeksChange={(w) => setWeeksParam(String(w))} />
      {latest ? (
        <>
          <UsageStyleLabelsSection snapshot={latest} />
          <UsageRhythmSection profile={data} snapshot={latest} />
          <UsageScreensSection profile={data} snapshot={latest} />
          <UsageTaskSection snapshot={latest} />
          <UsageResponseSection snapshot={latest} />
          <UsageProficiencySection snapshot={latest} />
          <UsageSecuritySection snapshot={latest} />
          <UsageAiSection snapshot={latest} />
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          Chưa có bản tổng hợp tuần nào cho người này (bản tổng hợp chạy mỗi sáng thứ Hai).
        </p>
      )}
    </PageContainer>
  )
}
