import { AlertTriangle, Plus, X } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'

import {
  buildCondition,
  defaultConditionValue,
  fullRow,
  isMultiValueOp,
  isValueFreeOp,
  OP_LABELS,
  parseCondition,
  toArray,
  type ConditionChoice,
  type ConditionField,
  type ConditionOp,
  type ConditionRow,
} from './condition-rule'
import { conditionText } from './condition-sentence'

interface ConditionBuilderProps<F extends ConditionField> {
  /** Chuỗi điều kiện JSON đang lưu. */
  value: string
  onChange: (condition: string) => void
  /** Danh mục ô đem ra so được của ngữ cảnh này. Phải có ít nhất một ô. */
  fields: F[]
  /** Lựa chọn của từng ô danh mục (ô số / ô có-không không cần). */
  getOptions: (field: F) => ConditionChoice[]
  /** Nhãn đầu khối; bỏ trống khi nơi gọi tự dựng nhãn phía trên. */
  label?: ReactNode
  /** Câu hiện khi chưa có dòng nào — nói rõ «không điều kiện» nghĩa là gì ở đây. */
  emptyText: ReactNode
  /** Tiền tố câu tổng kết, ví dụ «Bước chỉ chạy khi ». */
  sentencePrefix: string
  /** Câu giải thích khi chuỗi đang lưu vượt ngoài thứ bộ chọn diễn tả được. */
  advancedText: ReactNode
  disabled?: boolean
}

/**
 * BỘ CHỌN ĐIỀU KIỆN — mỗi dòng «trường · phép so · giá trị» chọn sẵn, **thay
 * cho ô gõ JSON**, kèm một câu tiếng Việt nói lại đúng thứ vừa khai để người
 * dùng tự soát trước khi lưu.
 *
 * Nâng từ bộ dựng điều kiện của luồng duyệt (`modules/approval`) ở bao-CR-528
 * để màn Cấu hình hệ thống dùng chung. Phần riêng của từng nơi (danh mục ô,
 * nguồn lựa chọn, câu chữ) do nơi gọi truyền vào.
 */
export function ConditionBuilder<F extends ConditionField>({
  value,
  onChange,
  fields,
  getOptions,
  label,
  emptyText,
  sentencePrefix,
  advancedText,
  disabled = false,
}: ConditionBuilderProps<F>) {
  const { advanced } = parseCondition(value, fields)

  //  Các dòng giữ ở state RIÊNG, không suy thẳng từ chuỗi đang lưu: một dòng
  //  vừa thêm hoặc vừa đổi ô thì chưa có giá trị, mà `buildCondition` cố ý bỏ
  //  những dòng chưa đủ ra khỏi chuỗi gửi backend. Suy ngược từ chuỗi thì dòng
  //  đang khai dở **biến mất ngay dưới tay người dùng**.
  const [rows, setRows] = useState<ConditionRow[]>(() => parseCondition(value, fields).rows)

  function write(nextRows: ConditionRow[]) {
    setRows(nextRows)
    onChange(buildCondition(nextRows, fields))
  }

  function changeRow(index: number, patch: Partial<ConditionRow>) {
    write(rows.map((row, i) => (i === index ? { ...row, ...patch } : row)))
  }

  function addRow() {
    const field = fields[0]
    write([
      ...rows,
      { field: field.name, op: field.ops[0], value: defaultConditionValue(field.ops[0], field.kind) },
    ])
  }

  if (advanced) {
    //  Điều kiện khai tay từ trước KHÔNG được lặng lẽ ghi đè: người khai trước
    //  có thể đã viết đúng một điều kiện mà bộ chọn chưa diễn tả được.
    return (
      <div className="space-y-2">
        {label && <Label>{label}</Label>}
        <div className="space-y-1.5 rounded-md border border-amber-300 bg-amber-50 px-3 py-2">
          <p className="flex items-start gap-2 text-sm text-amber-900">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>{advancedText}</span>
          </p>
          <p className="font-mono text-xs break-all text-amber-900">{value}</p>
          {!disabled && (
            <button
              type="button"
              className="text-xs underline underline-offset-2"
              onClick={() => {
                setRows([])
                onChange('')
              }}
            >
              Bỏ điều kiện này và chọn lại
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {label && <Label>{label}</Label>}

      {rows.length === 0 ? (
        <p className="text-xs text-muted-foreground">{emptyText}</p>
      ) : (
        <ul className="space-y-2">
          {rows.map((row, index) => {
            const field = fields.find((item) => item.name === row.field)
            return (
              <li key={index} className="rounded-md border bg-card p-2">
                {/*  Nhắc "VÀ" giữa các dòng: backend nối mọi dòng bằng VÀ
                     (`condition_service.matches` dùng `all`). Không nói ra thì
                     người khai dễ tưởng các dòng là HOẶC và khai ra một điều
                     kiện không phiếu nào khớp. */}
                {index > 0 && (
                  <p className="mb-1.5 text-xs font-medium text-muted-foreground">VÀ</p>
                )}

                <div className="flex items-center gap-2">
                  <Select
                    value={row.field}
                    disabled={disabled}
                    onValueChange={(name) => {
                      const next = fields.find((item) => item.name === name)
                      if (!next) return
                      //  Đổi ô thì phải reset phép và giá trị: "Mật" của ô mức mật
                      //  đọc thành id phòng ban ở ô sau là một điều kiện sai mà
                      //  trông vẫn hợp lệ.
                      changeRow(index, {
                        field: name,
                        op: next.ops[0],
                        value: defaultConditionValue(next.ops[0], next.kind),
                      })
                    }}
                  >
                    <SelectTrigger className="flex-1" aria-label="Trường so">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {fields.map((item) => (
                        <SelectItem key={item.name} value={item.name}>
                          {item.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {!disabled && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      title="Bỏ điều kiện này"
                      aria-label="Bỏ điều kiện này"
                      onClick={() => write(rows.filter((_, i) => i !== index))}
                    >
                      <X />
                    </Button>
                  )}
                </div>

                {field && (
                  <ValueRow
                    row={row}
                    field={field}
                    options={field.kind === 'number' || field.kind === 'bool' ? [] : getOptions(field)}
                    disabled={disabled}
                    onChange={(patch) => changeRow(index, patch)}
                  />
                )}
              </li>
            )
          })}
        </ul>
      )}

      {!disabled && (
        <Button type="button" variant="outline" size="sm" onClick={addRow}>
          <Plus className="size-4" />
          Thêm điều kiện
        </Button>
      )}

      {/*  Dòng khai dở KHÔNG được lưu — nói ra, đừng để người dùng bấm lưu rồi
           mở lại mới phát hiện mất một dòng. */}
      {rows.some((row) => !fullRow(row, fields.find((item) => item.name === row.field)?.kind)) && (
        <p className="text-xs text-amber-700">Điều kiện chưa chọn giá trị sẽ không được lưu.</p>
      )}

      {rows.length > 0 && (
        //  Câu tổng kết: người khai đọc lại đúng thứ mình vừa chọn trước khi
        //  lưu. Bốn ô chọn rời rạc không tự nói ra chúng ghép thành nghĩa gì.
        <p className="rounded-md bg-muted/60 px-3 py-2 text-xs">
          <span className="text-muted-foreground">{sentencePrefix}</span>
          <b>{conditionText(rows, fields, getOptions)}</b>
        </p>
      )}
    </div>
  )
}

interface ValueRowProps {
  row: ConditionRow
  field: ConditionField
  options: ConditionChoice[]
  disabled: boolean
  onChange: (patch: Partial<ConditionRow>) => void
}

/** Phép so sánh + ô nhập giá trị của một dòng. */
function ValueRow({ row, field, options, disabled, onChange }: ValueRowProps) {
  return (
    <div className="mt-2 flex items-center gap-2">
      <Select
        value={row.op}
        disabled={disabled}
        onValueChange={(op) =>
          onChange({
            op: op as ConditionOp,
            value: defaultConditionValue(op as ConditionOp, field.kind),
          })
        }
      >
        <SelectTrigger
          className={cn(isValueFreeOp(row.op) && 'flex-1', !isValueFreeOp(row.op) && 'w-40 shrink-0')}
          aria-label="Phép so"
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {field.ops.map((op) => (
            <SelectItem key={op} value={op}>
              {OP_LABELS[op]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {!isValueFreeOp(row.op) && (
        <div className="min-w-0 flex-1">
          <ValueInput
            row={row}
            field={field}
            options={options}
            disabled={disabled}
            onChange={onChange}
          />
        </div>
      )}
    </div>
  )
}

function ValueInput({ row, field, options, disabled, onChange }: ValueRowProps) {
  if (isMultiValueOp(row.op)) {
    return (
      <MultiPicker
        value={toArray(row.value)}
        onChange={(ids) => onChange({ value: ids })}
        options={options}
        placeholder="Chọn giá trị…"
        disabled={disabled}
      />
    )
  }

  if (field.kind === 'bool') {
    return (
      <Select
        value={row.value === false ? 'false' : 'true'}
        disabled={disabled}
        onValueChange={(next) => onChange({ value: next === 'true' })}
      >
        <SelectTrigger className="w-full" aria-label="Giá trị">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="true">Có</SelectItem>
          <SelectItem value="false">Không</SelectItem>
        </SelectContent>
      </Select>
    )
  }

  if (field.kind === 'number') {
    return (
      <Input
        type="number"
        min={0}
        aria-label="Giá trị"
        placeholder="Nhập số…"
        disabled={disabled}
        value={typeof row.value === 'number' ? row.value : ''}
        onChange={(event) =>
          //  Ô trống là «chưa nhập» (`null`), KHÔNG phải `0`: `Number('')` ra 0,
          //  và «số dòng từ 0 trở xuống» là một điều kiện thật, khác hẳn nghĩa.
          onChange({ value: event.target.value === '' ? null : Number(event.target.value) })
        }
      />
    )
  }

  return (
    <Select
      value={String(row.value || '')}
      disabled={disabled}
      onValueChange={(next) => onChange({ value: Number(next) })}
    >
      <SelectTrigger className="w-full" aria-label="Giá trị">
        <SelectValue placeholder="Chọn mức…" />
      </SelectTrigger>
      <SelectContent>
        {options.map((item) => (
          <SelectItem key={item.id} value={String(item.id)}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
