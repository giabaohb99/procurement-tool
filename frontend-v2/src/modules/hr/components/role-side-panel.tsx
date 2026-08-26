import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { Plus, Search } from 'lucide-react'
import { useState } from 'react'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { useCreateRole, useSaveRoleOrder, useUpdateRole } from '../hooks/use-roles'
import type { Role } from '../types/role'
import { RoleListItem } from './role-list-item'
import { RoleRenameDialog } from './role-rename-dialog'

interface RoleSidePanelProps {
  roles: Role[]
  selectedId: number | null
  onSelect: (roleId: number) => void
}

/** Cột trái màn Phân quyền: tìm, chọn, tạo, đổi tên và xếp thứ tự vai trò. */
export function RoleSidePanel({ roles, selectedId, onSelect }: RoleSidePanelProps) {
  const [keyword, setKeyword] = useState('')
  const [isAdding, setAdding] = useState(false)
  const [draft, setDraft] = useState({ code: '', name: '' })
  //  Thứ tự đang hiện trên màn, đặt ngay lúc thả. Chờ máy chủ trả rồi mới vẽ lại
  //  thì dòng vừa kéo nhảy về chỗ cũ chừng nửa giây — nhìn như thao tác trượt.
  //  `null` = chưa kéo lần nào, cứ theo thứ tự máy chủ trả.
  const [thuTuTamThoi, setThuTuTamThoi] = useState<number[] | null>(null)
  //  Vai trò đang mở hộp đổi tên. `null` = hộp đóng.
  const [dangDoiTen, setDangDoiTen] = useState<Role | null>(null)

  const { can } = usePermission()
  const canWrite = can('role', 'write')
  const createRole = useCreateRole()
  const updateRole = useUpdateRole()
  const saveOrder = useSaveRoleOrder()

  const sensors = useSensors(
    //  Phải kéo đi 6px mới tính là kéo, nếu không mỗi cú bấm chọn vai trò đều bị
    //  nuốt thành một thao tác kéo dài 0 pixel (cùng lý do với `flow-canvas`).
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const daSapXep = xepTheoThuTuTamThoi(roles, thuTuTamThoi)

  const visible = daSapXep.filter(
    (role) =>
      !keyword || `${role.name} ${role.code}`.toLowerCase().includes(keyword.toLowerCase()),
  )

  //  ĐANG LỌC THÌ KHÔNG CHO KÉO. Trên danh sách đã lọc, "thả dòng A xuống dưới
  //  dòng B" không nói được gì về những dòng đang bị ẩn nằm giữa hai dòng đó —
  //  lưu xuống là thứ tự thật khác hẳn thứ người dùng vừa nhìn thấy.
  const dangLoc = keyword.trim().length > 0
  const choKeo = canWrite && !dangLoc

  function khiThaDong(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const ids = daSapXep.map((role) => role.id)
    const tu = ids.indexOf(Number(active.id))
    const den = ids.indexOf(Number(over.id))
    if (tu < 0 || den < 0) return

    const moi = arrayMove(ids, tu, den)
    setThuTuTamThoi(moi)
    saveOrder.mutate(moi)
  }

  async function submitNewRole() {
    const code = draft.code.trim()
    if (!code) return
    const created = await createRole.mutateAsync({
      code,
      name: draft.name.trim() || code,
    })
    setAdding(false)
    setDraft({ code: '', name: '' })
    onSelect(created.id)
  }

  return (
    <Card className="h-fit gap-3 p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-navy">Vai trò</p>
        <PermissionGate entity="role" action="create">
          <Button size="sm" variant="outline" onClick={() => setAdding((v) => !v)}>
            <Plus />
            Thêm
          </Button>
        </PermissionGate>
      </div>

      {isAdding && (
        <div className="space-y-2 rounded-lg border border-dashed p-3">
          <Input
            placeholder="Mã (vd pur_staff)"
            value={draft.code}
            onChange={(e) => setDraft({ ...draft, code: e.target.value })}
          />
          <Input
            placeholder="Tên vai trò"
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={submitNewRole}
              disabled={createRole.isPending || !draft.code.trim()}
            >
              Tạo
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setAdding(false)}>
              Hủy
            </Button>
          </div>
        </div>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Tìm vai trò…"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
      </div>

      <div className="max-h-[60vh] space-y-1 overflow-y-auto">
        {visible.length === 0 && (
          <p className="py-4 text-center text-sm text-muted-foreground">
            Không có vai trò nào khớp.
          </p>
        )}

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={khiThaDong}
        >
          <SortableContext
            items={visible.map((role) => role.id)}
            strategy={verticalListSortingStrategy}
          >
            {visible.map((role) => (
              <RoleListItem
                key={role.id}
                role={role}
                selected={role.id === selectedId}
                onSelect={onSelect}
                canWrite={canWrite}
                canDrag={choKeo}
                onRename={setDangDoiTen}
              />
            ))}
          </SortableContext>
        </DndContext>
      </div>

      <RoleRenameDialog
        role={dangDoiTen}
        pending={updateRole.isPending}
        onOpenChange={(open) => !open && setDangDoiTen(null)}
        onSubmit={(roleId, name) =>
          updateRole.mutate({ roleId, name }, { onSuccess: () => setDangDoiTen(null) })
        }
      />

      {/*  Nói ra vì sao tay cầm kéo biến mất khi đang gõ tìm — không nói thì
           người dùng tưởng chức năng hỏng. */}
      {canWrite && dangLoc && (
        <p className="text-xs text-muted-foreground">
          Xóa từ khóa tìm để kéo đổi thứ tự.
        </p>
      )}
    </Card>
  )
}

/**
 * Áp thứ tự vừa kéo lên danh sách máy chủ trả về.
 *
 * Vai trò KHÔNG có trong dãy tạm (ai đó vừa tạo thêm ở tab khác) được đẩy xuống
 * cuối chứ không bị bỏ rơi — mất một dòng khỏi cột trái là mất luôn đường vào
 * ma trận quyền của nó.
 */
function xepTheoThuTuTamThoi(roles: Role[], thuTu: number[] | null): Role[] {
  if (!thuTu) return roles
  const viTri = new Map(thuTu.map((id, index) => [id, index]))
  return [...roles].sort(
    (a, b) => (viTri.get(a.id) ?? Number.MAX_SAFE_INTEGER) - (viTri.get(b.id) ?? Number.MAX_SAFE_INTEGER),
  )
}
