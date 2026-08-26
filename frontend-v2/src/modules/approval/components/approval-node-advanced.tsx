import type { Employee } from '@/modules/hr/types/employee'
import { Checkbox } from '@/shared/ui/checkbox'
import { EmployeeMultiSelect } from '@/shared/ui/employee-multi-select'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { NODE_KIND, ON_NO_APPROVER, type ApprovalNode, type ApprovalOptions } from '../types/approval'
import { NodeConditionBuilder } from './node-condition-builder'

interface ApprovalNodeAdvancedProps {
  form: Partial<ApprovalNode>
  options?: ApprovalOptions
  employees: Employee[]
  /** Loại chứng từ của luồng — bộ dựng điều kiện cần để biết phiếu có ô nào. */
  entity: string
  onChange: <K extends keyof ApprovalNode>(khoa: K, gia_tri: ApprovalNode[K]) => void
}

/**
 * «Tùy chỉnh thêm» của một bước — phần chín trên mười bước KHÔNG cần đụng tới.
 *
 * Tách khỏi form chính không phải để giấu, mà vì mỗi ô ở đây trả lời một câu
 * người khai luồng chỉ hỏi khi họ đã gặp vấn đề: *"cùng một người ký hai lần
 * thì sao"*, *"người duyệt nghỉ việc thì sao"*. Bày sẵn thì họ phải đọc và loại
 * bỏ tám câu chưa liên quan trước khi tới được câu của mình.
 */
export function ApprovalNodeAdvanced({
  form,
  options,
  employees,
  entity,
  onChange,
}: ApprovalNodeAdvancedProps) {
  function pickBook(khoa: keyof ApprovalNode) {
    return (value: string) => onChange(khoa, Number(value) as never)
  }

  return (
    <div className="space-y-4 rounded-lg border bg-muted/30 p-3">
      <div className="space-y-2">
        <Label>Bước làm gì</Label>
        <Select value={String(form.node_kind)} onValueChange={pickBook('node_kind')}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(options?.node_kinds ?? []).map((item) => (
              <SelectItem key={item.value} value={String(item.value)}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {form.node_kind === NODE_KIND.cc && (
          <p className="text-xs text-muted-foreground">
            Người nhận bản sao chỉ được báo, không phải bấm gì — luồng đi tiếp ngay.
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label>Vai trò trong quy trình</Label>
        <Select value={String(form.flow_role)} onValueChange={pickBook('flow_role')}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(options?.flow_roles ?? []).map((item) => (
              <SelectItem key={item.value} value={String(item.value)}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Nếu người này đã duyệt ở bước trước</Label>
        <Select value={String(form.skip_duplicate)} onValueChange={pickBook('skip_duplicate')}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(options?.skip_modes ?? []).map((item) => (
              <SelectItem key={item.value} value={String(item.value)}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Hạn duyệt (giờ)</Label>
        <Input
          type="number"
          min={0}
          value={form.sla_hours ?? 0}
          onChange={(event) => onChange('sla_hours', Number(event.target.value))}
        />
        <p className="text-xs text-muted-foreground">
          0 = không đặt hạn. Quá hạn thì hệ nhắc, lâu nữa thì đẩy lên cấp trên.
        </p>
      </div>

      <div className="space-y-2">
        <Label>Không tìm được người duyệt thì</Label>
        <Select value={String(form.on_no_approver)} onValueChange={pickBook('on_no_approver')}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(options?.on_no_approver ?? []).map((item) => (
              <SelectItem key={item.value} value={String(item.value)}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {/*  Nói thẳng vì sao thiếu lựa chọn mà người dùng có thể đang tìm. */}
        <p className="text-xs text-muted-foreground">
          Cố ý <b>không có</b> lựa chọn «tự động duyệt qua»: với văn bản, nó tạo ra văn
          bản có hiệu lực mà không ai chịu trách nhiệm.
        </p>
      </div>

      {form.on_no_approver === ON_NO_APPROVER.fallback && (
        <div className="space-y-2">
          <Label>Người dự phòng</Label>
          <EmployeeMultiSelect
            value={form.fallback_employee_id ? [form.fallback_employee_id] : []}
            //  Chỉ nhận MỘT người dự phòng — lấy người cuối vừa tick để hành vi
            //  giống một ô chọn đơn, dù dùng chung component chọn nhiều.
            onChange={(ids) => onChange('fallback_employee_id', ids.at(-1) ?? null)}
            employees={employees}
            placeholder="Chọn người dự phòng…"
          />
        </div>
      )}

      <NodeConditionBuilder
        value={form.condition ?? ''}
        onChange={(condition) => onChange('condition', condition)}
        entity={entity}
        employees={employees}
      />

      <div className="flex items-start gap-3">
        <Checkbox
          id="node-default-branch"
          className="mt-0.5"
          checked={form.is_default_branch ?? false}
          onCheckedChange={(checked) => onChange('is_default_branch', checked === true)}
        />
        <div className="space-y-1">
          <Label htmlFor="node-default-branch">Là nhánh mặc định của chặng này</Label>
          <p className="text-xs text-muted-foreground">
            Phiếu không khớp nhánh nào sẽ rơi vào đây. Chặng có rẽ nhánh mà thiếu nhánh
            mặc định thì <b>phiếu bị kẹt</b> và biến mất khỏi mọi danh sách.
          </p>
        </div>
      </div>
    </div>
  )
}
