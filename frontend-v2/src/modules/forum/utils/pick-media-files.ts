/** Trần của một bài viết — khớp `FILE_POLICY` entity `forum_post` phía backend. */
export const MAX_MEDIA_PER_POST = 10
export const MAX_MEDIA_MB = 50

// Khớp bộ đuôi của `backend/app/core/file_registry.py`: nhận khi content-type
// là image/*, video/* HOẶC đuôi tệp nằm trong bộ này (tệp kéo từ Zalo/ảnh chụp
// màn hình đôi khi mất content-type). Video chỉ mp4/webm — hai định dạng
// `<video>` mọi trình duyệt phát được (D-Q3 chốt 27/08/2026).
const IMAGE_EXTENSIONS = new Set(['jpg', 'jpeg', 'png', 'webp'])
const VIDEO_EXTENSIONS = new Set(['mp4', 'webm'])

export interface PickMediaResult {
  accepted: File[]
  /** Mỗi lý do một câu, sẵn cho toast — rỗng nghĩa là nhận hết. */
  errors: string[]
}

function extOf(name: string): string {
  return name.split('.').pop()?.toLowerCase() ?? ''
}

/** Tệp này là video? Dùng chung cho cả File lúc chọn lẫn media đã đăng trên thẻ bài. */
export function isVideoMedia(filename: string, contentType = ''): boolean {
  if (contentType.startsWith('video/')) return true
  return VIDEO_EXTENSIONS.has(extOf(filename))
}

function isMedia(file: File): boolean {
  if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
    // content-type video lạ (mov/avi…) vẫn phải khớp đuôi backend cho phép.
    return !file.type.startsWith('video/') || VIDEO_EXTENSIONS.has(extOf(file.name))
  }
  const ext = extOf(file.name)
  return IMAGE_EXTENSIONS.has(ext) || VIDEO_EXTENSIONS.has(ext)
}

/**
 * Lọc danh sách tệp người dùng vừa chọn/dán/kéo vào bài: bỏ tệp không phải
 * ảnh/video, bỏ tệp quá 50MB, và cắt ở trần 10 tệp/bài (tính cả `existingCount`
 * đã đính). Chặn ở đây để người dùng biết ngay, không phải chờ backend 400.
 */
export function pickMediaFiles(files: File[], existingCount: number): PickMediaResult {
  const errors: string[] = []

  const rejected = files.filter((file) => !isMedia(file))
  if (rejected.length) {
    errors.push(
      `Chỉ đính được ảnh (jpg, png, webp) hoặc video (mp4, webm) — đã bỏ qua ${rejected.length} tệp khác.`,
    )
  }

  const tooBig = files.filter((file) => isMedia(file) && file.size > MAX_MEDIA_MB * 1024 * 1024)
  if (tooBig.length) {
    errors.push(`Mỗi tệp tối đa ${MAX_MEDIA_MB}MB — đã bỏ qua ${tooBig.length} tệp quá nặng.`)
  }

  const usable = files.filter((file) => isMedia(file) && file.size <= MAX_MEDIA_MB * 1024 * 1024)
  const room = Math.max(0, MAX_MEDIA_PER_POST - existingCount)
  if (usable.length > room) {
    errors.push(
      `Mỗi bài tối đa ${MAX_MEDIA_PER_POST} ảnh/video — đã bỏ qua ${usable.length - room} tệp thừa.`,
    )
  }

  return { accepted: usable.slice(0, room), errors }
}
