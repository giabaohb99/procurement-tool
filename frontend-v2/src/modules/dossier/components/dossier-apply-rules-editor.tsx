import { Info, Plus, Trash2 } from 'lucide-react'
import { useController, type Control } from 'react-hook-form'

import type { CrudRecord } from '@/shared/crud'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { CollapsibleSection } from '@/shared/ui/collapsible-section'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import {
  APPLY_FIELDS,
  APPLY_FIELD_LABEL,
  APPLY_OPS,
  APPLY_OP_LABEL,
  DOC_KIND_LABEL,
  DOC_KIND_ORDER,
  DOC_KIND_WARNING,
  MAX_APPLY_CONDITIONS,
  conditionValueToText,
  isMultiValueOp,
  textToConditionValue,
  type ApplyCondition,
  type ApplyField,
  type ApplyOp,
  type DocKind,
} from '../types/dossier-applicability'
import {
  EMPTY_APPLY_RULES,
  type DossierApplyRules,
} from '../types/dossier-apply-rules'

interface DossierApplyRulesEditorProps {
  control: Control<CrudRecord>
  name: string
  disabled?: boolean
}

/** Dòng điều kiện mới — mặc định chiều dễ đúng nhất. */
function emptyCondition(): ApplyCondition {
  return { field: APPLY_FIELDS.PRODUCT_CODE, op: APPLY_OPS.EQ, value: '' }
}

/**
 * Câu TÓM TẮT hiện khi khối đang gập.
 *
 * ⚠️ Phải phân biệt được **hai ca rỗng có nghĩa ngược nhau**, vì gập lại thì
 * đây là thứ DUY NHẤT người dùng đọc được về cả khối:
 *   * chưa chọn màn nào → «chưa áp dụng ở đâu»;
 *   * có màn mà không điều kiện → «mọi phiếu», tức đang áp cho TẤT CẢ.
 * Gộp hai ca thành một câu chung là giấu mất cái thứ hai — thứ đang bật cho cả
 * công ty mà người ta tưởng mình chưa khai gì.
 */
function summaryText(docKinds: DocKind[], conditionCount: number): string {
  if (docKinds.length === 0) return 'chưa áp dụng ở đâu'
  const where = docKinds.map((kind) => DOC_KIND_LABEL[kind]).join(' · ')
  return conditionCount === 0
    ? `${where} · mọi phiếu`
    : `${where} · ${conditionCount} điều kiện`
}

/**
 * ĐIỀU KIỆN ÁP DỤNG — *«giấy này phải kèm theo chứng từ nào»*.
 *
 * Hai tầng, và **tầng trên quyết định tầng dưới có nghĩa hay không**: chọn màn
 * trước, rồi mới khai dòng hàng phải thỏa gì.
 *
 * ⚠️ **HAI CA RỖNG, HAI NGHĨA NGƯỢC NHAU** — cả hai im lặng, nên cả hai phải
 * được NÓI THÀNH CÂU trên màn hình chứ không để người dùng suy ra từ một bảng
 * trống:
 *   * chưa chọn màn nào → hồ sơ không hiện ra ở đâu (mặc định, đúng hành vi cũ);
 *   * đã chọn màn, không khai điều kiện → áp cho **MỌI** phiếu loại đó.
 *
 * ⚠️ Nối thẳng vào form của khung CRUD bằng `useController`, không giữ state
 * riêng — cùng lý lẽ `DossierCustomFieldsEditor`: màn THÊM MỚI chưa có bản ghi
 * nên không tách khối lưu riêng được, và hai nguồn sự thật cho một ô sẽ lệch
 * nhau ở đúng lần `reset` không ai ngờ.
 */
export function DossierApplyRulesEditor({
  control,
  name,
  disabled,
}: DossierApplyRulesEditorProps) {
  const { field } = useController({ control, name })
  const rules: DossierApplyRules =
    field.value && typeof field.value === 'object'
      ? (field.value as DossierApplyRules)
      : EMPTY_APPLY_RULES

  const docKinds = rules.docKinds ?? []
  const conditions = rules.conditions ?? []
  const set = (patch: Partial<DossierApplyRules>) =>
    field.onChange({ docKinds, conditions, ...patch })

  const toggleKind = (kind: DocKind, checked: boolean) =>
    set({
      docKinds: checked ? [...docKinds, kind] : docKinds.filter((k) => k !== kind),
    })

  //  ⚠️ Đổi CHIỀU hay đổi PHÉP thì nắn lại giá trị. Không nắn thì chuyển từ
  //  «thuộc» (giá trị là MẢNG) sang «là» (giá trị là CHUỖI) làm ô nhập nhận một
  //  mảng và React hiện `SP-001,SP-002` như một mã sản phẩm duy nhất — lưu
  //  xuống là một mã không tồn tại, im lặng.
  const setCondition = (index: number, patch: Partial<ApplyCondition>) => {
    const next = conditions.map((row, i) => {
      if (i !== index) return row
      const merged = { ...row, ...patch }
      if (patch.op && isMultiValueOp(patch.op) !== isMultiValueOp(row.op)) {
        merged.value = textToConditionValue(conditionValueToText(row.value), patch.op)
      }
      return merged
    })
    set({ conditions: next })
  }

  const warnings = docKinds
    .map((kind) => DOC_KIND_WARNING[kind])
    .filter((text): text is string => Boolean(text))

  //  Tóm tắt lúc gập phải nói được HAI ca rỗng khác nhau — xem `summaryText`.
  const summary = summaryText(docKinds, conditions.length)

  return (
    <CollapsibleSection
      title="Điều kiện áp dụng"
      description="Chứng từ nào có dòng hàng khớp thì trang chi tiết của nó hiện ra hồ sơ này. Bỏ trống = hồ sơ chỉ nằm trong kho, không hiện ở đâu cả."
      summary={summary}
      storageKey="dossier.apply-rules"
      //  ⚠️ Chưa khai gì thì GẬP SẴN, và đó là tình trạng của gần như mọi hồ sơ
      //  đang có. Mở sẵn một khối rỗng ở mọi tờ hồ sơ là bắt tất cả cuộn qua
      //  một thứ hầu hết không dùng, chỉ để phục vụ số ít có dùng.
      defaultOpen={docKinds.length > 0}
    >
      <div className="space-y-3 px-3 py-3 sm:px-4">
        <div className="space-y-2">
          <Label className="text-xs font-medium text-muted-foreground">
            Hiện ở màn
          </Label>
          <div className="grid gap-2 @lg:grid-cols-2">
            {DOC_KIND_ORDER.map((kind) => (
              <label
                key={kind}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-md border px-2.5 py-2 text-sm',
                  docKinds.includes(kind) && 'border-primary/40 bg-primary/5',
                  disabled && 'cursor-not-allowed opacity-60',
                )}
              >
                <Checkbox
                  checked={docKinds.includes(kind)}
                  disabled={disabled}
                  onCheckedChange={(v) => toggleKind(kind, v === true)}
                />
                {DOC_KIND_LABEL[kind]}
              </label>
            ))}
          </div>
        </div>

        {/*  Cảnh báo riêng của màn vừa chọn — xem `DOC_KIND_WARNING`. Không nói
             ra thì người khai gắn điều kiện theo sản phẩm cho YCBG, thấy nó
             không bao giờ khớp, rồi đi tìm lỗi ở một chỗ không có lỗi nào. */}
        {warnings.map((text) => (
          <p
            key={text}
            className="flex gap-2 rounded-md border border-amber-400/40 bg-amber-50 px-2.5 py-2 text-xs text-amber-900 dark:bg-amber-950/30 dark:text-amber-200"
          >
            <Info className="mt-px size-3.5 shrink-0" />
            <span>{text}</span>
          </p>
        ))}

        {/*  Chưa chọn màn nào thì bảng điều kiện KHÔNG dựng: nó chưa có nghĩa
             gì, và một bảng bấm được nhưng không chạy là lời hứa suông. */}
        {docKinds.length > 0 && (
          <div className="space-y-2 border-t pt-3">
            <Label className="text-xs font-medium text-muted-foreground">
              Khi dòng hàng thỏa
            </Label>

            {conditions.length === 0 ? (
              //  ⚠️ Câu này là chốt chặn hiểu nhầm nguy hiểm nhất của cả tính
              //  năng. Bảng trống trông như «chưa khai gì» trong khi nghĩa thật
              //  của nó là «áp cho TẤT CẢ».
              <p className="rounded-md border border-dashed px-3 py-3 text-center text-sm text-muted-foreground">
                Chưa có điều kiện nào — hồ sơ sẽ hiện ở{' '}
                <strong className="text-foreground">mọi</strong>{' '}
                {docKinds.map((k) => DOC_KIND_LABEL[k].toLowerCase()).join(' · ')}.
              </p>
            ) : (
              <div className="space-y-2 @2xl:space-y-0">
                <div className="hidden gap-2 border-b border-border/60 pb-1.5 text-xs font-medium text-muted-foreground @2xl:grid @2xl:grid-cols-[minmax(0,1fr)_150px_minmax(0,1.4fr)_36px]">
                  <span>Chiều</span>
                  <span>So sánh</span>
                  <span>Giá trị</span>
                  <span />
                </div>

                {conditions.map((row, index) => (
                  <ConditionRow
                    key={index}
                    row={row}
                    index={index}
                    disabled={disabled}
                    onChange={(patch) => setCondition(index, patch)}
                    onRemove={() =>
                      set({ conditions: conditions.filter((_, i) => i !== index) })
                    }
                  />
                ))}
              </div>
            )}

            {!disabled && (
              <div className="flex flex-wrap items-center gap-3 pt-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={conditions.length >= MAX_APPLY_CONDITIONS}
                  onClick={() => set({ conditions: [...conditions, emptyCondition()] })}
                >
                  <Plus />
                  Thêm điều kiện
                </Button>
                <span className="text-xs text-muted-foreground">
                  {conditions.length}/{MAX_APPLY_CONDITIONS} điều kiện
                  {conditions.length > 1 && ' · các dòng nối nhau bằng VÀ'}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </CollapsibleSection>
  )
}

interface ConditionRowProps {
  row: ApplyCondition
  index: number
  disabled?: boolean
  onChange: (patch: Partial<ApplyCondition>) => void
  onRemove: () => void
}

/** MỘT dòng điều kiện: **chiều · phép so sánh · giá trị**. */
function ConditionRow({ row, index, disabled, onChange, onRemove }: ConditionRowProps) {
  const multi = isMultiValueOp(row.op)

  return (
    <div className="grid gap-2 rounded-lg border bg-card p-2.5 @2xl:grid-cols-[minmax(0,1fr)_150px_minmax(0,1.4fr)_36px] @2xl:items-start @2xl:gap-x-2 @2xl:rounded-none @2xl:border-x-0 @2xl:border-t-0 @2xl:border-b @2xl:border-border/60 @2xl:bg-transparent @2xl:px-0 @2xl:py-2">
      <div className="space-y-1">
        <Label htmlFor={`ac-field-${index}`} className="text-xs @2xl:sr-only">
          Chiều
        </Label>
        <Select
          value={row.field}
          disabled={disabled}
          onValueChange={(v) => onChange({ field: v as ApplyField })}
        >
          <SelectTrigger id={`ac-field-${index}`} className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(APPLY_FIELD_LABEL).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1">
        <Label htmlFor={`ac-op-${index}`} className="text-xs @2xl:sr-only">
          So sánh
        </Label>
        <Select
          value={row.op}
          disabled={disabled}
          onValueChange={(v) => onChange({ op: v as ApplyOp })}
        >
          <SelectTrigger id={`ac-op-${index}`} className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(APPLY_OP_LABEL).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1">
        <Label htmlFor={`ac-val-${index}`} className="text-xs @2xl:sr-only">
          Giá trị
        </Label>
        <Input
          id={`ac-val-${index}`}
          value={conditionValueToText(row.value)}
          disabled={disabled}
          //  Chữ gợi ý đổi theo phép so sánh — nó là chỗ DUY NHẤT nói ra rằng
          //  «thuộc» nhận nhiều giá trị ngăn bằng dấu phẩy.
          placeholder={multi ? 'SP-001, SP-002, SP-003' : 'SP-001'}
          onChange={(e) => onChange({ value: textToConditionValue(e.target.value, row.op) })}
        />
      </div>

      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-9 shrink-0 justify-self-end text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        aria-label={`Xóa điều kiện ${index + 1}`}
        disabled={disabled}
        onClick={onRemove}
      >
        <Trash2 className="size-4" />
      </Button>
    </div>
  )
}
