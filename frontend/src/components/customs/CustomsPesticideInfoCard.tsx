// THẺ ĐẦU TRANG chi tiết thuốc BVTV — giao diện cũ (01/10/2026, đồng bộ bản v2
// `frontend-v2/.../customs-pesticide-hero-card.tsx`). Gom thứ người đọc cần ngay vào một chỗ: nút lùi
// + tên + tình trạng + nút thao tác, hoạt chất, công ty, số đăng ký (chép được), bốn ô thông tin nhanh
// (phân nhóm · lĩnh vực · hiệu lực đến · nhóm độc) và câu tóm tắt. Lưới nhãn – giá trị cũ bỏ hẳn.
import type { CSSProperties, ReactNode } from 'react'
import { toast } from '../toast'
import { fmtDate } from './customs-shared'
import { pesticideStatusBadgeClass } from '../../utils/customs-pesticide'
import {
  describeRemainingTerm,
  parsePesticideToxicity,
  toSentenceCaseIfShouting,
  type ToxicityItem,
  type ToxicitySeverity,
} from '../../utils/customs-pesticide-display'

const MUTED: CSSProperties = { color: 'var(--muted)' }

export default function CustomsPesticideInfoCard({ data, leading, actions }: {
  data: any
  /** Nút lùi — đứng trước tên thuốc. */
  leading?: ReactNode
  /** Sửa · Xóa — góc phải dòng tên. */
  actions?: ReactNode
}) {
  const manual = !!data.is_manual
  //  Trống thì nói rõ: thuốc từ bản cào là «Nguồn không ghi», thuốc tự thêm là «Chưa nhập».
  const missing = manual ? 'Chưa nhập' : 'Nguồn không ghi'
  const remaining = describeRemainingTerm(data.expires_on, new Date())
  const toxicity = parsePesticideToxicity(data.toxicity)

  return (
    <div className="card" style={{ padding: 0, marginBottom: 16, overflow: 'hidden' }}>
      <div style={{ padding: 20 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', gap: 12 }}>
          {leading}
          <div style={{ flex: 1, minWidth: 0 }}>
            <h2 className="page-title" style={{ margin: 0, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 }}>
              {data.trade_name}
              <span className={`badge ${pesticideStatusBadgeClass(data.status)}`}>{data.status_label || 'Chưa rõ'}</span>
              {manual && <span className="badge gray">Tự thêm</span>}
            </h2>
            <div style={{ fontSize: 14, marginTop: 4 }}>
              <b style={{ fontWeight: 600 }}>{data.active_ingredient || missing}</b>
              {data.concentration && <span style={MUTED}> · {data.concentration}</span>}
            </div>
            <div style={{ fontSize: 14, marginTop: 2, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6, ...MUTED }}>
              <span>{data.registrant || missing}</span>
              {data.registration_no && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  · SĐK <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', color: 'var(--ink)' }}>{data.registration_no}</span>
                  <CopyIcon value={data.registration_no} />
                </span>
              )}
            </div>
          </div>
          {actions && <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>{actions}</div>}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginTop: 16 }}>
          <Fact label="Phân nhóm" empty={!data.pest_group} missing={missing}>{data.pest_group}</Fact>
          <Fact label="Lĩnh vực" empty={!data.sector} missing={missing}>{toSentenceCaseIfShouting(data.sector || '')}</Fact>
          {/* Ngày HẾT HẠN đứng dòng chính; ngày cấp + thời gian còn lại xuống dòng phụ. */}
          <Fact label="Hiệu lực đến" empty={!data.expires_on} missing={missing}>
            {fmtDate(data.expires_on)}
            <span style={{ display: 'block', fontSize: 12, fontWeight: 400, ...MUTED }}>
              {data.registered_on && <>Cấp {fmtDate(data.registered_on)}</>}
              {data.registered_on && remaining && ' · '}
              {remaining && (
                <span style={remaining === 'Đã hết hạn' ? { color: 'var(--red)', fontWeight: 600 } : undefined}>{remaining}</span>
              )}
            </span>
          </Fact>
          <Fact label="Nhóm độc" empty={toxicity.length === 0} missing={missing}>
            <span style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {toxicity.map((item, i) => <ToxicityChip key={i} item={item} />)}
            </span>
          </Fact>
        </div>
      </div>

      {/* duoc-CR-495 — câu mô tả của trang nguồn, ngăn bằng một vạch mảnh (đại ca chốt 29/09: không
          khung màu, không viền trái). Nhóm kháng thường trống ở nguồn — chỉ bày khi có. */}
      {(data.summary || data.resistance) && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '14px 20px', fontSize: 14, lineHeight: 1.6, ...MUTED }}>
          {data.summary && <div><b style={{ color: 'var(--ink)', fontWeight: 600 }}>Tóm tắt sử dụng: </b>{data.summary}</div>}
          {data.resistance && <div style={{ marginTop: data.summary ? 6 : 0 }}><b style={{ color: 'var(--ink)', fontWeight: 600 }}>Quản lý tính kháng: </b>{data.resistance}</div>}
        </div>
      )}
    </div>
  )
}

function Fact({ label, empty, missing, children }: { label: string; empty: boolean; missing: string; children: ReactNode }) {
  return (
    <div style={{ background: '#f4f7fb', borderRadius: 10, padding: '10px 12px', minWidth: 0 }}>
      <div style={{ fontSize: 12, ...MUTED }}>{label}</div>
      <div style={{
        marginTop: 2, fontSize: 14, wordBreak: 'break-word',
        ...(empty ? { fontStyle: 'italic', ...MUTED } : { fontWeight: 600 }),
      }}>
        {empty ? missing : children}
      </div>
    </div>
  )
}

const TOXICITY_TONE: Record<ToxicitySeverity, CSSProperties> = {
  high: { background: 'var(--red-bg)', color: 'var(--red)' },
  medium: { background: 'var(--amber-bg)', color: 'var(--amber)' },
  low: { background: 'var(--green-bg)', color: '#4d7c0f' },
  unknown: { background: '#fff', color: 'var(--muted)' },
}

/** Một nhóm độc: mã (GHS 5) đậm + nhãn mức độc — chữ luôn đi kèm, màu không nói một mình. */
function ToxicityChip({ item }: { item: ToxicityItem }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'baseline', gap: 4, borderRadius: 6, padding: '2px 8px',
      fontSize: 12, fontWeight: 500, ...TOXICITY_TONE[item.severity],
    }}>
      {/* Mã nhóm KHÔNG được bẻ dòng — «GHS» một dòng, «5» một dòng là đọc không ra. */}
      {item.code && <b style={{ whiteSpace: 'nowrap' }}>{item.code}</b>}
      {item.code && item.label && <span aria-hidden>·</span>}
      <span>{item.label}</span>
    </span>
  )
}

function CopyIcon({ value }: { value: string }) {
  async function copy() {
    try {
      await navigator.clipboard.writeText(value)
      toast.success('Đã copy số đăng ký')
    } catch {
      toast.error('Trình duyệt không cho copy — hãy bôi đen rồi Ctrl+C')
    }
  }
  return (
    <button type="button" className="icon-btn" title="Copy số đăng ký" onClick={copy}
      style={{ width: 24, height: 24, margin: '-4px 0' }}>
      <i className="ti ti-copy" style={{ fontSize: 14 }} />
    </button>
  )
}
