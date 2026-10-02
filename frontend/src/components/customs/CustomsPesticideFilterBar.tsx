// Cụm ô tìm + bốn ô chọn + nút «Xóa lọc» của mục «Thuốc BVTV» — tách khỏi `CustomsPesticideTab.tsx`
// (02/10/2026) để tệp đó không vượt 200 dòng. Thuần hiển thị: nhận giá trị/hàm đặt giá trị từ
// trang cha, không tự giữ state hay gọi API — xem `customs-pesticide-filter-controls.tsx` ở
// frontend-v2 (bản này dựng cùng tinh thần, khác khuôn component vì v1 không dùng shadcn).
import SearchSelect from '../SearchSelect'
import { BANNED_ONLY, PesticideFilters, formatBannedFilterLabel } from '../../utils/customs-pesticide'
import { toSentenceCaseIfShouting } from '../../utils/customs-pesticide-display'

type Props = {
  draftQ: string
  onDraftQChange: (v: string) => void
  draft: PesticideFilters
  options: any
  filtersActive: boolean
  onSelect: (k: 'status' | 'pestGroup' | 'sector' | 'banned', v: string) => void
  onReset: () => void
}

export default function CustomsPesticideFilterBar({
  draftQ, onDraftQChange, draft, options, filtersActive, onSelect, onReset,
}: Props) {
  return (
    <>
      <input value={draftQ} onChange={(e) => onDraftQChange(e.target.value)} aria-label="Tìm thuốc BVTV"
        placeholder="Tên thuốc, hoạt chất, công ty, số đăng ký…" style={{ width: 260 }} />
      <div style={{ width: 190 }}>
        <SearchSelect value={draft.status} placeholder="Tất cả tình trạng" autoSelectSingle={false}
          options={[{ value: '', label: 'Tất cả tình trạng' },
            ...(options?.statuses || []).map((s: any) => ({ value: String(s.value), label: `${s.label} (${s.count})` }))]}
          onChange={(v) => onSelect('status', v)} />
      </div>
      <div style={{ width: 200 }}>
        <SearchSelect value={draft.pestGroup} placeholder="Tất cả phân nhóm" autoSelectSingle={false}
          options={(options?.pest_groups || []).map((g: any) => ({ value: g.value, label: `${g.value} (${g.count})` }))}
          onChange={(v) => onSelect('pestGroup', v)} />
      </div>
      {/* 01/10/2026 — lọc Lĩnh vực (backend có sẵn); cột tra cứu của trang chi tiết mở thẳng tham số này. */}
      <div style={{ width: 220 }}>
        <SearchSelect value={draft.sector ?? ''} placeholder="Tất cả lĩnh vực" autoSelectSingle={false}
          options={(options?.sectors || []).map((g: any) => ({ value: g.value, label: `${toSentenceCaseIfShouting(g.value)} (${g.count})` }))}
          onChange={(v) => onSelect('sector', v)} />
      </div>
      <div style={{ width: 240 }}>
        <SearchSelect value={draft.banned} placeholder="Mọi thuốc" autoSelectSingle={false}
          options={[{ value: BANNED_ONLY, label: formatBannedFilterLabel(options?.banned_rules, options?.banned_count) }]}
          onChange={(v) => onSelect('banned', v)} />
      </div>
      {filtersActive && (
        <button className="btn ghost" onClick={onReset}><i className="ti ti-rotate" />Xóa lọc</button>
      )}
    </>
  )
}
