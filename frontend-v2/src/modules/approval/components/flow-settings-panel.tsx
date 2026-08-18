import { useState } from 'react'
import { toast } from 'sonner'
import { SlidersHorizontal, X } from 'lucide-react'

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
  onCancel?: () => void
}

/**
 * Cài đặt chung của một luồng — bảng bên phải khi chưa chọn bước nào.
 */
export function FlowSettingsPanel({
  flow,
  entityMacDinh,
  onDoiEntity,
  onSaved,
  onCancel,
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

  function handleSave() {
    if (!form.name?.trim()) {
      toast.error('Vui lòng nhập tên luồng duyệt')
      return
    }
    save.mutate(
      { id: flow?.id, values: { ...form, name: form.name.trim() } },
      { onSuccess: (moi) => onSaved?.(moi) },
    )
  }

  const isCreate = !flow

  return (
    <Card className="flex h-full flex-col overflow-hidden rounded-2xl border-border/80 shadow-md">
      <div className="flex items-center justify-between border-b border-border/60 bg-muted/30 px-5 py-4">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <SlidersHorizontal className="size-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-foreground">
              {isCreate ? 'Thông tin luồng duyệt' : 'Cài đặt luồng duyệt'}
            </h3>
            <p className="text-xs text-muted-foreground">
              {isCreate ? 'Thiết lập đối tượng & điều kiện áp dụng' : 'Cập nhật phạm vi & điều kiện luồng'}
            </p>
          </div>
        </div>

        {onCancel && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onCancel}
            className="size-7 rounded-lg text-muted-foreground hover:text-foreground"
          >
            <X className="size-4" />
          </Button>
        )}
      </div>

      <div className="flex-1 space-y-4.5 overflow-y-auto p-5">
        <div className="space-y-2">
          <Label className="text-xs font-semibold">Loại chứng từ</Label>
          <Select
            value={form.entity ?? 'document'}
            onValueChange={(value) => {
              dat('entity', value)
              onDoiEntity?.(value)
            }}
            disabled={Boolean(flow)}
          >
            <SelectTrigger className="h-10 w-full rounded-xl">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              {Object.entries(ENTITY_LABELS).map(([ma, nhan]) => (
                <SelectItem key={ma} value={ma}>
                  {nhan}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {flow && (
            <p className="text-[11px] text-muted-foreground">
              Không đổi được sau khi tạo — phiếu đã chạy qua luồng sẽ giữ nguyên loại.
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-semibold">
            Tên luồng <span className="text-destructive">*</span>
          </Label>
          <Input
            placeholder="VD: Duyệt đơn mua hàng trên 50 triệu"
            value={form.name ?? ''}
            onChange={(event) => dat('name', event.target.value)}
            className="h-10 rounded-xl"
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-xs font-semibold">Mã luồng</Label>
            <Input
              placeholder="VD: PO_OVER_50M"
              value={form.code ?? ''}
              onChange={(event) => dat('code', event.target.value)}
              className="h-10 rounded-xl font-mono text-xs"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-semibold">Độ ưu tiên</Label>
            <Input
              type="number"
              value={form.priority ?? 0}
              onChange={(event) => dat('priority', Number(event.target.value))}
              className="h-10 rounded-xl"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label className="text-xs font-semibold">Mô tả luồng</Label>
          <Input
            placeholder="Mô tả mục đích hoặc quy tắc duyệt..."
            value={form.description ?? ''}
            onChange={(event) => dat('description', event.target.value)}
            className="h-10 rounded-xl"
          />
        </div>

        <div className="space-y-2 pt-1">
          <FlowScopePicker
            entity={form.entity ?? 'document'}
            condition={form.condition ?? ''}
            onChange={(condition) => dat('condition', condition)}
          />
        </div>

        <div className="flex items-center justify-between rounded-xl border border-border/60 bg-muted/20 p-3">
          <div className="space-y-0.5">
            <Label htmlFor="flow-active" className="text-xs font-semibold cursor-pointer">
              Trạng thái hoạt động
            </Label>
            <p className="text-[11px] text-muted-foreground">
              {form.is_active ? 'Đang kích hoạt áp dụng cho chứng từ mới' : 'Tạm dừng áp dụng luồng này'}
            </p>
          </div>
          <Switch
            id="flow-active"
            checked={form.is_active ?? true}
            onCheckedChange={(bat) => dat('is_active', bat)}
          />
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 border-t border-border/60 bg-muted/20 p-4">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} className="rounded-xl px-4">
            Hủy
          </Button>
        )}
        <Button
          type="button"
          disabled={save.isPending}
          onClick={handleSave}
          className="rounded-xl px-5 font-semibold shadow-xs"
        >
          {isCreate ? 'Tạo luồng & Vẽ sơ đồ' : 'Lưu cài đặt'}
        </Button>
      </div>
    </Card>
  )
}
