import { BadgeCheck, Stamp } from 'lucide-react'

import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Card } from '@/shared/ui/card'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import type { SealCompanyRef, SealRequest } from '../types/seal-request'

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

function InfoRow({
  label,
  children,
  className,
}: {
  label: string
  children: React.ReactNode
  className?: string
}) {
  return (
    //  `min-w-0`: ô lưới co được dưới bề rộng một từ dài (email/URL) để không đẩy tràn lưới.
    <div className={cn('flex min-w-0 flex-col gap-1', className)}>
      <span className="text-xs text-muted-foreground">{label}</span>
      <ReadOnlyValue>{children}</ReadOnlyValue>
    </div>
  )
}

/** Một dòng pháp nhân: logo + tên + mã số thuế. */
function CompanyRow({ company }: { company: SealCompanyRef }) {
  const initial = (company.name.trim()[0] || '?').toUpperCase()
  return (
    <div className="flex items-center gap-3 rounded-md border bg-muted/20 px-3 py-2">
      <Avatar size="sm" className="size-8">
        {company.logo && <AvatarImage src={company.logo} alt="" className="object-contain" />}
        <AvatarFallback>{initial}</AvatarFallback>
      </Avatar>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-navy dark:text-foreground">{company.name}</p>
        <p className="text-xs text-muted-foreground">MST: {company.tax_code || '—'}</p>
      </div>
    </div>
  )
}

/** Thân chi tiết phiếu đóng dấu — Block 1 (thông tin + người tạo) · Phê duyệt · Công ty · Ghi chú. */
export function SealDetailBody({ request }: { request: SealRequest }) {
  return (
    <>
      {/* Block 1 — thông tin phiếu + người tạo (mã, ngày tạo, người tạo, email, SĐT, vai trò, mục đích) */}
      {/*  pb-4: padding-bottom (dưới danh sách công ty) giảm từ 20px (p-5) còn 16px. */}
      <Card className="flex flex-col gap-4 p-5 pb-4">
        {/*  Tiêu đề block dạng icon + nhãn loại (giống Block 1 của Đặt xe). Gạch dưới kéo
            HẾT BỀ NGANG thẻ: `-mx-5` bù lại `p-5` của Card rồi `px-5` giữ chữ thẳng hàng.
            `-mt-1` kéo padding-top của tiêu đề từ 20px (p-5) còn 16px. */}
        <div className="-mx-5 -mt-1 flex items-center justify-between border-b px-5 pb-3">
          <span className="inline-flex items-center gap-2 font-medium">
            <Stamp className="size-5 text-rose-600 dark:text-rose-400" />
            Yêu cầu duyệt dấu
          </span>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Mã phiếu">{request.code || '— (phiếu nháp)'}</InfoRow>
          <InfoRow label="Ngày tạo">{formatDateTime(request.created_at) || '—'}</InfoRow>
          <InfoRow label="Người tạo">{request.requester || '—'}</InfoRow>
          <InfoRow label="Email">{request.requester_email || '—'}</InfoRow>
          <InfoRow label="Số điện thoại">{request.requester_phone || '—'}</InfoRow>
          <InfoRow label="Vai trò">{request.requester_role || '—'}</InfoRow>
          {/*  Mục đích trải hết 2 cột (rộng = SĐT + Vai trò) để đọc câu dài không bị cắt. */}
          <InfoRow label="Mục đích sử dụng" className="sm:col-span-2">
            {request.purpose || '—'}
          </InfoRow>
        </div>

        {/*  Công ty cần đóng dấu — nằm ngay trong Block 1, kế mục đích sử dụng. */}
        <div className="flex flex-col gap-2">
          <span className="text-xs text-muted-foreground">
            Công ty cần đóng dấu ({request.companies.length})
          </span>
          {request.companies.length > 0 ? (
            //  Mỗi công ty trải HẾT bề ngang (1 cột) để tên + MST không bị cắt cụt.
            <div className="flex flex-col gap-2">
              {request.companies.map((company) => (
                <CompanyRow key={company.id} company={company} />
              ))}
            </div>
          ) : (
            <ReadOnlyValue>—</ReadOnlyValue>
          )}
        </div>
      </Card>

      {/* Block 2 — Thông tin phê duyệt (TBP duyệt · Văn thư đóng dấu) */}
      <Card className="flex flex-col gap-4 p-5 pb-4">
        {/*  Header icon + gạch dưới hết bề ngang, padding giống Block 1. */}
        <div className="-mx-5 -mt-1 flex items-center justify-between border-b px-5 pb-3">
          <span className="inline-flex items-center gap-2 font-medium">
            <BadgeCheck className="size-5 text-emerald-600 dark:text-emerald-400" />
            Thông tin phê duyệt
          </span>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Người phê duyệt">{request.approver_name || '—'}</InfoRow>
          <InfoRow label="Ngày duyệt">{formatDateTime(request.approved_at) || '—'}</InfoRow>
          <InfoRow label="Văn thư">{request.completed_by_name || '—'}</InfoRow>
          <InfoRow label="Ngày hoàn thành yêu cầu">{formatDateTime(request.completed_at) || '—'}</InfoRow>
        </div>
      </Card>

      {/*  Chỉ hiện khi ghi chú CÓ NỘI DUNG THẬT — `.trim()` để ô toàn khoảng trắng /
          xuống dòng cũng coi như rỗng, không dựng khung trống. */}
      {request.note?.trim() && (
        <Card className="flex flex-col gap-2 p-5">
          <SectionHeading>Ghi chú</SectionHeading>
          <ReadOnlyValue multiline>{request.note}</ReadOnlyValue>
        </Card>
      )}
    </>
  )
}
