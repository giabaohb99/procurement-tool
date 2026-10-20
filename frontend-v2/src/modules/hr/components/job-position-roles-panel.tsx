import { Loader2, Plus, Save, Trash2, Users } from 'lucide-react'
import { useRef, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import {
  useApplyJobPositionRoles,
  useJobPositionRoles,
  useSaveJobPositionRoles,
} from '../hooks/use-job-position-roles'
import { useRoles } from '../hooks/use-roles'

/** Vai trò Quản trị hệ thống không bao giờ vào gói (backend cũng chặn). */
const ADMIN_ROLE_CODE = 'admin'

/**
 * Tab «Quyền mặc định» của một chức vụ (duoc-CR-653).
 *
 * ⚠️ Gói chỉ là DANH SÁCH VAI TRÒ. Bậc phạm vi dữ liệu (cá nhân / phòng ban / công ty / tất cả) nằm trong
 * từng vai trò (màn Phân quyền), không chọn lại ở đây — muốn «Trưởng phòng ở bậc phòng ban» thì chọn vai
 * trò đã cấu hình bậc đó.
 *
 * ⚠️ «Lưu» chỉ ghi gói. Người đang giữ chức vụ chỉ nhận thay đổi khi bấm «Áp lại» (có hộp xác nhận, kèm
 * số người) — sửa gói không bao giờ tự đổi quyền của ai.
 */
export function JobPositionRolesPanel({ positionId }: { positionId: number }) {
  const { can } = usePermission()
  const canRead = can('role', 'read')
  const canWrite = can('role', 'write')
  const bundle = useJobPositionRoles(positionId, canRead)
  const { data: allRoles } = useRoles()
  const save = useSaveJobPositionRoles(positionId)
  const apply = useApplyJobPositionRoles(positionId)

  //  Bản nháp: null = chưa sửa gì, hiện thẳng dữ liệu đã lưu.
  const [draft, setDraft] = useState<number[] | null>(null)
  const [pick, setPick] = useState('')
  //  Chốt bấm đúp (L5): `isPending` chỉ đổi sau một nhịp render, hai cú bấm sát nhau vẫn lọt → hai PUT cùng lúc.
  const savingRef = useRef(false)

  if (!canRead) {
    return (
      <p className="text-sm text-muted-foreground">
        Bạn cần quyền xem Vai trò để xem quyền mặc định của chức vụ.
      </p>
    )
  }
  if (bundle.isLoading) return <Loader2 className="animate-spin text-muted-foreground" />
  if (bundle.isError || !bundle.data) {
    return <p className="text-sm text-destructive">Không tải được quyền mặc định của chức vụ.</p>
  }

  const saved = bundle.data.roles.map((r) => r.role_id)
  const current = draft ?? saved
  const dirty = draft !== null && [...draft].sort().join() !== [...saved].sort().join()
  const byId = new Map((allRoles ?? []).map((r) => [r.id, r]))
  const options = (allRoles ?? [])
    .filter((r) => r.code !== ADMIN_ROLE_CODE && !current.includes(r.id))
    .map((r) => ({ value: String(r.id), label: `${r.name} (${r.code})` }))
  const holders = bundle.data.eligible_holders

  const add = () => {
    if (!pick) return
    setDraft([...current, Number(pick)])
    setPick('')
  }

  const onSave = () => {
    if (savingRef.current) return
    savingRef.current = true
    save.mutate(current, {
      onSuccess: () => setDraft(null),
      onSettled: () => {
        savingRef.current = false
      },
    })
  }

  const onApply = async () => {
    const ok = await confirm({
      title: 'Áp lại quyền mặc định',
      message:
        `Đối chiếu lại vai trò của ${holders} người đang giữ chức vụ này: thêm vai trò còn thiếu trong gói ` +
        'và gỡ vai trò hệ thống đã tự cấp trước đây mà nay không còn trong gói. Vai trò quản trị gán tay ' +
        'không bị đụng tới. Tiếp tục?',
      confirmLabel: 'Áp lại',
      tone: 'default',
    })
    if (ok) apply.mutate()
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Quyền mặc định của chức vụ</CardTitle>
        <p className="text-sm text-muted-foreground">
          Tài khoản của nhân sự giữ chức vụ này được tự cấp các vai trò dưới đây (lúc cấp tài khoản và mỗi
          khi đổi chức vụ). Bậc phạm vi dữ liệu nằm trong từng vai trò. Vai trò quản trị gán tay không bị
          thay đổi. Vai trò quản trị và vai trò có quyền ghi/tạo/xóa trên Vai trò / Tài khoản không đưa vào
          gói được. Muốn bỏ một vai trò của gói cho riêng một người: sửa gói hoặc đổi chức vụ của họ — tick
          bỏ ở màn Phân quyền tài khoản sẽ bị «Áp lại» cấp lại.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Vai trò</TableHead>
              <TableHead className="w-40">Mã</TableHead>
              {canWrite && <TableHead className="w-16" />}
            </TableRow>
          </TableHeader>
          <TableBody>
            {current.length === 0 && (
              <TableRow>
                <TableCell colSpan={canWrite ? 3 : 2} className="text-muted-foreground">
                  Chưa có vai trò nào trong gói.
                </TableCell>
              </TableRow>
            )}
            {current.map((id) => {
              const r = byId.get(id)
              const fromServer = bundle.data.roles.find((x) => x.role_id === id)
              return (
                <TableRow key={id}>
                  <TableCell className="font-medium">{r?.name ?? fromServer?.role_name ?? `#${id}`}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {r?.code ?? fromServer?.role_code}
                  </TableCell>
                  {canWrite && (
                    <TableCell>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        aria-label="Bỏ vai trò khỏi gói"
                        onClick={() => setDraft(current.filter((x) => x !== id))}
                      >
                        <Trash2 />
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              )
            })}
          </TableBody>
        </Table>

        {canWrite && (
          <div className="flex flex-wrap items-center gap-2">
            <div className="w-full max-w-sm">
              <SearchSelect
                value={pick}
                onChange={setPick}
                options={options}
                placeholder="Chọn vai trò để thêm…"
                searchPlaceholder="Tìm vai trò…"
                emptyMessage="Không còn vai trò nào để thêm"
              />
            </div>
            <Button type="button" variant="outline" onClick={add} disabled={!pick}>
              <Plus />
              Thêm
            </Button>
            <Button type="button" onClick={onSave} disabled={!dirty || save.isPending}>
              {save.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              Lưu
            </Button>
            <Button
              type="button"
              variant="outline"
              className="ml-auto"
              onClick={onApply}
              disabled={dirty || apply.isPending || holders === 0}
              title={dirty ? 'Lưu gói trước khi áp lại' : undefined}
            >
              {apply.isPending ? <Loader2 className="animate-spin" /> : <Users />}
              Áp lại cho người đang giữ chức vụ ({holders} người)
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
