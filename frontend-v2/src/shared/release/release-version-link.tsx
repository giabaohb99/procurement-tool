import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'

import { runningVersionText } from './release-format'
import { useReleaseUnseen } from './use-release-info'

/**
 * Liên kết "Phiên bản 2.12.0" tới trang Có gì mới, kèm chấm đỏ khi có đợt chưa xem (bao-CR-722).
 * Dùng ở chân trang chủ (màn chọn phân hệ, không có menu trái) và chân menu trái của phân hệ.
 * Máy chủ chưa trả phiên bản thì không vẽ gì.
 */
export function ReleaseVersionLink({ className }: { className?: string }) {
  const { unseen, version } = useReleaseUnseen()
  if (!version) return null
  return (
    <Link
      to={appRoutes.whatsNew}
      className={cn('inline-flex items-center gap-1.5 hover:text-foreground hover:underline', className)}
      title={runningVersionText(version, '')}
    >
      {unseen && (
        <span className="size-1.5 shrink-0 rounded-full bg-destructive" role="status" aria-label="Có đợt cập nhật chưa xem" />
      )}
      <span>Phiên bản {version.version}</span>
    </Link>
  )
}
