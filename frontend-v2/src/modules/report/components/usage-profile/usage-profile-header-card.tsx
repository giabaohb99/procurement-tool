import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { appRoutes } from '@/shared/constants/app-routes'

import type { UsageProfileDetail } from '../../types/usage-profile'
import { USAGE_WEEK_OPTIONS, describeCohort } from '../../utils/usage-profile-helpers'

interface UsageProfileHeaderCardProps {
  profile: UsageProfileDetail
  weeks: number
  onWeeksChange: (weeks: number) => void
}

/** Đầu hồ sơ: tên · mã · phòng · thâm niên · số tuần xem · nhóm đang so sánh. */
export function UsageProfileHeaderCard({ profile, weeks, onWeeksChange }: UsageProfileHeaderCardProps) {
  const { subject, latest } = profile
  return (
    <Card className="space-y-2 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Button variant="outline" size="icon" asChild aria-label="Về danh sách">
            <Link to={appRoutes.report.usageProfiles}>
              <ArrowLeft />
            </Link>
          </Button>
          <div>
            <h1 className="text-xl font-semibold">{subject.full_name}</h1>
            <p className="text-sm text-muted-foreground">
              {[
                subject.emp_code,
                subject.position,
                subject.department_name,
                subject.company_name,
                subject.role_names.length > 0 ? subject.role_names.join(', ') : null,
                subject.tenure_days != null ? `thâm niên ${subject.tenure_days} ngày` : null,
              ]
                .filter(Boolean)
                .join(' · ')}
            </p>
          </div>
        </div>
        <Select value={String(weeks)} onValueChange={(v) => onWeeksChange(Number(v))}>
          <SelectTrigger className="w-auto min-w-32" aria-label="Số tuần xem">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {USAGE_WEEK_OPTIONS.map((w) => (
              <SelectItem key={w} value={String(w)}>
                {w} tuần gần nhất
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {latest && <p className="text-sm text-muted-foreground">{describeCohort(latest.cohort)}</p>}
    </Card>
  )
}
