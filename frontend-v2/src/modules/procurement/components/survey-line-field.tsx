import { Circle, CircleCheck } from 'lucide-react'
import { useMemo } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatMoney, formatQuantity } from '@/shared/utils/format-money'
import type { SurveyCatalog } from '../helpers/survey-catalog'
import { isSupplierFromCatalog, rowAmount, toNumber } from '../helpers/survey-line'
import {
  SURVEY_APPROVE_OPTIONS,
  SURVEY_LAB_OPTIONS,
  type SurveyField,
  type SurveyLine,
} from '../types/survey-detail'
import { LabResultBadge, LineApproveBadge } from './document-status-badge'

/** Radix Select cấm value rỗng — dùng mã canh này cho lựa chọn "để trống". */
const EMPTY_CATALOG_VALUE = '__empty__'

/** Màu chữ của ô chọn kết luận LAB — xanh = đạt, đỏ = không đạt (CR-109). */
const LAB_TEXT_CLASS: Record<string, string> = {
  'Mẫu đạt': 'text-success',
  'Mẫu không đạt': 'text-destructive',
}

/**
 * Ô chữ CHỈ ĐỌC.
 *
 * CR-090: ô chỉ đọc cũng phải xuống dòng — cắt cụt là mất nội dung mà người xem
 * không biết là đang bị cắt. Giữ `title` để rê chuột vẫn đọc được cả câu.
 */
function ReadOnlyText({ value }: { value: string }) {
  return (
    <div className="whitespace-pre-wrap break-words leading-snug" title={value || undefined}>
      {value || <span className="text-muted-foreground">—</span>}
    </div>
  )
}

interface SurveyLineFieldProps {
  field: Pick<SurveyField, 'key' | 'label' | 'type' | 'options'>
  line: SurveyLine
  /** `cell` = trong bảng (gọn, chặn Enter), `form` = trong popup chi tiết dòng. */
  variant: 'cell' | 'form'
  /** Nội dung dòng có sửa được không (theo trạng thái phiếu + quyền). */
  editable: boolean
  /** Hai ô duyệt của TP/QL có sửa được không — quyền riêng, khác `editable`. */
  approveEditable: boolean
  /** Ô đang thiếu thông tin bắt buộc, tô đỏ sau khi bấm Gửi duyệt. */
  invalid?: boolean
  catalog: SurveyCatalog
  onChange: (changes: Partial<SurveyLine>) => void
}

/**
 * Một ô của dòng khảo sát, render theo `field.type`.
 *
 * Cùng một component phục vụ CẢ bảng lẫn popup chi tiết dòng: hai chỗ hiện cùng
 * một dữ liệu, tách ra hai bản là sớm muộn cũng lệch luật (bản v1 từng lệch ở ô
 * NCC — bảng cho gõ tay, popup thì không).
 */
export function SurveyLineField({
  field,
  line,
  variant,
  editable,
  approveEditable,
  invalid,
  catalog,
  onChange,
}: SurveyLineFieldProps) {
  const isCell = variant === 'cell'
  const type = field.type ?? 'text'
  const value = line[field.key]
  const text = String(value ?? '')

  const supplierOptions = useMemo(
    () =>
      catalog.suppliers.map((supplier) => ({
        value: supplier.code,
        label: `${supplier.code} — ${supplier.name}`,
      })),
    [catalog.suppliers],
  )

  const invalidClass = invalid && 'border-destructive ring-2 ring-destructive/20'

  /** Ô chữ tự giãn. Trong bảng thì Enter KHÔNG xuống dòng (CR-090) — nó là phím
   *  "xong ô" theo thói quen bảng tính, chèn xuống dòng là làm hỏng dữ liệu. */
  function textEditor(multiline: boolean) {
    return (
      <Textarea
        rows={1}
        value={text}
        placeholder={isCell ? undefined : field.label}
        onChange={(event) => onChange({ [field.key]: event.target.value })}
        onKeyDown={(event) => {
          if (isCell && event.key === 'Enter' && !event.shiftKey) event.preventDefault()
        }}
        className={cn(
          'w-full',
          isCell ? 'min-h-8 resize-none px-2 py-1 text-sm' : multiline ? 'min-h-20' : 'min-h-16',
          invalidClass,
        )}
      />
    )
  }

  switch (type) {
    /* ---- NCC sẵn có: công tắc đổi kiểu ô NCC, KHÔNG lưu xuống DB ---- */
    case 'check': {
      const checked =
        field.key === 'supplier_available'
          ? isSupplierFromCatalog(line, catalog.supplierCodes)
          : value === true
      if (!editable) return <ReadOnlyText value={checked ? 'Có' : 'Không'} />
      return (
        <div className={cn(isCell && 'flex justify-center')}>
          <Checkbox
            checked={checked}
            onCheckedChange={(next) => onChange({ [field.key]: next === true })}
          />
        </div>
      )
    }

    case 'date':
      if (!editable) return <ReadOnlyText value={text} />
      return (
        <DatePicker
          value={text}
          size={isCell ? 'sm' : 'default'}
          clearable
          onChange={(next) => onChange({ [field.key]: next })}
        />
      )

    case 'computed':
      // Thành tiền suy từ giá × MOQ × VAT, nhưng số đã lưu được ưu tiên.
      return <ReadOnlyText value={formatMoney(rowAmount(line))} />

    case 'num':
    case 'vat': {
      if (!editable) {
        return (
          <ReadOnlyText value={type === 'vat' ? `${text || 0}%` : formatQuantity(toNumber(value))} />
        )
      }
      return (
        <Input
          type="number"
          inputMode="decimal"
          min={0}
          max={type === 'vat' ? 99.99 : undefined}
          step={type === 'vat' ? 0.01 : 'any'}
          value={text}
          onChange={(event) => onChange({ [field.key]: event.target.value })}
          className={cn('w-full', isCell && 'h-8 px-2 text-right text-sm', invalidClass)}
        />
      )
    }

    /* ---- Duyệt dòng: quyền riêng, người khảo sát chỉ được xem ---- */
    case 'approve':
      if (!approveEditable) return <LineApproveBadge status={text} />
      return (
        <Select
          value={text || EMPTY_CATALOG_VALUE}
          onValueChange={(next) =>
            onChange({ [field.key]: next === EMPTY_CATALOG_VALUE ? '' : next })
          }
        >
          <SelectTrigger className={cn('w-full', isCell && 'h-8 text-sm')}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent position="popper" align="start">
            <SelectItem value={EMPTY_CATALOG_VALUE}>-- Chưa xét --</SelectItem>
            {SURVEY_APPROVE_OPTIONS.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )

    /* ---- Kết luận LAB: hai lựa chọn, để trống = chưa có kết quả (CR-109) ---- */
    case 'lab': {
      if (!editable) return <LabResultBadge result={text} />
      // Trong BẢNG thì dùng ô chọn: cột rộng 150px, hai cái nút không nằm vừa.
      if (isCell)
        return (
          <Select
            value={text || EMPTY_CATALOG_VALUE}
            onValueChange={(next) =>
              onChange({ [field.key]: next === EMPTY_CATALOG_VALUE ? '' : next })
            }
          >
            <SelectTrigger
              className={cn('h-8 w-full text-sm font-medium', LAB_TEXT_CLASS[text], invalidClass)}
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper" align="start">
              <SelectItem value={EMPTY_CATALOG_VALUE}>-- Chưa có KQ --</SelectItem>
              {SURVEY_LAB_OPTIONS.map((option) => (
                <SelectItem key={option} value={option} className={LAB_TEXT_CLASS[option]}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )
      // Trong POPUP thì hai nút bấm cho nhanh tay — bấm lại nút đang chọn để bỏ chọn.
      return (
        <div
          className={cn(
            'flex flex-wrap items-center gap-2',
            invalid && 'rounded-md p-1 ring-2 ring-destructive/20',
          )}
        >
          {SURVEY_LAB_OPTIONS.map((option) => {
            const on = text === option
            const pass = option === 'Mẫu đạt'
            return (
              <Button
                key={option}
                type="button"
                variant="outline"
                onClick={() => onChange({ [field.key]: on ? '' : option })}
                className={cn(
                  'font-semibold',
                  pass
                    ? 'border-success/50 text-success hover:text-success'
                    : 'border-destructive/50 text-destructive hover:text-destructive',
                  on && (pass ? 'bg-success/15 hover:bg-success/20' : 'bg-destructive/15 hover:bg-destructive/20'),
                )}
              >
                {on ? <CircleCheck className="size-4" /> : <Circle className="size-4" />}
                {option}
              </Button>
            )
          })}
        </div>
      )
    }

    case 'select': {
      if (!editable) return <ReadOnlyText value={text} />
      const options = field.options ?? []
      // Dữ liệu cũ có thể mang giá trị không còn trong danh sách — giữ lại làm
      // một lựa chọn, bỏ đi là mở phiếu ra ô trắng rồi lưu đè mất.
      const merged = options.includes(text) || !text ? [...options] : [text, ...options]
      return (
        <Select
          value={text || EMPTY_CATALOG_VALUE}
          onValueChange={(next) =>
            onChange({ [field.key]: next === EMPTY_CATALOG_VALUE ? '' : next })
          }
        >
          <SelectTrigger className={cn('w-full', isCell && 'h-8 text-sm')}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent position="popper" align="start">
            <SelectItem value={EMPTY_CATALOG_VALUE}>-- Chọn --</SelectItem>
            {merged.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
    }

    case 'unit':
      if (!editable) return <ReadOnlyText value={text} />
      return (
        <SearchSelect
          value={text}
          size={isCell ? 'sm' : 'default'}
          placeholder="-- ĐVT --"
          searchPlaceholder="Tìm đơn vị tính…"
          clearable
          options={catalog.units.map((unit) => ({ value: unit, label: unit }))}
          onChange={(next) => onChange({ [field.key]: next })}
          className={cn(invalidClass)}
        />
      )

    /* ---- Tên pháp lý ở bảng SẢN PHẨM: bảng dòng SP không có cột này trong DB,
       nên suy từ danh mục NCC và KHÓA lại. Xem CR-091. ---- */
    case 'legal': {
      const supplierCode = String(line.supplier_code ?? '').trim()
      const legalName = catalog.supplierByCode.get(supplierCode)?.name ?? ''
      return <ReadOnlyText value={legalName} />
    }

    /* ---- Ô NCC: chọn từ danh mục, hoặc gõ tay khi NCC chưa được tạo ---- */
    case 'supplier': {
      if (!editable) return <ReadOnlyText value={text} />
      if (!isSupplierFromCatalog(line, catalog.supplierCodes)) return textEditor(false)
      return (
        <SearchSelect
          value={text}
          wrap
          size={isCell ? 'sm' : 'default'}
          placeholder="Chọn/tìm NCC…"
          searchPlaceholder="Tìm theo mã hoặc tên NCC…"
          options={supplierOptions}
          className={cn(invalidClass)}
          onChange={(next) => {
            const supplier = catalog.supplierByCode.get(next)
            onChange(
              supplier
                ? {
                    supplier_code: supplier.code,
                    supplier_name: supplier.name,
                    tax_code: supplier.tax_code,
                    reg_address: supplier.address,
                  }
                : { supplier_code: next },
            )
          }}
        />
      )
    }

    case 'textarea':
      if (!editable) return <ReadOnlyText value={text} />
      return textEditor(true)

    default:
      if (!editable) return <ReadOnlyText value={text} />
      return textEditor(false)
  }
}
