import type { Employee } from '@/modules/hr/types/employee'
import { ConditionBuilder } from '@/shared/condition-builder/condition-builder'
import { Label } from '@/shared/ui/label'

import { conditionFieldsOf } from '../config/condition-fields'
import { useConditionChoices } from '../hooks/use-condition-choices'

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
 * Phần bộ chọn dùng chung nằm ở `shared/condition-builder/` (nâng lên ở
 * bao-CR-528 để màn Cấu hình hệ thống dùng lại); ở đây chỉ còn danh mục ô của
 * luồng duyệt và câu chữ riêng của bước.
 */
export function NodeConditionBuilder({
  value,
  onChange,
  entity,
  employees,
}: NodeConditionBuilderProps) {
  const fields = conditionFieldsOf(entity)
  const getOptions = useConditionChoices(employees, entity)

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

  return (
    <ConditionBuilder
      value={value}
      onChange={onChange}
      fields={fields}
      getOptions={getOptions}
      label="Bước này chỉ chạy khi"
      emptyText={
        <>
          Chưa đặt điều kiện — bước <b>luôn chạy</b>. Chỉ cần đặt khi một chặng có nhiều
          nhánh và mỗi nhánh dành cho một loại phiếu khác nhau.
        </>
      }
      sentencePrefix="Bước chỉ chạy khi "
      advancedText={
        <>
          Bước này đang dùng điều kiện <b>khai tay</b>, phức tạp hơn thứ bộ chọn diễn tả
          được. Giữ nguyên để không làm hỏng luồng đang chạy.
        </>
      }
    />
  )
}
