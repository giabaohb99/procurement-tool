import { formatDateTime } from '@/shared/utils/format-date'

import type { ReleaseEntry, ReleaseVersion } from './release-api'

/** Dòng "đang chạy": phiên bản, commit, giờ build, môi trường — thiếu thứ nào ghi "không rõ", không đoán. */
export function runningVersionText(v: ReleaseVersion | undefined, uiCommit: string): string {
  if (!v) return 'Đang tải phiên bản...'
  const parts = [`Phiên bản ${v.version}`, `máy chủ ${v.commit || 'không rõ'}`]
  if (uiCommit && uiCommit !== v.commit) parts.push(`giao diện ${uiCommit}`)
  parts.push(v.built_at ? `build lúc ${formatDateTime(v.built_at) || v.built_at}` : 'giờ build không rõ')
  if (v.environment) parts.push(v.environment)
  return parts.join(' · ')
}

/** Lọc theo phân hệ: giữ đợt có ít nhất một mục khớp, trong đợt chỉ giữ mục khớp. */
export function filterReleases(releases: ReleaseEntry[], module: string): ReleaseEntry[] {
  if (!module) return releases
  return releases
    .map((r) => ({ ...r, notes: r.notes.filter((n) => n.module === module) }))
    .filter((r) => r.notes.length > 0)
}
