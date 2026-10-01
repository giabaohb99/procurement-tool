// Thẻ «Thông tin đăng ký» của trang chi tiết thuốc BVTV — làm lại 01/10/2026, đồng bộ bản v2
// (`frontend-v2/.../customs-pesticide-info-card.tsx`). Trước đây chín cặp nhãn – giá trị dàn đều một
// lưới, hoạt chất nặng ngang «Lĩnh vực», nhóm độc là một dòng chữ dài (đại ca chê khó nhìn). Nay hai
// khối «Đăng ký» / «Phân loại», mỗi dòng nhãn trái – giá trị phải; số đăng ký có nút chép, thời hạn
// kèm thời gian còn lại, nhóm độc tách thành thẻ theo mức độc.
import type { CSSProperties, ReactNode } from 'react'
import { toast } from '../toast'
import { fmtDate } from './customs-shared'
import {
  describeRemainingTerm,
  parsePesticideToxicity,
  toSentenceCaseIfShouting,
  type ToxicityItem,
  type ToxicitySeverity,
} from '../../utils/customs-pesticide-display'

const SECTION_TITLE: CSSProperties = {
  fontSize: 11, fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase',
  color: 'var(--muted)', margin: '0 0 4px',
}

export default function CustomsPesticideInfoCard({ data }: { data: any }) {
  const manual = !!data.is_manual
  const term = data.registered_on || data.expires_on
    ? `${fmtDate(data.registered_on)} – ${fmtDate(data.expires_on)}` : ''
  const remaining = describeRemainingTerm(data.expires_on, new Date())
  const toxicity = parsePesticideToxicity(data.toxicity)

  return (
    <div className="card" style={{ padding: 0, marginBottom: 16, overflow: 'hidden' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))' }}>
        <Section title="Đăng ký">
          <Row label="Hoạt chất" manual={manual} empty={!data.active_ingredient}>
            <span style={{ fontWeight: 700 }}>{data.active_ingredient}</span>
          </Row>
          <Row label="Hàm lượng" manual={manual} empty={!data.concentration}>{data.concentration}</Row>
          <Row label="Số đăng ký" manual={manual} empty={!data.registration_no}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>{data.registration_no}</span>
              <CopyIcon value={data.registration_no} />
            </span>
          </Row>
          <Row label="Thời hạn" manual={manual} empty={!term}>
            {term}
            {remaining && (
              <span style={{
                display: 'block', marginTop: 2, fontSize: 12,
                color: remaining === 'Đã hết hạn' ? 'var(--red)' : 'var(--muted)',
                fontWeight: remaining === 'Đã hết hạn' ? 600 : 400,
              }}>{remaining}</span>
            )}
          </Row>
          <Row label="Công ty đăng ký" manual={manual} empty={!data.registrant}>{data.registrant}</Row>
        </Section>

        <Section title="Phân loại" leftBorder>
          <Row label="Phân nhóm" manual={manual} empty={!data.pest_group}>{data.pest_group}</Row>
          <Row label="Lĩnh vực" manual={manual} empty={!data.sector}>{toSentenceCaseIfShouting(data.sector || '')}</Row>
          <Row label="Nhóm độc" manual={manual} empty={toxicity.length === 0}>
            <span style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {toxicity.map((item, i) => <ToxicityChip key={i} item={item} />)}
            </span>
          </Row>
          <Row label="Nhóm kháng" manual={manual} empty={!data.resistance}>{data.resistance}</Row>
        </Section>
      </div>

      {/* duoc-CR-495 — câu mô tả của trang nguồn, DƯỚI phần thông tin, ngăn bằng một vạch mảnh
          (đại ca chốt 29/09: không khung màu, không viền trái). */}
      {data.summary && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '14px 20px' }}>
          <div style={SECTION_TITLE}>Tóm tắt sử dụng</div>
          <div style={{ fontSize: 14, lineHeight: 1.6 }}>{data.summary}</div>
        </div>
      )}
    </div>
  )
}

function Section({ title, leftBorder, children }: { title: string; leftBorder?: boolean; children: ReactNode }) {
  return (
    <section style={{ padding: '14px 20px', minWidth: 0, borderLeft: leftBorder ? '1px solid var(--border)' : undefined }}>
      <div style={SECTION_TITLE}>{title}</div>
      <dl style={{ margin: 0 }}>{children}</dl>
    </section>
  )
}

/** Trống thì ghi rõ: thuốc từ bản cào là «Nguồn không ghi», thuốc tự thêm là «Chưa nhập». */
function Row({ label, manual, empty, children }: { label: string; manual: boolean; empty: boolean; children: ReactNode }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '136px minmax(0, 1fr)', gap: 12, alignItems: 'baseline',
      padding: '9px 0', borderBottom: '1px solid #eef2f7', fontSize: 14,
    }}>
      <dt style={{ color: 'var(--muted)' }}>{label}</dt>
      <dd style={{
        margin: 0, wordBreak: 'break-word',
        ...(empty ? { fontStyle: 'italic', color: 'var(--muted)' } : { fontWeight: 500 }),
      }}>
        {empty ? (manual ? 'Chưa nhập' : 'Nguồn không ghi') : children}
      </dd>
    </div>
  )
}

const TOXICITY_TONE: Record<ToxicitySeverity, CSSProperties> = {
  high: { background: 'var(--red-bg)', color: 'var(--red)' },
  medium: { background: 'var(--amber-bg)', color: 'var(--amber)' },
  low: { background: 'var(--green-bg)', color: '#4d7c0f' },
  unknown: { background: '#f1f5f9', color: 'var(--muted)' },
}

/** Một nhóm độc: mã (GHS 5) đậm + nhãn mức độc — chữ luôn đi kèm, màu không nói một mình. */
function ToxicityChip({ item }: { item: ToxicityItem }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4, borderRadius: 6, padding: '2px 8px',
      fontSize: 12, fontWeight: 500, ...TOXICITY_TONE[item.severity],
    }}>
      {item.code && <b>{item.code}</b>}
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
