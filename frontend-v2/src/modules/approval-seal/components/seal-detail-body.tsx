import { BadgeCheck, Building2, NotebookPen, Stamp, UserCheck } from 'lucide-react'
import type { ReactNode } from 'react'

import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Card } from '@/shared/ui/card'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import type { SealRequest } from '../types/seal-request'

function InfoItem({
  label,
  children,
  className,
}: {
  label: string
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn('flex min-w-0 flex-col gap-1', className)}>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <div className="text-sm text-foreground font-medium">{children}</div>
    </div>
  )
}

function SectionHeader({
  icon: Icon,
  title,
  iconColor = 'text-primary',
  extra,
}: {
  icon: React.ElementType
  title: string
  iconColor?: string
  extra?: ReactNode
}) {
  return (
    <div className="-mx-5 -mt-1 flex items-center justify-between border-b border-border/50 px-5 pb-3">
      <div className="flex items-center gap-2 font-semibold text-sm text-navy dark:text-foreground">
        <Icon className={cn('size-4.5 shrink-0', iconColor)} />
        <span>{title}</span>
      </div>
      {extra && <div className="text-xs text-muted-foreground">{extra}</div>}
    </div>
  )
}

/**
 * Thân chi tiết yêu cầu đóng dấu:
 * - Khối 1: Thông tin văn bản & Mục đích sử dụng con dấu.
 * - Khối 2: Danh sách pháp nhân / Công ty cần đóng dấu.
 * - Khối 3: Thông tin người yêu cầu & Đơn vị.
 * - Khối 4: Tiến trình phê duyệt & Văn thư đóng dấu.
 * - Khối 5: Ghi chú đính kèm (nếu có).
 */
export function SealDetailBody({ request }: { request: SealRequest }) {
  const hasApprovalInfo = Boolean(
    request.approver_name || request.approved_at || request.completed_by_name || request.completed_at,
  )

  return (
    <div className="flex flex-col gap-5">
      {/* Khối 1: Văn bản & Mục đích */}
      <Card className="flex flex-col gap-4 p-5">
        <SectionHeader
          icon={Stamp}
          title="Thông tin văn bản & Mục đích đóng dấu"
          iconColor="text-rose-600 dark:text-rose-400"
          extra={
            <span className="font-mono text-xs font-semibold text-primary">
              {request.code || 'Bản nháp'}
            </span>
          }
        />

        <div className="grid gap-4 sm:grid-cols-2">
          {request.title && (
            <InfoItem label="Trích yếu / Tiêu đề văn bản" className="sm:col-span-2">
              <span className="text-base font-semibold text-navy dark:text-foreground leading-snug">
                {request.title}
              </span>
            </InfoItem>
          )}

          <InfoItem label="Mục đích sử dụng con dấu" className="sm:col-span-2">
            <span className="whitespace-pre-wrap leading-relaxed text-foreground/90 font-normal">
              {request.purpose || '—'}
            </span>
          </InfoItem>

          <InfoItem label="Số lượng bản đóng dấu">
            <span className="font-mono font-semibold text-foreground">
              {request.copies ? `${request.copies} bản` : '—'}
            </span>
          </InfoItem>

          <InfoItem label="Thời điểm gửi yêu cầu">
            <span className="tabular-nums font-normal text-muted-foreground">
              {formatDateTime(request.created_at) || '—'}
            </span>
          </InfoItem>
        </div>
      </Card>

      {/* Khối 2: Pháp nhân / Công ty cần đóng dấu */}
      <Card className="flex flex-col gap-4 p-5">
        <SectionHeader
          icon={Building2}
          title="Pháp nhân / Công ty đóng dấu"
          iconColor="text-blue-600 dark:text-blue-400"
          extra={
            <span className="text-xs text-muted-foreground">
              {request.companies.length} công ty
            </span>
          }
        />

        {request.companies.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {request.companies.map((company, index) => {
              const initial = (company.name?.trim()[0] || '?').toUpperCase()
              return (
                <div
                  key={company.id ?? index}
                  className="group relative flex items-start gap-3 rounded-lg border border-border/70 bg-card p-3.5 transition-all hover:border-primary/40 hover:shadow-xs"
                >
                  <Avatar size="sm" className="size-9 shrink-0 rounded-md border border-border/60 bg-white shadow-2xs">
                    {company.logo && (
                      <AvatarImage src={company.logo} alt={company.name} className="object-contain p-1" />
                    )}
                    <AvatarFallback className="bg-primary/10 text-xs font-bold text-primary">
                      {initial}
                    </AvatarFallback>
                  </Avatar>

                  <div className="min-w-0 flex-1 space-y-1">
                    <p className="font-semibold text-xs leading-snug text-navy dark:text-foreground">
                      {company.name}
                    </p>
                    {company.tax_code && (
                      <p className="font-mono text-[11px] text-muted-foreground">
                        MST: <span className="font-medium text-foreground/80">{company.tax_code}</span>
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <ReadOnlyValue>—</ReadOnlyValue>
        )}
      </Card>

      {/* Khối 3: Thông tin người tạo & Đơn vị */}
      <Card className="flex flex-col gap-4 p-5">
        <SectionHeader
          icon={UserCheck}
          title="Người yêu cầu & Đơn vị"
          iconColor="text-indigo-600 dark:text-indigo-400"
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <InfoItem label="Họ và tên">
            <span>{request.requester || '—'}</span>
          </InfoItem>

          <InfoItem label="Chức danh / Phòng ban">
            <span className="text-muted-foreground">{request.requester_role || '—'}</span>
          </InfoItem>

          <InfoItem label="Email liên hệ">
            <span className="font-mono text-xs text-muted-foreground">
              {request.requester_email || '—'}
            </span>
          </InfoItem>

          <InfoItem label="Số điện thoại">
            <span className="font-mono text-xs text-muted-foreground">
              {request.requester_phone || '—'}
            </span>
          </InfoItem>
        </div>
      </Card>

      {/* Khối 4: Thông tin phê duyệt & Đóng dấu (hiện khi đã có dữ liệu duyệt) */}
      {hasApprovalInfo && (
        <Card className="flex flex-col gap-4 p-5">
          <SectionHeader
            icon={BadgeCheck}
            title="Thông tin phê duyệt & Đóng dấu"
            iconColor="text-emerald-600 dark:text-emerald-400"
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <InfoItem label="Trưởng bộ phận phê duyệt">
              <span>{request.approver_name || '—'}</span>
            </InfoItem>

            <InfoItem label="Thời điểm phê duyệt">
              <span className="tabular-nums text-muted-foreground">
                {formatDateTime(request.approved_at) || '—'}
              </span>
            </InfoItem>

            <InfoItem label="Văn thư thực hiện đóng dấu">
              <span>{request.completed_by_name || '—'}</span>
            </InfoItem>

            <InfoItem label="Thời điểm hoàn tất đóng dấu">
              <span className="tabular-nums text-muted-foreground">
                {formatDateTime(request.completed_at) || '—'}
              </span>
            </InfoItem>
          </div>
        </Card>
      )}

      {/* Khối 5: Ghi chú của người yêu cầu */}
      {request.note?.trim() && (
        <Card className="flex flex-col gap-4 p-5">
          <SectionHeader
            icon={NotebookPen}
            title="Ghi chú người gửi"
            iconColor="text-amber-600 dark:text-amber-400"
          />
          <ReadOnlyValue multiline>{request.note}</ReadOnlyValue>
        </Card>
      )}
    </div>
  )
}
