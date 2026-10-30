import { ENTITY_LABELS } from '../helpers/entity-link'
import { usePermissionApprovers } from '../hooks/use-approvals'

interface PermissionApproversHintProps {
  /** Loại chứng từ của luồng — cũng chính là khóa quyền được soi (backend tự ghi vào bước). */
  entity: string
}

/**
 * Cách chọn "Người có quyền duyệt (theo phân quyền)" (duoc-CR-680): nói rõ luật và bày luôn
 * AI đang giữ quyền Duyệt trên loại chứng từ này, qua vai trò nào, phạm vi nào — người khai
 * luồng không phải mở màn Phân quyền tài khoản ra dò.
 *
 * Danh sách chưa lọc theo phiếu (lúc khai luồng chưa có phiếu): người phạm vi "Công ty" chỉ nhận
 * phiếu của công ty mình khi chạy thật.
 */
export function PermissionApproversHint({ entity }: PermissionApproversHintProps) {
  const { data, isLoading, isError } = usePermissionApprovers(entity, true)
  const label = ENTITY_LABELS[entity] ?? entity

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        Bước giao cho những người được tick quyền <strong>Duyệt</strong> trên <strong>{label}</strong> ở màn Phân quyền tài
        khoản, trong phạm vi dữ liệu của họ (phạm vi <strong>Công ty</strong> chỉ nhận phiếu của công ty mình).
        Chỉ tính phạm vi Phòng ban, Công ty, Tất cả; không tính vai trò Quản trị hệ thống. Đổi phân
        quyền thì phiếu gửi sau tự theo.
      </p>

      {isLoading && <p className="text-xs text-muted-foreground">Đang tải người giữ quyền…</p>}
      {isError && (
        <p className="text-xs text-destructive">Không tải được danh sách người giữ quyền.</p>
      )}
      {data && data.length === 0 && (
        <p className="rounded-md border border-amber-300 bg-amber-50 px-2 py-1.5 text-xs text-amber-900">
          Chưa ai giữ quyền này — bước sẽ không tìm được người duyệt.
        </p>
      )}
      {data && data.length > 0 && (
        <>
          <p className="text-xs font-medium">Hiện có {data.length} người giữ quyền:</p>
          <ul className="max-h-40 divide-y overflow-y-auto rounded-md border text-xs">
            {data.map((person) => (
              <li key={person.employee_id} className="flex justify-between gap-3 px-2 py-1.5">
                <span>
                  {person.name} <span className="text-muted-foreground">{person.code}</span>
                </span>
                <span className="text-right text-muted-foreground">
                  {person.roles.map((grant) => `${grant.role} · ${grant.scope_label}`).join(', ')}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
