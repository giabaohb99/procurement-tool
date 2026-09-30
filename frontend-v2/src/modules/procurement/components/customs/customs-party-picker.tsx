// bao-CR-503 — ô gõ có gợi ý để THÊM doanh nghiệp nhập khẩu / đối tác nước ngoài vào bộ lọc
// (sheet 4 mục 4–5 của yêu cầu phòng Thu mua: «Multi-select có gợi ý»).
//
// Chọn nhiều bằng cách cộng dồn: mỗi lần chọn là thêm một chip vào bộ lọc (cùng cơ chế với nút
// «Lọc theo doanh nghiệp này» ở thẻ Nhà nhập khẩu / chi tiết dòng), ô tự trống lại để gõ tiếp.
// Danh sách tra PHÍA SERVER (`/api/customs/parties`) — hàng nghìn đối tượng, không nạp hết được.
import { useState } from 'react'

import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { SearchSelect } from '@/shared/ui/search-select'

import { useCustomsParties } from '../../hooks/use-customs'
import type { CustomsPartyType } from '../../types/customs'
import { toPartyOptions } from '../../utils/customs'

interface CustomsPartyPickerProps {
  partyType: CustomsPartyType
  /** Id đang nằm trong bộ lọc, nối dấu phẩy — để khỏi gợi ý lại người đã chọn. */
  selectedIds: string
  placeholder: string
  onPick: (id: number, name: string) => void
}

export function CustomsPartyPicker({ partyType, selectedIds, placeholder, onPick }: CustomsPartyPickerProps) {
  const [keyword, setKeyword] = useState('')
  const debouncedKeyword = useDebouncedValue(keyword, 300)
  const parties = useCustomsParties(partyType, debouncedKeyword.trim())

  return (
    <SearchSelect
      value=""
      onChange={(value) => {
        const hit = parties.data?.find((party) => String(party.id) === value)
        if (hit) onPick(hit.id, hit.name)
      }}
      options={toPartyOptions(parties.data, selectedIds)}
      placeholder={placeholder}
      searchPlaceholder="Gõ tên hoặc mã số thuế…"
      emptyMessage={parties.isFetching ? 'Đang tìm…' : 'Không tìm thấy.'}
      onSearchChange={setKeyword}
    />
  )
}
