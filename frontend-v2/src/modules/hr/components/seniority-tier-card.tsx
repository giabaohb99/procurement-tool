import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  useDeleteSeniorityTier,
  useSaveSeniorityTier,
  useSeniorityTiers,
} from '../hooks/use-leave'
import type { SeniorityTier } from '../types/leave'

interface SeniorityTierCardProps {
  leaveTypeId: number
}

const EMPTY_FORM = { years_from: 5, years_to: 0, extra_days: 1 }

/**
 * BẬC THÂM NIÊN của một loại nghỉ — luật *5 năm +1 ngày* khai bằng DỮ LIỆU.
 *
 * Viết `years // 5` trong `balance_service` thì tới lúc công ty đổi thành bậc
 * không đều (5 năm +1, 10 năm +3) phải sửa mã và deploy. Bảng này là chỗ Nhân
 * sự tự thêm dòng.
 *
 * ⚠️ Lấy bậc **CAO NHẤT khớp được**, KHÔNG cộng dồn: khai *"từ 5 năm: +1"* và
 * *"từ 10 năm: +2"* thì người 10 năm được +2, không phải +3. Câu này hiện thẳng
 * trên màn hình vì đọc bảng số không đoán ra được, và đoán sai thì Nhân sự khai
 * bậc theo kiểu cộng dồn — mọi người sẽ thiếu ngày.
 */
export function SeniorityTierCard({ leaveTypeId }: SeniorityTierCardProps) {
  const { can } = usePermission()
  const canWrite = can('leave_type', 'write')

  const { data, isLoading } = useSeniorityTiers(leaveTypeId)
  const save = useSaveSeniorityTier(leaveTypeId)
  const remove = useDeleteSeniorityTier(leaveTypeId)
  const [form, setForm] = useState(EMPTY_FORM)

  const tiers: SeniorityTier[] = data?.items ?? []

  const addTier = () => {
    save.mutate({ values: form }, { onSuccess: () => setForm(EMPTY_FORM) })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Bậc phép theo thâm niên</CardTitle>
        <p className="text-sm text-muted-foreground">
          Số ngày <strong>cộng thêm</strong> vào hạn mức năm. Hệ thống lấy bậc{' '}
          <strong>cao nhất khớp được</strong>, không cộng dồn các bậc — khai «từ 5 năm: +1»
          và «từ 10 năm: +2» thì người 10 năm được <strong>+2</strong>, không phải +3.
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Đang tải…</p>
        ) : tiers.length === 0 ? (
          <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            Chưa khai bậc nào — mọi người nhận đúng hạn mức năm, không cộng thâm niên.
          </p>
        ) : (
          <ul className="divide-y rounded-md border">
            {tiers.map((tier) => (
              <li key={tier.id} className="flex items-center gap-3 px-3 py-2 text-sm">
                <span className="flex-1">
                  Từ <strong>{tier.years_from}</strong> năm
                  {/* `years_to = 0` là bậc cuối, không có trần trên — hiện số 0
                      thì đọc thành "đến 0 năm", vô nghĩa. */}
                  {tier.years_to ? ` đến dưới ${tier.years_to} năm` : ' trở lên'}
                </span>
                <span className="font-semibold text-primary">+{tier.extra_days} ngày</span>
                {canWrite && (
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Xóa bậc từ ${tier.years_from} năm`}
                    onClick={() => remove.mutate(tier.id)}
                    disabled={remove.isPending}
                  >
                    <Trash2 className="size-4 text-destructive" />
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}

        {canWrite && (
          <div className="grid grid-cols-1 items-end gap-3 rounded-md border bg-muted/30 p-3 sm:grid-cols-4">
            <div className="space-y-1">
              <Label htmlFor="tier-from">Từ năm thứ</Label>
              <Input
                id="tier-from"
                type="number"
                min={0}
                value={form.years_from}
                onChange={(e) => setForm({ ...form, years_from: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="tier-to">Đến dưới năm thứ</Label>
              <Input
                id="tier-to"
                type="number"
                min={0}
                value={form.years_to}
                onChange={(e) => setForm({ ...form, years_to: Number(e.target.value) })}
              />
              <p className="text-xs text-muted-foreground">0 = bậc cuối, không có trần trên</p>
            </div>
            <div className="space-y-1">
              <Label htmlFor="tier-extra">Cộng thêm (ngày)</Label>
              <Input
                id="tier-extra"
                type="number"
                min={0}
                step={0.5}
                value={form.extra_days}
                onChange={(e) => setForm({ ...form, extra_days: Number(e.target.value) })}
              />
            </div>
            <Button onClick={addTier} disabled={save.isPending}>
              <Plus className="mr-1 size-4" />
              Thêm bậc
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
