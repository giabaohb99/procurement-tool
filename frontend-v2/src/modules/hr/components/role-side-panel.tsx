import { Plus, Search } from 'lucide-react'
import { useState } from 'react'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
import { useCreateRole } from '../hooks/use-roles'
import type { Role } from '../types/role'

interface RoleSidePanelProps {
  roles: Role[]
  selectedId: number | null
  onSelect: (roleId: number) => void
}

/** Cột trái màn Phân quyền: tìm, chọn và tạo vai trò. */
export function RoleSidePanel({ roles, selectedId, onSelect }: RoleSidePanelProps) {
  const [keyword, setKeyword] = useState('')
  const [isAdding, setAdding] = useState(false)
  const [draft, setDraft] = useState({ code: '', name: '' })

  const createRole = useCreateRole()

  const visible = roles.filter(
    (role) =>
      !keyword || `${role.name} ${role.code}`.toLowerCase().includes(keyword.toLowerCase()),
  )

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

        {visible.map((role) => (
          <button
            key={role.id}
            type="button"
            onClick={() => onSelect(role.id)}
            className={cn(
              'w-full rounded-lg px-3 py-2 text-left text-sm transition-colors',
              role.id === selectedId
                ? 'bg-primary/10 font-semibold text-primary'
                : 'hover:bg-accent',
            )}
          >
            {role.name}
            <span className="block text-xs font-normal text-muted-foreground">
              {role.code}
            </span>
          </button>
        ))}
      </div>
    </Card>
  )
}
