import { ChevronDown, Settings2 } from 'lucide-react'
import { useState } from 'react'

import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { Button } from '@/shared/ui/button'
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
import { cn } from '@/shared/utils/cn'
import { danhSachId, ghepId } from '../helpers/approver-ref'
import { useApprovalOptions } from '../hooks/use-approvals'
import { APPROVER_KIND, MULTI_MODE, type ApprovalNode } from '../types/approval'
import { ApprovalNodeAdvanced } from './approval-node-advanced'

interface ApprovalNodeFormProps {
  /** Bỏ trống = thêm bước mới. */
  node?: ApprovalNode
  seqGoiY: number
  isPending?: boolean
  onSubmit: (values: Partial<ApprovalNode>) => void
  onCancel: () => void
}

/** Ô "Người duyệt" cần điền gì, theo từng cách chọn. */
const GOI_Y_REF: Record<number, string> = {
  [APPROVER_KIND.role]: 'Mã vai trò, ngăn bằng dấu phẩy: dept_head,pur_manager',
  [APPROVER_KIND.levelUp]: 'Số cấp cần lên, ví dụ: 2',
  [APPROVER_KIND.field]: 'Tên ô trên phiếu, ví dụ: signer_employee_id',
}

/**
 * Khai MỘT BƯỚC duyệt.
 *
 * Mặc định chỉ hỏi **ba câu**: bước tên gì, ai duyệt, nhiều người thì tính sao.
 * Chín trên mười bước chỉ cần đúng ba câu đó. Mọi thứ còn lại — trùng người,
 * hạn duyệt, không tìm được ai, rẽ nhánh — nằm sau nút «Tùy chỉnh thêm».
 *
 * Bản trước bày cả mười ô cùng lúc. Người khai luồng phải đọc hết mười ô để
 * biết mình không cần đụng tám trong số đó, và mỗi ô không hiểu là một lần họ
 * dừng lại đi hỏi.
 */
export function ApprovalNodeForm({
  node,
  seqGoiY,
  isPending,
  onSubmit,
  onCancel,
}: ApprovalNodeFormProps) {
  const { data: options } = useApprovalOptions()
  const { data: employeePage } = useEmployees({ page_size: 1000, is_active: true })
  const [moNangCao, setMoNangCao] = useState(false)

  const [form, setForm] = useState<Partial<ApprovalNode>>(() => ({
    seq: node?.seq ?? seqGoiY,
    branch_key: node?.branch_key ?? '',
    name: node?.name ?? '',
    node_kind: node?.node_kind ?? 1,
    flow_role: node?.flow_role ?? 4,
    approver_kind: node?.approver_kind ?? APPROVER_KIND.employee,
    approver_ref: node?.approver_ref ?? '',
    multi_mode: node?.multi_mode ?? MULTI_MODE.any,
    quorum_percent: node?.quorum_percent ?? 50,
    condition: node?.condition ?? '',
    is_default_branch: node?.is_default_branch ?? false,
    skip_duplicate: node?.skip_duplicate ?? 1,
    sla_hours: node?.sla_hours ?? 0,
    on_no_approver: node?.on_no_approver ?? 3,
    fallback_employee_id: node?.fallback_employee_id ?? null,
  }))

  function dat<K extends keyof ApprovalNode>(khoa: K, gia_tri: ApprovalNode[K]) {
    setForm((truoc) => ({ ...truoc, [khoa]: gia_tri }))
  }

  const chonDichDanh = form.approver_kind === APPROVER_KIND.employee
  //  Chỉ ba cách cần ô nhập; ba cách còn lại (trưởng bộ phận, đại diện pháp
  //  nhân, đích danh) tự suy ra người nên bày ô trống chỉ tổ làm người dùng
  //  tưởng mình quên điền.
  const canOThem = GOI_Y_REF[form.approver_kind ?? 0] !== undefined
  const nhieuNguoi = danhSachId(form.approver_ref).length > 1 || !chonDichDanh

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Tên bước</Label>
        <Input
          placeholder="VD: Trưởng bộ phận duyệt"
          value={form.name ?? ''}
          onChange={(event) => dat('name', event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label>Ai duyệt bước này</Label>
        <Select
          value={String(form.approver_kind)}
          onValueChange={(value) => {
            //  Đổi cách chọn thì ô người duyệt phải xóa: mã nhân sự của cách cũ
            //  đọc thành mã vai trò của cách mới là bước giao cho nhầm người.
            dat('approver_kind', Number(value) as never)
            dat('approver_ref', '')
          }}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(options?.approver_kinds ?? []).map((item) => (
              <SelectItem key={item.value} value={String(item.value)}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {chonDichDanh && (
          <EmployeeMultiSelect
            value={danhSachId(form.approver_ref)}
            onChange={(ids) => dat('approver_ref', ghepId(ids))}
            employees={employeePage?.items ?? []}
            placeholder="Chọn người duyệt…"
          />
        )}

        {canOThem && (
          <>
            <Input
              value={form.approver_ref ?? ''}
              onChange={(event) => dat('approver_ref', event.target.value)}
            />
            <p className="text-xs text-muted-foreground">{GOI_Y_REF[form.approver_kind ?? 0]}</p>
          </>
        )}
      </div>

      {/*  Câu "nhiều người thì sao" chỉ có nghĩa khi bước THẬT SỰ có nhiều
           người. Chọn đúng một người mà vẫn hỏi là hỏi một câu không dùng. */}
      {nhieuNguoi && (
        <div className="space-y-2">
          <Label>Nhiều người thì</Label>
          <Select
            value={String(form.multi_mode)}
            onValueChange={(value) => dat('multi_mode', Number(value) as never)}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(options?.multi_modes ?? []).map((item) => (
                <SelectItem key={item.value} value={String(item.value)}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {form.multi_mode === MULTI_MODE.quorum && (
            <Input
              type="number"
              min={1}
              max={100}
              value={form.quorum_percent ?? 50}
              onChange={(event) => dat('quorum_percent', Number(event.target.value))}
            />
          )}
        </div>
      )}

      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="w-full justify-between px-2"
        onClick={() => setMoNangCao(!moNangCao)}
      >
        <span className="flex items-center gap-2">
          <Settings2 className="size-4" />
          Tùy chỉnh thêm
        </span>
        <ChevronDown className={cn('size-4 transition-transform', moNangCao && 'rotate-180')} />
      </Button>

      {moNangCao && (
        <ApprovalNodeAdvanced
          form={form}
          options={options}
          employees={employeePage?.items ?? []}
          onChange={dat}
        />
      )}

      <div className="flex justify-end gap-2 border-t pt-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          Hủy
        </Button>
        <Button type="button" disabled={isPending} onClick={() => onSubmit(form)}>
          {node ? 'Lưu bước' : 'Thêm bước'}
        </Button>
      </div>
    </div>
  )
}