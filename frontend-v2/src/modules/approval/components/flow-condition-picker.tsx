import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { ConditionBuilder } from '@/shared/condition-builder/condition-builder'
import { Label } from '@/shared/ui/label'
import { conditionFieldsOf } from '../config/condition-fields'
import { useConditionChoices } from '../hooks/use-condition-choices'

interface FlowConditionPickerProps {
  /** Chuỗi điều kiện đang lưu trên luồng. */
  condition: string
  onChange: (condition: string) => void
  /** Loại chứng từ của luồng — quyết định danh mục ô đặt điều kiện được. */
  entity: string
}

/**
 * «Luồng này áp cho phiếu nào» của các loại chứng từ KHÁC văn bản (bao-CR-579).
 *
 * Văn bản có bộ chọn riêng ba lựa chọn (`FlowScopePicker`). Đặt xe và Duyệt dấu
 * cần thứ khác: khai NHIỀU luồng cho cùng một loại phiếu, mỗi luồng một điều kiện
 * (giao hàng thì thêm Giám đốc, một phòng ban có luồng riêng…). Luồng có điều
 * kiện được xét trước theo độ ưu tiên, luồng không đặt điều kiện là mặc định và
 * đứng cuối hàng — xem `flow_service.pick_flow`.
 *
 * Loại chứng từ chưa khai ô nào thì nói thẳng là luồng áp cho mọi phiếu.
 */
export function FlowConditionPicker({ condition, onChange, entity }: FlowConditionPickerProps) {
  const fields = conditionFieldsOf(entity)
  const needsEmployees = fields.some((field) => field.source === 'employee')
  const { data: employeePage } = useEmployees(
    { page_size: 1000, is_active: true },
    { enabled: needsEmployees },
  )
  const getOptions = useConditionChoices(employeePage?.items ?? [], entity)

  if (fields.length === 0) {
    return (
      <div className="space-y-2">
        <Label>Áp cho phiếu nào</Label>
        <p className="text-sm text-muted-foreground">
          Loại chứng từ này chưa có ô nào để đặt điều kiện — luồng áp cho <b>mọi phiếu</b>{' '}
          của loại đó.
        </p>
      </div>
    )
  }

  return (
    <ConditionBuilder
      value={condition}
      onChange={onChange}
      fields={fields}
      getOptions={getOptions}
      label="Áp cho phiếu nào"
      emptyText={
        <>
          Chưa đặt điều kiện — đây là luồng <b>mặc định</b>, áp cho mọi phiếu không khớp
          luồng nào khác. Cần luồng riêng cho một nhóm phiếu (ví dụ phiếu giao hàng) thì
          tạo thêm luồng, đặt điều kiện ở đây và cho độ ưu tiên cao hơn.
        </>
      }
      sentencePrefix="Luồng chỉ áp khi "
      advancedText={
        <>
          Luồng này đang dùng điều kiện <b>khai tay</b>, phức tạp hơn thứ bộ chọn diễn tả
          được. Giữ nguyên để không làm hỏng luồng đang chạy.
        </>
      }
    />
  )
}
