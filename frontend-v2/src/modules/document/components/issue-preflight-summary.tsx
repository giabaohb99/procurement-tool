import { AlertTriangle, ArrowRight, Ban, CalendarClock, FileCheck, Hash } from 'lucide-react'

import { formatDate } from '@/shared/utils/format-date'
import type { DocumentIssuePreview } from '../types/document-link'

interface IssuePreflightSummaryProps {
  preview: DocumentIssuePreview
}

/**
 * BỐN THỨ SẮP XẢY RA khi bấm Ban hành (J04).
 *
 * Ban hành không lùi được — số hiệu cấp ra là cấp vĩnh viễn, phiên bản khóa là
 * khóa một chiều, văn bản cũ bị thay thế thì đổi trạng thái ngay. Nên trước khi
 * bấm phải nhìn thấy đủ: số nào sẽ cấp, bản nào bị khóa và áp dụng từ bao giờ,
 * văn bản nào chết theo, và văn bản này tới được ai.
 *
 * **Chặn** và **cảnh báo** để tách bạch: gộp chung thì người dùng học được thói
 * quen bỏ qua tất.
 */
export function IssuePreflightSummary({ preview }: IssuePreflightSummaryProps) {
  return (
    <div className="space-y-3">
      <dl className="grid gap-x-4 gap-y-2 rounded-md border bg-muted/30 px-4 py-3 text-sm sm:grid-cols-2">
        <Row icon={Hash} label="Số hiệu sẽ cấp">
          {preview.issue_number_preview ? (
            <span className="font-mono font-medium">{preview.issue_number_preview}</span>
          ) : (
            <span className="text-muted-foreground">Không cấp số lúc ban hành</span>
          )}
        </Row>

        <Row icon={FileCheck} label="Phiên bản sẽ khóa">
          {preview.version_no ? `Bản ${preview.version_no}` : '—'}
        </Row>

        <Row icon={CalendarClock} label="Hiệu lực từ">
          {preview.effective_date ? formatDate(preview.effective_date) : 'Ngay khi ban hành'}
          {!preview.effective_now && (
            <span className="ml-2 text-muted-foreground">— chưa áp dụng ngay</span>
          )}
        </Row>

        <Row icon={ArrowRight} label="Phạm vi áp dụng">
          {/*  Không khai dòng nào KHÔNG còn là lỗi: văn bản áp trong đúng pháp
               nhân ban hành (quy tắc 3, `scope_service.py`). */}
          {preview.scope_count > 0
            ? `${preview.scope_count} dòng`
            : 'Mặc định — toàn bộ pháp nhân ban hành'}
        </Row>
      </dl>

      {/*  Hậu quả nặng nhất và không lùi được: văn bản khác chết theo. */}
      {preview.will_supersede.length > 0 && (
        <div className="rounded-md border px-4 py-3 text-sm">
          <p className="mb-2 flex items-center gap-2 font-medium">
            <Ban className="size-4 text-muted-foreground" />
            Ban hành xong thì {preview.will_supersede.length} văn bản đổi trạng thái
          </p>
          <ul className="space-y-1">
            {preview.will_supersede.map((item) => (
              <li key={item.document_id} className="flex flex-wrap items-center gap-2">
                <span className="font-medium">
                  {item.display_code ? `${item.display_code} · ` : ''}
                  {item.title}
                </span>
                <span className="text-xs text-muted-foreground">
                  {item.current_status_label}
                </span>
                <ArrowRight className="size-3.5 text-muted-foreground" />
                <span className="text-xs font-medium">{item.next_status_label}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {preview.blockers.length > 0 && (
        <Notice tone="block" title="Chưa ban hành được:" items={preview.blockers} />
      )}

      {preview.warnings.length > 0 && (
        <Notice tone="warn" title="Nên xem lại trước khi ban hành:" items={preview.warnings} />
      )}
    </div>
  )
}

function Row({
  icon: Icon,
  label,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0">
        <dt className="text-xs text-muted-foreground">{label}</dt>
        <dd>{children}</dd>
      </div>
    </div>
  )
}

function Notice({
  tone,
  title,
  items,
}: {
  tone: 'block' | 'warn'
  title: string
  items: string[]
}) {
  const isBlock = tone === 'block'
  return (
    <div
      className={
        isBlock
          ? 'flex gap-3 rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3'
          : 'flex gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3'
      }
    >
      <AlertTriangle
        className={
          isBlock
            ? 'mt-0.5 size-4 shrink-0 text-destructive'
            : 'mt-0.5 size-4 shrink-0 text-amber-700'
        }
      />
      <div className={isBlock ? 'text-sm text-destructive' : 'text-sm text-amber-900'}>
        <p className="font-medium">{title}</p>
        <ul className="mt-1 list-inside list-disc">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
