import { ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { formatDate } from '@/shared/utils/format-date'
import { SR_STATUS_LABELS } from '../types/purchase-document'
import type { LinkedSurveyRequest } from '../types/purchase-request-detail'
import { StatusBadge } from './document-status-badge'

interface LinkedSurveyRequestCardProps {
  surveyRequest: LinkedSurveyRequest
  /** Không có quyền đọc YCBG thì mã là chữ thường — bấm vào chỉ ăn 403. */
  canOpen: boolean
}

/**
 * Một YCBG NGUỒN của phiếu YCMH ở khổ điện thoại — thay cho bảng 4 cột của thẻ
 * *Chứng từ liên quan*.
 *
 * ⚠️ **Người yêu cầu lên dòng đầu, mã phiếu tụt xuống dòng phụ**: mã YCBG chỉ khác
 * nhau vài chữ số cuối, xếp dọc đọc không ra phiếu nào của ai. Mã vẫn là LIÊN KẾT
 * sang chi tiết YCBG — thẻ không phải vùng bấm, nên liên kết đứng một mình được.
 */
export function LinkedSurveyRequestCard({ surveyRequest, canOpen }: LinkedSurveyRequestCardProps) {
  return (
    <div className="space-y-1.5 p-3">
      <p className="font-medium break-words text-foreground">
        {surveyRequest.requester || '(chưa rõ người yêu cầu)'}
      </p>

      <p className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
        {canOpen ? (
          <Link
            className="inline-flex items-center gap-1 font-medium text-sky-600 hover:underline dark:text-sky-400"
            to={appRoutes.procurement.surveyRequestDetail(surveyRequest.id)}
          >
            {surveyRequest.code}
            <ExternalLink className="size-3.5" />
          </Link>
        ) : (
          <span className="font-medium text-sky-600 dark:text-sky-400">{surveyRequest.code}</span>
        )}
        {surveyRequest.request_date && (
          <span>
            <span aria-hidden="true">· </span>
            {formatDate(surveyRequest.request_date)}
          </span>
        )}
      </p>

      <StatusBadge status={surveyRequest.status} labels={SR_STATUS_LABELS} />
    </div>
  )
}
