import { AlertTriangle, Plus, X } from 'lucide-react'
import { useState } from 'react'

import type { Employee } from '@/modules/hr/types/employee'
import { Button } from '@/shared/ui/button'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { conditionFieldsOf, type ConditionFieldDef } from '../config/condition-fields'
import { conditionText } from '../helpers/condition-sentence'
import { useConditionChoices } from '../hooks/use-condition-choices'
import {
  buildCondition,
  fullRow,
  laPhepNhieuGiaTri,
  OP_LABELS,
  parseCondition,
  toArray,
  type ConditionOp,
  type ConditionRow,
} from '../helpers/node-condition'

interface NodeConditionBuilderProps {
  /** Chuỗi điều kiện JSON đang lưu trên bước. */
  value: string
  onChange: (condition: string) => void
  /** Loại chứng từ của luồng — quyết định danh mục ô đem ra rẽ nhánh được. */
  entity: string
  employees: Employee[]
}

/**
 * «Bước này chỉ chạy khi …» — **thay cho ô gõ JSON**.
 *
 * Ô cũ bắt người khai luồng gõ tay
 * `[{"field":"secrecy_level","op":"gte","value":3}]`. Ba thứ hỏng cùng lúc: họ
 * phải biết tên cột trong CSDL, phải nhớ danh sách phép so sánh, và gõ sai thì
 * backend **nuốt lặng** (`condition_service.parse` trả rỗng khi JSON hỏng) nên
 * nhánh không bao giờ khớp mà màn hình không báo gì.
 *
 * Ở đây mỗi dòng là một câu chọn sẵn, và câu tiếng Việt dưới cùng nói lại đúng
 * thứ vừa khai để người dùng tự soát trước khi lưu.
 */
export function NodeConditionBuilder({
  value,
  onChange,
  entity,
  employees,
}: NodeConditionBuilderProps) {
  const fields = conditionFieldsOf(entity)
  const getOptions = useConditionChoices(employees)
  const { advanced } = parseCondition(value, (name) =>
    fields.some((field) => field.name === name),
  )

  //  Các dòng giữ ở state RIÊNG, không suy thẳng từ chuỗi đang lưu: một dòng
  //  vừa thêm hoặc vừa đổi ô thì chưa có giá trị, mà `buildCondition` cố ý bỏ
  //  những dòng chưa đủ ra khỏi chuỗi gửi backend. Suy ngược từ chuỗi thì dòng
  //  đang khai dở **biến mất ngay dưới tay người dùng**.
  //  Khởi tạo một lần là đủ: form khai bước mount lại theo `key` của từng bước.
  const [rows, setRows] = useState<ConditionRow[]>(
    () => parseCondition(value, (name) => fields.some((field) => field.name === name)).rows,
  )

  function ghi(rowsMoi: ConditionRow[]) {
    setRows(rowsMoi)
    onChange(buildCondition(rowsMoi))
  }

  function changeRow(index: number, thayDoi: Partial<ConditionRow>) {
    ghi(rows.map((row, i) => (i === index ? { ...row, ...thayDoi } : row)))
  }

  function addRow() {
    const field = fields[0]
    ghi([...rows, { field: field.name, op: field.ops[0], value: defaultValue(field.ops[0]) }])
  }

  //  Loại chứng từ chưa nối vào bộ máy duyệt (mới chỉ văn bản có
  //  `approval_bridge`) thì phiếu của nó CHƯA BAO GIỜ chạy qua đây — mọi điều
  //  kiện khai lúc này đều là chữ chết. Nói thẳng, không bày ô gõ JSON: bắt
  //  người dùng đoán tên cột rồi gõ ra một điều kiện không bao giờ được đọc là
  //  tệ hơn không cho khai.
  if (fields.length === 0) {
    return (
      <div className="space-y-2">
        <Label>Bước này chỉ chạy khi</Label>
        <p className="text-xs text-muted-foreground">
          Loại chứng từ này chưa nối vào bộ máy duyệt mới nên chưa đặt được điều kiện —
          bước <b>luôn chạy</b>. Cần rẽ nhánh thì tách thành hai luồng riêng.
        </p>
        {value && (
          //  Có điều kiện cũ thì phải thấy được và bỏ được, đừng giấu đi.
          <div className="space-y-1.5 rounded-md border border-amber-300 bg-amber-50 px-3 py-2">
            <p className="text-xs text-amber-900">Điều kiện đang lưu trên bước này:</p>
            <p className="font-mono text-xs break-all text-amber-900">{value}</p>
            <button
              type="button"
              className="text-xs underline underline-offset-2"
              onClick={() => onChange('')}
            >
              Bỏ điều kiện này
            </button>
          </div>
        )}
      </div>
    )
  }

  if (advanced) {
    //  Điều kiện khai tay từ trước KHÔNG được lặng lẽ ghi đè: người khai trước
    //  có thể đã viết đúng một điều kiện mà bộ dựng chưa diễn tả được.
    return (
      <div className="space-y-2">
        <Label>Bước này chỉ chạy khi</Label>
        <div className="space-y-1.5 rounded-md border border-amber-300 bg-amber-50 px-3 py-2">
          <p className="flex items-start gap-2 text-sm text-amber-900">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Bước này đang dùng điều kiện <b>khai tay</b>, phức tạp hơn thứ bộ chọn diễn
              tả được. Giữ nguyên để không làm hỏng luồng đang chạy.
            </span>
          </p>
          <p className="font-mono text-xs break-all text-amber-900">{value}</p>
          <button
            type="button"
            className="text-xs underline underline-offset-2"
            onClick={() => onChange('')}
          >
            Bỏ điều kiện này và chọn lại
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <Label>Bước này chỉ chạy khi</Label>

      {rows.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          Chưa đặt điều kiện — bước <b>luôn chạy</b>. Chỉ cần đặt khi một chặng có nhiều
          nhánh và mỗi nhánh dành cho một loại phiếu khác nhau.
        </p>
      ) : (
        <ul className="space-y-2">
          {rows.map((row, index) => (
            <li key={index} className="rounded-md border bg-card p-2">
              {/*  Nhắc "VÀ" giữa các dòng: backend nối mọi dòng bằng VÀ
                   (`condition_service.matches` dùng `all`). Không nói ra thì
                   người khai dễ tưởng các dòng là HOẶC và khai ra một điều kiện
                   không phiếu nào khớp. */}
              {index > 0 && (
                <p className="mb-1.5 text-xs font-medium text-muted-foreground">VÀ</p>
              )}

              <div className="flex items-center gap-2">
                <Select
                  value={row.field}
                  onValueChange={(name) => {
                    const field = fields.find((item) => item.name === name)
                    if (!field) return
                    //  Đổi ô thì phải reset phép và giá trị: "Mật" của ô mức mật
                    //  đọc thành id phòng ban ở ô sau là một điều kiện sai mà
                    //  trông vẫn hợp lệ.
                    changeRow(index, {
                      field: name,
                      op: field.ops[0],
                      value: defaultValue(field.ops[0]),
                    })
                  }}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {fields.map((field) => (
                      <SelectItem key={field.name} value={field.name}>
                        {field.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  title="Bỏ điều kiện này"
                  onClick={() => ghi(rows.filter((_, i) => i !== index))}
                >
                  <X />
                </Button>
              </div>

              <ValueRow
                row={row}
                field={fields.find((item) => item.name === row.field)}
                options={(() => {
                  const field = fields.find((item) => item.name === row.field)
                  return field ? getOptions(field) : []
                })()}
                onChange={(thayDoi) => changeRow(index, thayDoi)}
              />
            </li>
          ))}
        </ul>
      )}

      <Button type="button" variant="outline" size="sm" onClick={addRow}>
        <Plus className="size-4" />
        Thêm điều kiện
      </Button>

      {/*  Dòng khai dở KHÔNG được lưu — nói ra, đừng để người dùng bấm lưu rồi
           mở lại mới phát hiện mất một dòng. */}
      {rows.some((row) => !fullRow(row)) && (
        <p className="text-xs text-amber-700">
          Điều kiện chưa chọn giá trị sẽ không được lưu.
        </p>
      )}

      {rows.length > 0 && (
        //  Câu tổng kết: người khai đọc lại đúng thứ mình vừa chọn trước khi
        //  lưu. Bốn ô chọn rời rạc không tự nói ra chúng ghép thành nghĩa gì.
        <p className="rounded-md bg-muted/60 px-3 py-2 text-xs">
          <span className="text-muted-foreground">Bước chỉ chạy khi </span>
          <b>{conditionText(rows, fields, getOptions)}</b>
        </p>
      )}
    </div>
  )
}

interface ValueRowProps {
  row: ConditionRow
  field?: ConditionFieldDef
  options: { id: number; label: string; hint?: string }[]
  onChange: (thayDoi: Partial<ConditionRow>) => void
}

/** Phép so sánh + ô nhập giá trị của một dòng. */
function ValueRow({ row, field, options, onChange }: ValueRowProps) {
  if (!field) return null

  return (
    <div className="mt-2 flex items-center gap-2">
      <Select
        value={row.op}
        onValueChange={(op) =>
          onChange({ op: op as ConditionOp, value: defaultValue(op as ConditionOp) })
        }
      >
        <SelectTrigger className="w-40 shrink-0">
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

      <div className="min-w-0 flex-1">
        {laPhepNhieuGiaTri(row.op) ? (
          <MultiPicker
            value={toArray(row.value)}
            onChange={(ids) => onChange({ value: ids })}
            options={options}
            placeholder="Chọn giá trị…"
          />
        ) : (
          <Select
            value={String(row.value || '')}
            onValueChange={(value) => onChange({ value: Number(value) })}
          >
            <SelectTrigger className="w-full">
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
        )}
      </div>
    </div>
  )
}

function defaultValue(op: ConditionOp): number | number[] {
  return laPhepNhieuGiaTri(op) ? [] : 0
}

