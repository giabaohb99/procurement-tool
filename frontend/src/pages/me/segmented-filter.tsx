/**
 * Dải nút lọc dạng "segmented" dùng chung cho tab Việc cần làm và Yêu cầu hỗ trợ.
 * Hiện luôn SỐ LƯỢNG trên từng nhãn để biết ngay còn bao nhiêu việc mà không phải bấm thử.
 */
export type SegmentOption = { key: string; label: string; count?: number }

export default function SegmentedFilter({
  options, value, onChange,
}: { options: SegmentOption[]; value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ display: 'flex', gap: 4, background: '#f1f5f9', borderRadius: 10, padding: 4, flexWrap: 'wrap' }}>
      {options.map((o) => {
        const active = value === o.key
        return (
          <button
            key={o.key}
            onClick={() => onChange(o.key)}
            style={{
              border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13, fontWeight: 600,
              padding: '7px 14px', borderRadius: 7, display: 'inline-flex', alignItems: 'center', gap: 7,
              background: active ? '#fff' : 'transparent',
              color: active ? 'var(--navy)' : 'var(--muted)',
              boxShadow: active ? '0 1px 3px rgba(15,23,42,.14)' : 'none',
            }}
          >
            {o.label}
            {o.count != null && o.count > 0 && (
              <span
                style={{
                  fontSize: 11, fontWeight: 700, minWidth: 18, height: 18, padding: '0 5px', borderRadius: 999,
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  background: active ? '#e5f7ff' : '#e2e8f0', color: active ? 'var(--teal)' : 'var(--muted)',
                }}
              >
                {o.count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
