import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Card } from '@/shared/ui/card'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { formatDateTime } from '@/shared/utils/format-date'
import type { SealCompanyRef, SealRequest } from '../types/seal-request'

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
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

/** Thân chi tiết phiếu đóng dấu — thẻ Thông tin yêu cầu · Công ty · Người tạo · Ghi chú. */
export function SealDetailBody({ request }: { request: SealRequest }) {
  return (
    <>
      <Card className="flex flex-col gap-4 p-5">
        <SectionHeading>Thông tin yêu cầu</SectionHeading>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Mã phiếu">{request.code || '— (phiếu nháp)'}</InfoRow>
          <InfoRow label="TBP phê duyệt">{request.approver_name}</InfoRow>
          <InfoRow label="Mục đích sử dụng">{request.purpose}</InfoRow>
          <InfoRow label="Số chứng từ đã ký">{String(request.signed_doc_count)}</InfoRow>
          <InfoRow label="Ngày tạo">{formatDateTime(request.created_at) || '—'}</InfoRow>
        </div>

        <div className="flex flex-col gap-2">
          <span className="text-xs text-muted-foreground">
            Công ty cần đóng dấu ({request.companies.length})
          </span>
          {request.companies.length > 0 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {request.companies.map((company) => (
                <CompanyRow key={company.id} company={company} />
              ))}
            </div>
          ) : (
            <ReadOnlyValue>—</ReadOnlyValue>
          )}
        </div>
      </Card>

      <Card className="flex flex-col gap-4 p-5">
        <SectionHeading>Người tạo</SectionHeading>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Tên">{request.requester}</InfoRow>
          <InfoRow label="Email">{request.requester_email}</InfoRow>
          <InfoRow label="Số điện thoại">{request.requester_phone}</InfoRow>
          <InfoRow label="Vai trò">{request.requester_role}</InfoRow>
        </div>
      </Card>

      {request.note && (
        <Card className="flex flex-col gap-2 p-5">
          <SectionHeading>Ghi chú</SectionHeading>
          <ReadOnlyValue multiline>{request.note}</ReadOnlyValue>
        </Card>
      )}
    </>
  )
}
