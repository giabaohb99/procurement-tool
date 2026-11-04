import { apiGet, apiPut } from '@/core/api'

/**
 * PHIÊN BẢN ĐANG CHẠY + CÓ GÌ MỚI — `/api/system/version`, `/api/system/release-notes` (bao-CR-722).
 *
 * Nguồn là tệp `backend/app/data/release_notes.json` trong image máy chủ: "phiên bản" = đợt mới nhất của tệp,
 * commit / giờ build do Dockerfile bơm lúc build. Giao diện chỉ đọc; nhãn loại thay đổi do backend trả.
 *
 * "Đã xem" lưu ở tùy chọn cá nhân (`/api/me/preferences`, khóa `release_seen_version`) — một chấm đỏ nhỏ ở chân
 * menu và mục tài khoản khi phiên bản đang chạy khác bản đã xem.
 */

export interface ReleaseVersion {
  version: string
  release_date: string
  release_title: string
  /** Rỗng = image build không truyền BUILD_COMMIT — màn ghi "không rõ", không đoán. */
  commit: string
  built_at: string
  environment: string
}

export interface ReleaseNote {
  module: string
  kind: string
  kind_label: string
  cr: string
  text: string
}

export interface ReleaseEntry {
  version: string
  date: string
  title: string
  notes: ReleaseNote[]
  remarks: string[]
}

export interface ReleaseNotesResult {
  releases: ReleaseEntry[]
  modules: string[]
  kinds: { code: string; label: string }[]
  version: ReleaseVersion
}

export const RELEASE_SEEN_PREFERENCE_KEY = 'release_seen_version'

export function fetchReleaseVersion() {
  return apiGet<ReleaseVersion>('/api/system/version')
}

export function fetchReleaseNotes(limit = 20) {
  return apiGet<ReleaseNotesResult>(`/api/system/release-notes?limit=${limit}`)
}

/** Ghi "đã xem tới bản này" — im lặng: hỏng mạng thì lần mở sau ghi lại, không toast. */
export function saveReleaseSeen(version: string) {
  return apiPut<Record<string, string>>(
    '/api/me/preferences',
    { values: { [RELEASE_SEEN_PREFERENCE_KEY]: version } },
    { _silent: true } as never,
  )
}
