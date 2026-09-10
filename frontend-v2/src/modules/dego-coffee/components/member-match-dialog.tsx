import { Link2, Search, UserPlus } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Input } from '@/shared/ui/input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { coffeeApi } from '../api/coffee-api'
import { useCreatePosPartner, useMatchMember, useUnmatchMember } from '../hooks/use-coffee'
import type { CoffeeMember, PosPartnerHit } from '../types/coffee'
import { formatPoints } from '../utils/format-points'
import { CoffeeDialogShell } from './coffee-dialog-shell'

interface MemberMatchDialogProps {
  member: CoffeeMember
  onClose: () => void
}

/**
 * Ghép nhân sự ↔ khách POS365 (B-02, luật A3): tra SĐT/tên, NGƯỜI xác nhận từng
 * cặp; đã ghép thì chỉ hiện thông tin + nút Gỡ ghép — không cho ghép đè.
 * Tìm không ra thì tạo khách mới bên POS365 (B-03) — hành động GHI sang hệ
 * ngoài, có xem trước dữ liệu sẽ gửi.
 */
export function MemberMatchDialog({ member, onClose }: MemberMatchDialogProps) {
  const matchMember = useMatchMember()
  const unmatchMember = useUnmatchMember()
  const createPartner = useCreatePosPartner()
  const [keyword, setKeyword] = useState('')
  const [hits, setHits] = useState<PosPartnerHit[] | null>(null)
  const [selected, setSelected] = useState<PosPartnerHit | null>(null)
  const [searching, setSearching] = useState(false)

  const matched = member.pos_partner_id > 0
  const pending = matchMember.isPending || unmatchMember.isPending || createPartner.isPending

  async function handleSearch() {
    if (keyword.trim().length < 3) {
      toast.error('Nhập ít nhất 3 ký tự (SĐT hoặc tên) để tìm bên POS365.')
      return
    }
    setSearching(true)
    setSelected(null)
    try {
      const data = await coffeeApi.searchPosPartners(keyword.trim())
      setHits(data.items)
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      setSearching(false)
    }
  }

  function handleConfirm() {
    if (matched) {
      onClose()
      return
    }
    if (!selected) {
      toast.error('Chọn một khách POS365 trong kết quả tìm rồi mới xác nhận ghép.')
      return
    }
    matchMember.mutate(
      { id: member.id, pos_partner_id: selected.pos_partner_id, pos_partner_code: selected.code },
      { onSuccess: onClose },
    )
  }

  async function handleUnmatch() {
    if (
      !(await confirm({
        message: `Gỡ ghép ${member.employee_name} khỏi khách ${member.pos_partner_code}? Đơn mới từ khách này sẽ rơi vào hàng chờ chưa khớp.`,
      }))
    )
      return
    unmatchMember.mutate(member.id, { onSuccess: onClose })
  }

  async function handleCreatePartner() {
    if (
      !(await confirm({
        message: `Tạo khách MỚI trên POS365 với tên "${member.employee_name}" (mã ${member.employee_code}) rồi ghép luôn?`,
      }))
    )
      return
    createPartner.mutate(
      { id: member.id, name: member.employee_name, phone: '' },
      { onSuccess: onClose },
    )
  }

  return (
    <CoffeeDialogShell
      title={`Ghép POS365 — ${member.employee_name}`}
      description={
        matched
          ? 'Thành viên đã ghép. Muốn ghép sang khách khác thì Gỡ ghép trước (có ghi nhật ký).'
          : 'Tra khách bên POS365 rồi xác nhận TỪNG cặp — hệ không bao giờ tự ghép lại theo tên/SĐT.'
      }
      dirty={false}
      pending={pending}
      confirmLabel={matched ? 'Đóng' : 'Xác nhận ghép'}
      onConfirm={handleConfirm}
      onClose={onClose}
      widthClass="sm:max-w-[560px]"
    >
      {matched ? (
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-medium">Khách POS365</span>
            <ReadOnlyValue>{member.pos_partner_code || member.pos_partner_id}</ReadOnlyValue>
          </div>
          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-medium">Ghép lúc</span>
            <ReadOnlyValue>{member.matched_at}</ReadOnlyValue>
          </div>
          <div>
            <Button variant="destructive" onClick={() => void handleUnmatch()} disabled={pending}>
              Gỡ ghép
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className="flex gap-2">
            <Input
              value={keyword}
              placeholder="SĐT hoặc tên khách bên POS365"
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void handleSearch()
              }}
            />
            <Button variant="outline" onClick={() => void handleSearch()} disabled={searching}>
              <Search className="size-4" />
              Tìm
            </Button>
          </div>

          {hits !== null && hits.length === 0 && (
            <div className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
              Không tìm thấy khách nào.
              <div className="mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => void handleCreatePartner()}
                  disabled={pending}
                >
                  <UserPlus className="size-4" />
                  Tạo khách mới trên POS365
                </Button>
              </div>
            </div>
          )}

          {(hits ?? []).length > 0 && (
            <div className="flex max-h-64 flex-col gap-1 overflow-y-auto">
              {(hits ?? []).map((hit) => (
                <button
                  key={hit.pos_partner_id}
                  type="button"
                  onClick={() => setSelected(hit)}
                  className={
                    selected?.pos_partner_id === hit.pos_partner_id
                      ? 'flex items-center justify-between rounded-md border border-primary bg-accent px-3 py-2 text-left'
                      : 'flex items-center justify-between rounded-md border px-3 py-2 text-left hover:bg-accent/50'
                  }
                >
                  <span className="min-w-0">
                    <span className="block truncate font-medium">{hit.name}</span>
                    <span className="block font-mono text-xs text-muted-foreground">
                      {hit.code} · {hit.phone || 'không SĐT'}
                    </span>
                  </span>
                  {selected?.pos_partner_id === hit.pos_partner_id && (
                    <Link2 className="size-4 shrink-0 text-primary" />
                  )}
                </button>
              ))}
            </div>
          )}

          {selected && (
            <p className="text-sm text-muted-foreground">
              Sẽ ghép <span className="font-medium text-foreground">{member.employee_name}</span>{' '}
              với khách <span className="font-mono">{selected.code}</span>
              {selected.point ? ` (điểm hiện có bên POS365: ${formatPoints(selected.point)})` : ''}.
            </p>
          )}
        </>
      )}
    </CoffeeDialogShell>
  )
}
