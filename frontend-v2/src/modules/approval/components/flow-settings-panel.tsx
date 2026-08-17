import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { ENTITY_LABELS } from '../helpers/entity-link'
import { FlowScopePicker } from './flow-scope-picker'
import { useSaveApprovalFlow } from '../hooks/use-approvals'
import type { ApprovalFlow } from '../types/approval'

interface FlowSettingsPanelProps {
  /** Bỏ trống = đang TẠO luồng mới. */
  flow?: ApprovalFlow
  entityMacDinh?: string
  onDoiEntity?: (entity: string) => void
  onSaved?: (flow: ApprovalFlow) => void
}

/**
 * Cài đặt chung của một luồng — bảng bên phải khi chưa chọn bước nào.
 *
 * Tách khỏi sơ đồ vì hai thứ này trả lời hai câu khác nhau: sơ đồ là *"phiếu đi
 * qua những ai"*, cài đặt là *"luồng này áp cho phiếu nào"*. Trộn vào một chỗ
 * thì mỗi lần sửa một cái tên bước lại phải cuộn qua cả khối điều kiện áp dụng.
 */
export function FlowSettingsPanel({
  flow,
  entityMacDinh,
  onDoiEntity,
  onSaved,
}: FlowSettingsPanelProps) {
  const save = useSaveApprovalFlow()
  const [form, setForm] = useState<Partial<ApprovalFlow>>(() => ({
    entity: flow?.entity ?? entityMacDinh ?? 'document',
    code: flow?.code ?? '',
    name: flow?.name ?? '',
    description: flow?.description ?? '',
    is_active: flow?.is_active ?? true,
    priority: flow?.priority ?? 0,
    condition: flow?.condition ?? '',
    company_id: flow?.company_id ?? null,
  }))

  function dat<K extends keyof ApprovalFlow>(khoa: K, gia_tri: ApprovalFlow[K]) {
    setForm((truoc) => ({ ...truoc, [khoa]: gia_tri }))
  }

  return (
    <Card className="space-y-4 p-4">
      <p className="text-sm font-medium">Cài đặt luồng</p>

      <div className="space-y-2">
        <Label>Loại chứng từ</Label>
        <Select
          value={form.entity ?? 'document'}
          onValueChange={(value) => {
            dat('entity', value)
            onDoiEntity?.(value)
          }}
          //  Đổi loại chứng từ của luồng ĐANG DÙNG là đổi ý nghĩa của mọi phiếu
          //  đã chạy qua nó — khóa lại, muốn khác thì tạo luồng mới.
          disabled={Boolean(flow)}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(ENTITY_LABELS).map(([ma, nhan]) => (
              <SelectItem key={ma} value={ma}>
                {nhan}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {flow && (
          <p className="text-xs text-muted-foreground">
            Không đổi được sau khi tạo — phiếu đã chạy qua luồng này sẽ mất ý nghĩa.
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label>Tên luồng</Label>
        <Input
          placeholder="VD: Duyệt quy chế nội bộ"
          value={form.name ?? ''}
          onChange={(event) => dat('name', event.target.value)}
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Mã luồng</Label>
          <Input
            value={form.code ?? ''}
            onChange={(event) => dat('code', event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>Độ ưu tiên</Label>
          <Input
            type="number"
            value={form.priority ?? 0}
            onChange={(event) => dat('priority', Number(event.target.value))}
          />
        </div>
      </div>

      <FlowScopePicker
        entity={form.entity ?? 'document'}
        condition={form.condition ?? ''}
        onChange={(condition) => dat('condition', condition)}
      />

      <div className="flex items-center gap-3">
        <Switch
          id="flow-active"
          checked={form.is_active ?? true}
          onCheckedChange={(bat) => dat('is_active', bat)}
        />
        <Label htmlFor="flow-active">Đang dùng</Label>
      </div>

      <Button
        type="button"
        className="w-full"
        disabled={save.isPending}
        onClick={() =>
          save.mutate({ id: flow?.id, values: form }, { onSuccess: (moi) => onSaved?.(moi) })
        }
      >
        {flow ? 'Lưu cài đặt' : 'Tạo luồng'}
      </Button>
    </Card>
  )
}
