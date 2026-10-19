import { Eye, EyeOff, Pencil, Power, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import type { LaborContractVariableColumnActions } from '../config/labor-contract-variable-columns'
import { VARIABLE_SOURCE_SYSTEM, type LaborContractVariable } from '../types/labor-contract-variable'

/**
 * Nút thao tác của MỘT dòng biến. Ẩn theo quyền ở đây — quyền thật do backend (ghi đòi phạm vi «tất cả
 * pháp nhân»). Biến hệ thống: Sửa (tên / mô tả) + Ẩn / Hiện, KHÔNG có Xóa. Biến tùy chỉnh: Sửa ·
 * Ngừng dùng / Bật lại · Xóa (đang dùng thì backend chặn kèm số mẫu / hợp đồng).
 */
export function LaborContractVariableRowActions({
  variable,
  actions,
}: {
  variable: LaborContractVariable
  actions: LaborContractVariableColumnActions
}) {
  const system = variable.source === VARIABLE_SOURCE_SYSTEM
  if (!actions.canManage && !(actions.canDelete && !system)) return null
  return (
    <div className="flex items-center gap-0.5" onClick={(e) => e.stopPropagation()}>
      {actions.canManage && (
        <>
          <Button type="button" variant="ghost" size="icon" className="size-8" title="Sửa"
            aria-label={`Sửa biến ${variable.code}`} onClick={() => actions.onEdit(variable)}>
            <Pencil className="size-4" />
          </Button>
          {system ? (
            <Button type="button" variant="ghost" size="icon" className="size-8"
              title={variable.is_hidden ? 'Hiện lại trong danh sách hướng dẫn' : 'Ẩn khỏi danh sách hướng dẫn'}
              aria-label={`${variable.is_hidden ? 'Hiện' : 'Ẩn'} biến ${variable.code}`}
              onClick={() => actions.onToggleHidden(variable)}>
              {variable.is_hidden ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
            </Button>
          ) : (
            <Button type="button" variant="ghost" size="icon" className="size-8"
              title={variable.is_active ? 'Ngừng dùng' : 'Bật lại'}
              aria-label={`${variable.is_active ? 'Ngừng dùng' : 'Bật lại'} biến ${variable.code}`}
              onClick={() => actions.onToggleActive(variable)}>
              <Power className="size-4" />
            </Button>
          )}
        </>
      )}
      {actions.canDelete && !system && (
        <Button type="button" variant="ghost" size="icon" className="size-8 text-destructive" title="Xóa"
          aria-label={`Xóa biến ${variable.code}`} onClick={() => actions.onDelete(variable)}>
          <Trash2 className="size-4" />
        </Button>
      )}
    </div>
  )
}
