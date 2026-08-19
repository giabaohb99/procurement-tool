import { AlertTriangle, Ban, Clock, ClipboardCheck, FileDown, FileText, Lock, RefreshCw } from 'lucide-react'
import { useState } from 'react'

import { downloadFile } from '@/core/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type {
  SurveyOptionAttachment,
  SurveyRequestResult,
  SurveyResultLine,
  SurveyResultOption,
} from '../types/survey-request-detail'
import { LINE_STATUS_RESURVEY } from '../types/survey-request-detail'
import { SurveyLineStateBadge } from './document-status-badge'

interface SurveyRequestResultCardProps {
  result: SurveyRequestResult
  /** Cho phép chọn / bỏ chọn phương án. */
  canChoose: boolean
  /** Người yêu cầu được gắn cờ "cần khảo sát lại". */
  canSetLineStatus: boolean
  /** Nhắc người dùng bấm "Tạo yêu cầu mua" khi chưa chọn phương án nào. */
  showCreatePrHint: boolean
  /** Đã tạo YCMH nhưng người đang xem không có quyền chuyển Hoàn thành. */
  showWaitFinalizeHint: boolean
  onChooseOption: (lineId: number, optionId: number) => void
  onRequestResurvey: (lineId: number) => void
}

/**
 * Khu "Kết quả khảo sát" — nơi người yêu cầu chọn phương án để sinh YCMH.
 *
 * NCC đã bị backend gỡ danh tính (whitelist `_OPT_PUBLIC_FIELDS`), chỉ còn số ẩn
 * danh `ncc_ref`. Đừng cố hiện tên NCC ở đây, dữ liệu không có mà cũng không được
 * phép: người yêu cầu chọn theo thông số và giá, không theo quan hệ với NCC.
 */
export function SurveyRequestResultCard({
  result,
  canChoose,
  canSetLineStatus,
  showCreatePrHint,
  showWaitFinalizeHint,
  onChooseOption,
  onRequestResurvey,
}: SurveyRequestResultCardProps) {
  const [previewUrl, setPreviewUrl] = useState('')
  const [ycmhOf, setYcmhOf] = useState<SurveyResultOption | null>(null)

  return (
    <Card className="gap-4 py-4">
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="flex items-center gap-2 text-base text-navy dark:text-foreground">
          <ClipboardCheck className="size-4 text-primary" />
          Kết quả khảo sát{canChoose ? ' — chọn phương án' : ''}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6 px-4">
        {canChoose && (
          <p className="text-xs text-muted-foreground">
            Với mỗi sản phẩm, nhấn chọn 1 phương án phù hợp nhất; bấm lại phương án đang chọn để
            BỎ CHỌN. Không bắt buộc chọn hết — dòng không chọn sẽ không tạo YCMH. Đổi/bỏ được cho
            tới khi dòng đã tạo YCMH. (Tên NCC ẩn theo chính sách; "NCC #" cùng số là cùng nhà
            cung cấp.)
          </p>
        )}

        {result.lines.map((line, index) => (
          <ResultLineBlock
            key={line.id}
            line={line}
            lineNumber={index + 1}
            canChoose={canChoose}
            canSetLineStatus={canSetLineStatus}
            onChooseOption={onChooseOption}
            onRequestResurvey={onRequestResurvey}
            onPreviewImage={setPreviewUrl}
            onOpenYcmh={setYcmhOf}
          />
        ))}

        {showCreatePrHint && (
          <p className="text-xs text-muted-foreground">
            Chọn phương án cho (những) sản phẩm muốn mua, rồi bấm <b>"Tạo yêu cầu mua"</b> ở góc
            phải trên. Có thể tạo YCMH nhiều lần (mua lại) kể cả khi phiếu đã Hoàn thành.
          </p>
        )}
        {showWaitFinalizeHint && (
          <p className="text-xs text-muted-foreground">
            Đã tạo YCMH — chờ Quản lý/Admin thu mua chuyển Hoàn thành.
          </p>
        )}
      </CardContent>

      <ImagePreviewDialog url={previewUrl} onClose={() => setPreviewUrl('')} />
      <YcmhListDialog option={ycmhOf} onClose={() => setYcmhOf(null)} />
    </Card>
  )
}

function ResultLineBlock({
  line,
  lineNumber,
  canChoose,
  canSetLineStatus,
  onChooseOption,
  onRequestResurvey,
  onPreviewImage,
  onOpenYcmh,
}: {
  line: SurveyResultLine
  lineNumber: number
  canChoose: boolean
  canSetLineStatus: boolean
  onChooseOption: (lineId: number, optionId: number) => void
  onRequestResurvey: (lineId: number) => void
  onPreviewImage: (url: string) => void
  onOpenYcmh: (option: SurveyResultOption) => void
}) {
  const options = line.options ?? []
  const flagged = line.line_status === LINE_STATUS_RESURVEY

  return (
    <section className="space-y-2.5">
      <h4 className="font-semibold">
        Sản phẩm {lineNumber}: {line.requirement_detail || line.item_group || '—'}
      </h4>

      <p className="text-xs text-muted-foreground">
        Phân loại: <b>{line.item_group || '—'}</b> · SL dự kiến:{' '}
        <b>{formatQuantity(line.request_qty) || '—'}</b> {line.uom} · Giá đề xuất của bạn:{' '}
        <b>{formatUnitPrice(line.proposed_price) || '—'}</b>
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground">Trạng thái dòng:</span>
        <SurveyLineStateBadge state={line.progress_state} tone={line.progress_tone} />

        {/* Cờ khảo sát lại chỉ gắn được, không gỡ tay: backend tự gỡ khi người YC
            chọn lại một phương án. Gỡ tay thì dòng về "đã chọn" trong khi NSTM
            chưa khảo sát lại gì cả. */}
        {canSetLineStatus &&
          options.length > 0 &&
          (flagged ? (
            <Button
              variant="ghost"
              size="sm"
              disabled
              title="Dòng đang cần khảo sát lại — chọn 1 phương án bên dưới để gỡ cờ"
            >
              <Lock />
              Cần khảo sát lại
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
              title="Đánh dấu dòng này cần khảo sát lại (sẽ bỏ chọn phương án đang chọn)"
              onClick={() => onRequestResurvey(line.id)}
            >
              <RefreshCw />
              Cần khảo sát lại
            </Button>
          ))}
      </div>

      {flagged && (
        <p className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <span>
            Dòng này đang yêu cầu <b>khảo sát lại</b> — chờ NSTM cập nhật phương án. Chọn 1 phương
            án bên dưới sẽ tự gỡ cờ.
          </span>
        </p>
      )}

      {options.length === 0 ? (
        line.no_option ? (
          <p className="flex items-start gap-2 rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            <Ban className="mt-0.5 size-4 shrink-0" />
            Không có phương án phù hợp (đã chốt rỗng) — sản phẩm này không mua được từ phiếu khảo
            sát.
          </p>
        ) : (
          <p className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/5 px-3 py-2 text-sm text-warning">
            <Clock className="mt-0.5 size-4 shrink-0" />
            Đang khảo sát — chưa có phương án. Sản phẩm này chưa mua được, chờ NSTM khảo sát xong.
          </p>
        )
      ) : (
        <div className="grid gap-3 xl:grid-cols-2">
          {options.map((option) => (
            <OptionCard
              key={option.id}
              option={option}
              canChoose={canChoose}
              onChoose={() => onChooseOption(line.id, option.id)}
              onPreviewImage={onPreviewImage}
              onOpenYcmh={onOpenYcmh}
            />
          ))}
        </div>
      )}
    </section>
  )
}

function OptionCard({
  option,
  canChoose,
  onChoose,
  onPreviewImage,
  onOpenYcmh,
}: {
  option: SurveyResultOption
  canChoose: boolean
  onChoose: () => void
  onPreviewImage: (url: string) => void
  onOpenYcmh: (option: SurveyResultOption) => void
}) {
  const label = option.display_label || `Option ${option.public_id}`

  return (
    // Cả thẻ là vùng bấm chọn (không chỉ ô radio): thẻ cao cả trăm pixel, bắt
    // người dùng nhắm đúng ô tròn 16px là tự chuốc lỗi bấm nhầm.
    <div
      role={canChoose ? 'radio' : undefined}
      aria-checked={canChoose ? option.is_chosen : undefined}
      tabIndex={canChoose ? 0 : undefined}
      className={cn(
        'rounded-xl border-2 p-3.5 transition-colors',
        option.is_chosen ? 'border-primary bg-primary/5' : 'border-border bg-card',
        canChoose ? 'cursor-pointer hover:border-primary/50' : 'cursor-default',
        !canChoose && !option.is_chosen && 'opacity-55',
      )}
      onClick={() => canChoose && onChoose()}
      onKeyDown={(event) => {
        if (canChoose && (event.key === 'Enter' || event.key === ' ')) {
          event.preventDefault()
          onChoose()
        }
      }}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 font-semibold">
          <input type="radio" checked={option.is_chosen} readOnly className="size-4" />
          {label}
        </span>

        <span
          className="inline-flex items-center gap-1.5"
          onClick={(event) => event.stopPropagation()}
        >
          {option.ycmh_count > 0 && (
            <Badge
              variant="secondary"
              className="cursor-pointer gap-1 border-0 bg-info/10 text-info"
              title="Xem các Yêu cầu mua hàng đã tạo từ phương án này"
              onClick={() => onOpenYcmh(option)}
            >
              <FileText className="size-3.5" />
              YCMH: {option.ycmh_count}
            </Badge>
          )}
          {option.is_chosen && (
            <Badge variant="secondary" className="border-0 bg-success/10 text-success">
              Đã chọn
            </Badge>
          )}
        </span>
      </div>

      <p className="mb-2 font-medium">{option.snap_product_name || '—'}</p>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs sm:grid-cols-3">
        <OptionField label="Mã VTBB" value={option.system_product_code} />
        <OptionField label="Ngày khảo sát" value={formatDate(option.survey_result_date)} />
        <OptionField
          label="Đơn giá"
          value={
            option.snap_price_by_volume ? `${formatUnitPrice(option.snap_price_by_volume)} đ` : ''
          }
          strong
        />
        <OptionField label="ĐVT báo giá" value={option.snap_quote_unit} />
        <OptionField label="MOQ" value={formatQuantity(option.snap_moq)} />
        <OptionField label="Khoảng SL áp giá" value={option.snap_volume_range} />
        <OptionField label="VAT" value={option.snap_vat ? `${option.snap_vat}%` : ''} />
        <OptionField label="Xuất xứ" value={option.snap_origin} />
        <OptionField label="Thời gian giao" value={option.snap_delivery_time} />
        <OptionField label="Địa điểm giao" value={option.snap_delivery_place} />
        {/* Không có phí ship KHÔNG phải là thiếu dữ liệu — là miễn phí. */}
        <OptionField
          label="Phí vận chuyển"
          value={
            option.snap_shipping_cost ? `${formatUnitPrice(option.snap_shipping_cost)} đ` : 'Miễn phí'
          }
        />
        <OptionField label="Có mẫu" value={option.snap_sample_ready ? 'Có' : 'Không'} />
        <OptionField label="Kết quả lab" value={option.snap_lab_result} />
      </dl>

      {!!option.snap_spec && (
        <p className="mt-2 border-t border-dashed pt-2 text-xs">
          <span className="text-muted-foreground">Thông số: </span>
          {option.snap_spec}
        </p>
      )}

      <div
        className="mt-2 border-t border-dashed pt-2 text-xs"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="mb-1.5 text-muted-foreground">Tài liệu đính kèm:</p>
        {option.attachments.length ? (
          <div className="flex flex-wrap items-center gap-2">
            {option.attachments.map((file) =>
              isImageAttachment(file) ? (
                <button
                  key={file.file_id}
                  type="button"
                  title={file.filename}
                  onClick={() => onPreviewImage(file.url)}
                >
                  <img
                    className="size-14 rounded-md border object-cover"
                    src={file.url}
                    alt={file.filename}
                  />
                </button>
              ) : (
                <Button
                  key={file.file_id}
                  variant="outline"
                  size="sm"
                  onClick={() => void downloadFile(file.url, file.filename)}
                >
                  <FileDown />
                  {file.filename}
                </Button>
              ),
            )}
          </div>
        ) : (
          <p className="italic text-muted-foreground">Không có file đính kèm</p>
        )}
      </div>
    </div>
  )
}

function OptionField({
  label,
  value,
  strong = false,
}: {
  label: string
  value: string
  strong?: boolean
}) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={cn('break-words', strong && 'font-semibold')}>{value || '—'}</dd>
    </div>
  )
}

function isImageAttachment(file: SurveyOptionAttachment) {
  return file.content_type.startsWith('image/') || /\.(jpe?g|png|webp|gif)$/i.test(file.filename)
}

function ImagePreviewDialog({ url, onClose }: { url: string; onClose: () => void }) {
  return (
    <Dialog open={!!url} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl">
        <DialogHeader className="sr-only">
          <DialogTitle>Xem ảnh đính kèm</DialogTitle>
        </DialogHeader>
        {!!url && <img className="max-h-[80dvh] w-full object-contain" src={url} alt="Đính kèm" />}
      </DialogContent>
    </Dialog>
  )
}

function YcmhListDialog({
  option,
  onClose,
}: {
  option: SurveyResultOption | null
  onClose: () => void
}) {
  return (
    <Dialog open={!!option} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Yêu cầu mua hàng đã tạo</DialogTitle>
          <DialogDescription>
            Từ phương án {option?.display_label || `Option ${option?.public_id ?? ''}`}.
          </DialogDescription>
        </DialogHeader>

        <ul className="space-y-2">
          {(option?.ycmh_list ?? []).map((pr) => (
            <li key={pr.id} className="flex items-center justify-between gap-3 rounded-lg border px-3 py-2">
              <span className="font-medium">{pr.code}</span>
              <span className="text-sm text-muted-foreground">
                {formatDate(pr.date)} · {pr.status}
              </span>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  )
}
