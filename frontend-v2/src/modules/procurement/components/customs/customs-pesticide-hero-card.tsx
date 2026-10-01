// Thẻ ĐẦU TRANG chi tiết thuốc BVTV (01/10/2026 — làm lại cả trang sau ba lần vá từng khối bị chê).
// Gom thứ người đọc cần ngay vào một chỗ: tên + tình trạng + nút thao tác, hoạt chất, công ty, số đăng
// ký (chép được), bốn ô thông tin nhanh và câu tóm tắt. Lưới nhãn – giá trị chín dòng cũ bỏ hẳn.
import type { ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { CopyButton } from '@/shared/ui/copy-button'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

import type { CustomsPesticide } from '../../types/customs-pesticide'
import {
  describeRemainingTerm,
  parsePesticideToxicity,
  toSentenceCaseIfShouting,
  type ToxicityItem,
  type ToxicitySeverity,
} from '../../utils/customs-pesticide-display'
import { CustomsPesticideStatusBadge } from './customs-pesticide-status-badge'

interface CustomsPesticideHeroCardProps {
  pesticide: CustomsPesticide
  /** Nút lùi — đứng trước tên thuốc. */
  leading: ReactNode
  /** Sửa · Xóa · Tra cứu (màn hẹp) — góc phải dòng tên. */
  actions?: ReactNode
}

export function CustomsPesticideHeroCard({
  pesticide,
  leading,
  actions,
}: CustomsPesticideHeroCardProps) {
  const p = pesticide
  //  Trống thì nói rõ, đừng để một ô trắng tưởng lỗi màn: thuốc từ bản cào là «Nguồn không ghi»,
  //  thuốc tự thêm là «Chưa nhập» (không có nguồn nào để mà «không ghi»).
  const missing = p.is_manual ? 'Chưa nhập' : 'Nguồn không ghi'
  const remaining = describeRemainingTerm(p.expires_on, new Date())
  const toxicity = parsePesticideToxicity(p.toxicity)

  return (
    <Card className="gap-0 py-0">
      <div className="space-y-4 p-5">
        <div className="flex flex-wrap items-start gap-3">
          {leading}
          <div className="min-w-0 flex-1 space-y-1">
            <h1 className="flex flex-wrap items-center gap-2 text-xl font-semibold text-navy dark:text-foreground">
              {p.trade_name}
              <CustomsPesticideStatusBadge status={p.status} label={p.status_label} />
              {p.is_manual && <Badge variant="outline">Tự thêm</Badge>}
            </h1>
            <p className="text-sm">
              <span className="font-medium">{p.active_ingredient || missing}</span>
              {p.concentration && (
                <span className="text-muted-foreground"> · {p.concentration}</span>
              )}
            </p>
            <p className="flex flex-wrap items-center gap-x-2 text-sm text-muted-foreground">
              <span>{p.registrant || missing}</span>
              {p.registration_no && (
                <span className="inline-flex items-center gap-1">
                  <span aria-hidden>·</span>
                  SĐK <span className="font-mono text-foreground">{p.registration_no}</span>
                  <CopyButton
                    value={p.registration_no}
                    label="số đăng ký"
                    className="-my-1 size-6"
                  />
                </span>
              )}
            </p>
          </div>
          {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
        </div>

        <dl className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Fact label="Phân nhóm" empty={!p.pest_group} missing={missing}>
            {p.pest_group}
          </Fact>
          <Fact label="Lĩnh vực" empty={!p.sector} missing={missing}>
            {toSentenceCaseIfShouting(p.sector)}
          </Fact>
          {/*  Ngày HẾT HẠN là thứ người ta hỏi — đứng dòng chính; ngày cấp + thời gian còn lại xuống
               dòng phụ (bản «cấp → hết hạn» một dòng bị bẻ đôi ở dấu mũi tên trong ô hẹp). */}
          <Fact label="Hiệu lực đến" empty={!p.expires_on} missing={missing}>
            <span className="tabular-nums">{formatDate(p.expires_on)}</span>
            <span className="block text-xs font-normal text-muted-foreground">
              {p.registered_on && <>Cấp {formatDate(p.registered_on)}</>}
              {p.registered_on && remaining && ' · '}
              {remaining && (
                <span className={cn(remaining === 'Đã hết hạn' && 'font-medium text-destructive')}>
                  {remaining}
                </span>
              )}
            </span>
          </Fact>
          <Fact label="Nhóm độc" empty={toxicity.length === 0} missing={missing}>
            <span className="flex flex-wrap gap-1.5">
              {toxicity.map((item, index) => (
                <ToxicityChip key={index} item={item} />
              ))}
            </span>
          </Fact>
        </dl>
      </div>

      {(p.summary || p.resistance) && (
        <div className="space-y-2 border-t px-5 py-4 text-sm">
          {p.summary && (
            <p className="leading-relaxed text-muted-foreground">
              <span className="font-medium text-foreground">Tóm tắt sử dụng: </span>
              {p.summary}
            </p>
          )}
          {/*  Nhóm kháng thường trống ở nguồn — chỉ bày khi có, khỏi chiếm một ô «Nguồn không ghi». */}
          {p.resistance && (
            <p className="leading-relaxed text-muted-foreground">
              <span className="font-medium text-foreground">Quản lý tính kháng: </span>
              {p.resistance}
            </p>
          )}
        </div>
      )}
    </Card>
  )
}

function Fact({
  label,
  empty,
  missing,
  children,
}: {
  label: string
  empty: boolean
  missing: string
  children: ReactNode
}) {
  return (
    <div className="min-w-0 rounded-lg bg-muted/50 px-3 py-2.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          'mt-0.5 text-sm font-medium break-words',
          empty && 'font-normal text-muted-foreground italic',
        )}
      >
        {empty ? missing : children}
      </dd>
    </div>
  )
}

const TOXICITY_TONE: Record<ToxicitySeverity, string> = {
  high: 'border-destructive/30 bg-destructive/10 text-destructive',
  medium: 'border-warning/30 bg-warning/10 text-warning',
  low: 'border-success/30 bg-success/10 text-success',
  unknown: 'border-border bg-background text-muted-foreground',
}

/** Một nhóm độc: mã (GHS 5) đậm + nhãn mức độc, màu theo mức — chữ luôn đi kèm, màu không nói một mình. */
function ToxicityChip({ item }: { item: ToxicityItem }) {
  return (
    <span
      className={cn(
        'inline-flex items-baseline gap-1 rounded-md border px-1.5 py-0.5 text-xs',
        TOXICITY_TONE[item.severity],
      )}
    >
      {/*  Mã nhóm KHÔNG được bẻ dòng — «GHS» một dòng, «5» một dòng là đọc không ra. */}
      {item.code && <span className="font-semibold whitespace-nowrap">{item.code}</span>}
      {item.code && item.label && <span aria-hidden>·</span>}
      <span>{item.label}</span>
    </span>
  )
}
