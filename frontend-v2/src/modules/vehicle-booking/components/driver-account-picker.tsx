import { Search, X } from 'lucide-react'
import { useState } from 'react'

import { employeeInitials } from '@/modules/hr/types/employee'
import type { UserAccount } from '@/modules/hr/types/user-account'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { MIN_PHONE_DIGITS, useDriverAccountSearch } from '../hooks/use-driver-account-search'
import { CatalogFormField } from './catalog-form-field'

/**
 * Chữ chờ trong ô khóa khi chưa chọn tài khoản.
 *
 * ⚠️ Phải NHẠT và KHÔNG đậm: ô khóa vẽ chữ navy đậm (đó là format của một giá
 * trị thật), nên để nguyên câu này theo kiểu đó thì nó đọc ra như thể họ tên
 * của người này đúng là "Tự điền khi chọn tài khoản". Để ô trống trơn cũng
 * không xong — người mở trang lần đầu không biết vì sao ba ô đó không gõ được.
 */
function WaitingForAccount() {
  return <span className="font-normal text-muted-foreground">Tự điền khi chọn tài khoản</span>
}

interface DriverAccountPickerProps {
  /** Đã gắn tài khoản (form đang giữ `user_id`). */
  linked: boolean
  name: string
  phone: string
  email: string
  onSelect: (account: UserAccount) => void
  onClear: () => void
}

/**
 * Chọn TÀI KHOẢN NHÂN SỰ cho tài xế nội bộ: tìm theo số điện thoại, bấm một
 * dòng là tên · số điện thoại · email tự điền theo hồ sơ nhân sự.
 *
 * ⚠️ Ba ô tự điền đó hiện bằng `ReadOnlyValue` chứ không phải `<Input readOnly>`
 * xám. Ô nhập xám trông y như ô đang chờ gõ nhưng gõ không vào, nên người dùng
 * bấm vào đó mấy lần rồi mới đi tìm chỗ sửa; chữ trong ô khóa nói ngay rằng giá
 * trị này lấy từ nơi khác. Muốn đổi thì đổi ở hồ sơ nhân sự, hoặc gỡ tài khoản
 * ra chọn người khác.
 *
 * Trạng thái tìm kiếm (ô gõ + tài khoản vừa chọn) giữ TRONG component: biểu mẫu
 * chỉ cần biết kết quả cuối cùng là ai.
 */
export function DriverAccountPicker({
  linked,
  name,
  phone,
  email,
  onSelect,
  onClear,
}: DriverAccountPickerProps) {
  const [phoneSearch, setPhoneSearch] = useState('')
  const [selectedAccount, setSelectedAccount] = useState<UserAccount | null>(null)

  const searchResult = useDriverAccountSearch(phoneSearch)
  const results = searchResult.data?.items ?? []

  function handleSelect(account: UserAccount) {
    setSelectedAccount(account)
    onSelect(account)
  }

  function handleClear() {
    setSelectedAccount(null)
    setPhoneSearch('')
    onClear()
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label>
          Tài khoản nhân sự
          <RequiredMark hint="Tìm và chọn theo số điện thoại" />
        </Label>

        {linked ? (
          <div className="flex items-center gap-3 rounded-lg border bg-muted/40 px-3 py-2 transition-colors">
            <Avatar className="size-8">
              <AvatarImage src={selectedAccount?.avatar} alt={name} />
              <AvatarFallback className="text-xs">{employeeInitials(name)}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium">{name}</div>
              <div className="truncate text-xs text-muted-foreground">
                {[phone, selectedAccount?.code].filter(Boolean).join(' · ')}
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7 shrink-0"
              onClick={handleClear}
              aria-label="Đổi tài khoản"
            >
              <X className="size-4" />
            </Button>
          </div>
        ) : (
          <>
            <div className="relative">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                inputMode="numeric"
                placeholder="Nhập đủ số điện thoại để tìm…"
                value={phoneSearch}
                onChange={(e) => setPhoneSearch(e.target.value)}
              />
            </div>
            {searchResult.enabled ? (
              <div className="flex max-h-52 flex-col gap-1 overflow-y-auto rounded-lg border p-1">
                {searchResult.isLoading && (
                  <p className="px-2 py-3 text-center text-sm text-muted-foreground">Đang tìm…</p>
                )}
                {!searchResult.isLoading && results.length === 0 && (
                  <p className="px-2 py-3 text-center text-sm text-muted-foreground">
                    Không tìm thấy nhân sự nào khớp số điện thoại này.
                  </p>
                )}
                {results.map((account) => (
                  <button
                    key={account.id}
                    type="button"
                    onClick={() => handleSelect(account)}
                    className="flex items-center gap-3 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-accent"
                  >
                    <Avatar className="size-8">
                      <AvatarImage src={account.avatar} alt={account.full_name} />
                      <AvatarFallback className="text-xs">
                        {employeeInitials(account.full_name)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{account.full_name}</div>
                      <div className="truncate text-xs text-muted-foreground">
                        {[account.phone, account.code].filter(Boolean).join(' · ') || account.email}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                Gõ đủ số điện thoại ({MIN_PHONE_DIGITS} chữ số trở lên) để hiện danh sách.
              </p>
            )}
          </>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <CatalogFormField label="Họ tên">
          <ReadOnlyValue>{name || <WaitingForAccount />}</ReadOnlyValue>
        </CatalogFormField>
        <CatalogFormField label="Số điện thoại">
          <ReadOnlyValue>{phone || <WaitingForAccount />}</ReadOnlyValue>
        </CatalogFormField>
        <CatalogFormField
          label="Email"
          fullWidth
          hint="Lấy từ hồ sơ nhân sự — sai thì sửa ở hồ sơ, không sửa ở đây."
        >
          <ReadOnlyValue>{email || <WaitingForAccount />}</ReadOnlyValue>
        </CatalogFormField>
      </div>
    </div>
  )
}
