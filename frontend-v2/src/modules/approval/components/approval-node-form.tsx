import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { useApprovalOptions } from '../hooks/use-approvals'
import {
  APPROVER_KIND,
  MULTI_MODE,
  NODE_KIND,
  ON_NO_APPROVER,
  type ApprovalNode,
} from '../types/approval'

interface ApprovalNodeFormProps {
  /** Bỏ trống = thêm bước mới. */
  node?: ApprovalNode
  seqGoiY: number
  isPending?: boolean
  onSubmit: (values: Partial<ApprovalNode>) => void
  onCancel: () => void
}

/** Gợi ý cách điền ô «Người duyệt» theo từng cách chọn — nghĩa của ô đổi theo. */
const GOI_Y_REF: Record<number, string> = {
  [APPROVER_KIND.employee]: 'Mã nhân sự, nhiều người ngăn bằng dấu phẩy: 12,15',
  [APPROVER_KIND.role]: 'Mã vai trò, ngăn bằng dấu phẩy: dept_head,pur_manager',
  [APPROVER_KIND.deptHead]: 'Không cần điền — lấy trưởng bộ phận của người nộp',
  [APPROVER_KIND.levelUp]: 'Số cấp cần lên, ví dụ: 2',
  [APPROVER_KIND.companyRep]: 'Không cần điền — lấy người đại diện pháp nhân',
  [APPROVER_KIND.field]: 'Tên ô trên phiếu, ví dụ: signer_employee_id',
}

/**
 * Khai MỘT BƯỚC duyệt (I02–I07).
 *
 * Form dài nhưng phần lớn có mặc định dùng được ngay: bình thường người khai chỉ
 * đụng tên bước, cách chọn người duyệt và ô người duyệt. Bốn khối dưới cùng là
 * cho những luồng thật sự cần.
 */
export function ApprovalNodeForm({
  node,
  seqGoiY,
  isPending,
  onSubmit,
  onCancel,
}: ApprovalNodeFormProps) {
  const { data: options } = useApprovalOptions()
  const [form, setForm] = useState<Partial<ApprovalNode>>(() => ({
    seq: node?.seq ?? seqGoiY,
    branch_key: node?.branch_key ?? '',
    name: node?.name ?? '',
    node_kind: node?.node_kind ?? NODE_KIND.approval,
    flow_role: node?.flow_role ?? 4,
    approver_kind: node?.approver_kind ?? APPROVER_KIND.employee,
    approver_ref: node?.approver_ref ?? '',
    multi_mode: node?.multi_mode ?? MULTI_MODE.any,
    quorum_percent: node?.quorum_percent ?? 50,
    condition: node?.condition ?? '',
    is_default_branch: node?.is_default_branch ?? false,
    skip_duplicate: node?.skip_duplicate ?? 1,
    sla_hours: node?.sla_hours ?? 0,
    on_no_approver: node?.on_no_approver ?? ON_NO_APPROVER.block,
    fallback_employee_id: node?.fallback_employee_id ?? null,
  }))

  function dat<K extends keyof ApprovalNode>(khoa: K, gia_tri: ApprovalNode[K]) {
    setForm((truoc) => ({ ...truoc, [khoa]: gia_tri }))
  }

  function chonSo(khoa: keyof ApprovalNode) {
    return (value: string) => dat(khoa, Number(value) as never)
  }

  return (
    <div className="space-y-4 rounded-lg border bg-muted/30 p-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <Label>Chặng thứ</Label>
          <Input
            type="number"
            min={1}
            value={form.seq ?? 1}
            onChange={(event) => dat('seq', Number(event.target.value))}
          />
          <p className="text-xs text-muted-foreground">
            Nhiều bước cùng số chặng = các nhánh song song, chỉ một nhánh chạy.
          </p>
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label>Tên bước</Label>
          <Input
            placeholder="VD: Trưởng bộ phận duyệt"
            value={form.name ?? ''}
            onChange={(event) => dat('name', event.target.value)}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Bước làm gì</Label>
          <Select value={String(form.node_kind)} onValueChange={chonSo('node_kind')}>
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
          <Select value={String(form.flow_role)} onValueChange={chonSo('flow_role')}>
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
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Chọn người duyệt theo</Label>
          <Select value={String(form.approver_kind)} onValueChange={chonSo('approver_kind')}>
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
        </div>

        <div className="space-y-2">
          <Label>Người duyệt</Label>
          <Input
            value={form.approver_ref ?? ''}
            onChange={(event) => dat('approver_ref', event.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            {GOI_Y_REF[form.approver_kind ?? APPROVER_KIND.employee]}
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Nhiều người thì</Label>
          <Select value={String(form.multi_mode)} onValueChange={chonSo('multi_mode')}>
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
        </div>

        {form.multi_mode === MULTI_MODE.quorum && (
          <div className="space-y-2">
            <Label>Tỷ lệ cần đạt (%)</Label>
            <Input
              type="number"
              min={1}
              max={100}
              value={form.quorum_percent ?? 50}
              onChange={(event) => dat('quorum_percent', Number(event.target.value))}
            />
          </div>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Trùng người đã duyệt phía trước</Label>
          <Select value={String(form.skip_duplicate)} onValueChange={chonSo('skip_duplicate')}>
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
            onChange={(event) => dat('sla_hours', Number(event.target.value))}
          />
          <p className="text-xs text-muted-foreground">0 = không đặt hạn.</p>
        </div>
      </div>

      <div className="space-y-2">
        <Label>Không tìm được người duyệt thì</Label>
        <Select value={String(form.on_no_approver)} onValueChange={chonSo('on_no_approver')}>
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
        {/*  Nói thẳng ra vì sao thiếu lựa chọn mà người dùng có thể đang tìm. */}
        <p className="text-xs text-muted-foreground">
          Cố ý <b>không có</b> lựa chọn «tự động duyệt qua»: với văn bản, nó tạo ra
          văn bản có hiệu lực mà không ai chịu trách nhiệm.
        </p>
      </div>

      {form.on_no_approver === ON_NO_APPROVER.fallback && (
        <div className="space-y-2">
          <Label>Người dự phòng (mã nhân sự)</Label>
          <Input
            type="number"
            value={form.fallback_employee_id ?? ''}
            onChange={(event) =>
              dat('fallback_employee_id', Number(event.target.value) || null)
            }
          />
        </div>
      )}

      <div className="space-y-2">
        <Label>Điều kiện rẽ nhánh</Label>
        <Textarea
          rows={2}
          className="font-mono text-xs"
          placeholder='[{"field": "total", "op": "gte", "value": 50000000}]'
          value={form.condition ?? ''}
          onChange={(event) => dat('condition', event.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Để trống = bước này luôn chạy. Các dòng nối nhau bằng VÀ; cần HOẶC thì khai
          thành hai nhánh cùng số chặng.
        </p>
      </div>

      <div className="flex items-start gap-3">
        <Checkbox
          id="node-default-branch"
          className="mt-0.5"
          checked={form.is_default_branch ?? false}
          onCheckedChange={(checked) => dat('is_default_branch', checked === true)}
        />
        <div className="space-y-1">
          <Label htmlFor="node-default-branch">Là nhánh mặc định của chặng này</Label>
          <p className="text-sm text-muted-foreground">
            Phiếu không khớp nhánh nào sẽ rơi vào đây. <b>Chặng có rẽ nhánh mà thiếu
            nhánh mặc định thì phiếu bị kẹt</b> — không nhánh nào nhận, và nó biến mất
            khỏi mọi danh sách cho tới khi có người đi hỏi.
          </p>
        </div>
      </div>

      <div className="flex justify-end gap-2">
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
