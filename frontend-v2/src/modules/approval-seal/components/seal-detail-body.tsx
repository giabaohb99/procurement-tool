import { Building2, Stamp } from 'lucide-react'

import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Card } from '@/shared/ui/card'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { formatDateTime } from '@/shared/utils/format-date'
import type { SealRequest } from '../types/seal-request'
import { SealInfoItem as InfoItem } from './seal-info-item'
import { SealSectionHeader as SectionHeader } from './seal-section-header'

/**
 * Thân chi tiết yêu cầu đóng dấu — chỉ còn mạch *văn bản này là gì*:
 * - Khối 1: Thông tin văn bản & Mục đích sử dụng con dấu.
 * - Khối 2: Danh sách pháp nhân / Công ty cần đóng dấu.
 *
 * Ba khối kia dời sang CỘT PHẢI ngày 22/09/2026, mỗi khối một tệp riêng:
 * `seal-requester-card.tsx` · `seal-approval-info-card.tsx` · `seal-note-card.tsx`.
 */
export function SealDetailBody({ request }: { request: SealRequest }) {
  return (
    <div className="flex flex-col gap-5">
      {/*  Khối 1: Văn bản & Mục đích.
 *
 *  ⚠️ Xếp lại 22/09/2026 vì thẻ này ĐANG LẶP tiêu đề trang. `SealDetailHeader`
 *  đã bày mã phiếu · số bản · ngày gửi trên dải meta, lại còn `lg:sticky` nên
 *  dải đó nằm trong tầm mắt suốt lúc cuộn — bản trước dựng chúng thành bốn ô
 *  lưới nữa ở đây, thành ra cùng một con số hiện hai lần cách nhau 100px, và
 *  thứ DUY NHẤT thẻ này nói thêm được (trích yếu + mục đích ĐẦY ĐỦ — trên tiêu
 *  đề cả hai đều `line-clamp-1`) thì chìm giữa mấy ô lặp.
 *
 *  Nay: hai đoạn chữ là phần thân, ba con số rút xuống MỘT dòng chân nhỏ. Thêm
 *  gì vào thẻ này thì hỏi trước: *tiêu đề trang đã nói chưa?* */}
      <Card className="flex flex-col gap-4 p-5">
        <SectionHeader
          icon={Stamp}
          title="Nội dung văn bản & Mục đích đóng dấu"
          iconColor="text-rose-600 dark:text-rose-400"
        />

        <div className="flex flex-col gap-4">
          {request.title && (
            <InfoItem label="Trích yếu / Tiêu đề văn bản">
              <span className="text-base font-semibold text-navy dark:text-foreground leading-snug">
                {request.title}
              </span>
            </InfoItem>
          )}

          <InfoItem label="Mục đích sử dụng con dấu">
            <span className="whitespace-pre-wrap leading-relaxed text-foreground/90 font-normal">
              {request.purpose || '—'}
            </span>
          </InfoItem>
        </div>

        {/*  Dòng chân: ba con số nhận diện, chữ nhỏ, ngăn bằng dấu chấm giữa. Chúng
            là thứ để ĐỐI CHIẾU (đúng phiếu này không? mấy bản?) chứ không phải thứ
            để đọc, nên không đáng một ô có nhãn riêng. */}
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 border-t pt-3 text-xs text-muted-foreground">
          <span className="font-mono font-semibold text-primary">
            {request.code || 'Bản nháp'}
          </span>
          <span aria-hidden="true">·</span>
          <span>{request.copies ? `${request.copies} bản đóng dấu` : 'Chưa ghi số bản'}</span>
          <span aria-hidden="true">·</span>
          <span className="tabular-nums">
            {request.created_at ? `Gửi lúc ${formatDateTime(request.created_at)}` : 'Chưa gửi'}
          </span>
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

        {/*  ⚠️ DANH SÁCH DÒNG, không phải lưới thẻ (đổi 22/09/2026). Lưới
            `sm:grid-cols-2` chỉ đẹp ở số chẵn: phiếu một công ty — trường hợp
            THƯỜNG GẶP NHẤT — ra một thẻ con chiếm đúng nửa bề ngang rồi bỏ trống
            nửa còn lại, và phiếu ba công ty thì ô cuối lẻ loi y hệt. Mỗi dòng một
            pháp nhân thì số nào cũng đều, tên công ty dài cũng còn chỗ thở. */}
        {request.companies.length > 0 ? (
          <ul className="divide-y rounded-lg border">
            {request.companies.map((company, index) => {
              const initial = (company.name?.trim()[0] || '?').toUpperCase()
              return (
                <li
                  key={company.id ?? index}
                  className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3.5 py-3"
                >
                  <Avatar size="sm" className="size-9 shrink-0 rounded-md border border-border/60 bg-white shadow-2xs">
                    {company.logo && (
                      <AvatarImage src={company.logo} alt={company.name} className="object-contain p-1" />
                    )}
                    <AvatarFallback className="bg-primary/10 text-xs font-bold text-primary">
                      {initial}
                    </AvatarFallback>
                  </Avatar>

                  <p className="min-w-0 flex-1 text-sm font-medium leading-snug text-navy dark:text-foreground">
                    {company.name}
                  </p>

                  {/*  MST đẩy sang mép phải để mọi dòng thẳng cột — đây là con số
                      người ta dò theo chiều dọc, không phải đọc cùng tên. */}
                  {company.tax_code && (
                    <span className="shrink-0 font-mono text-xs text-muted-foreground">
                      MST <span className="font-medium text-foreground/80">{company.tax_code}</span>
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
        ) : (
          <ReadOnlyValue>—</ReadOnlyValue>
        )}
      </Card>

    </div>
  )
}
