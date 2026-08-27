import { ImageLightbox, useImageLightbox } from '@/shared/ui/image-lightbox'
import { cn } from '@/shared/utils/cn'

import type { ForumImage } from '../types/forum-post'
import { isVideoMedia } from '../utils/pick-media-files'

interface PostImageGridProps {
  images: ForumImage[]
}

/**
 * Khối media của bài viết. ẢNH xếp lưới kiểu bảng tin: 1 tấm nguyên khổ · 2 tấm
 * chia đôi · 3 tấm = 1 ngang + 2 vuông · từ 4 tấm là ô 2x2, dư bao nhiêu đè
 * «+N» lên ô cuối; bấm ảnh nào mở đèn chiếu tại đúng ảnh đó. VIDEO (D-Q3) đứng
 * riêng dưới lưới, mỗi clip nguyên khổ ngang kèm nút phát của trình duyệt —
 * không nhét vào lưới vì ô vuông cắt mất khung hình và đèn chiếu chỉ chiếu ảnh.
 */
export function PostImageGrid({ images }: PostImageGridProps) {
  const lightbox = useImageLightbox()
  const photos = images.filter((img) => !isVideoMedia(img.filename, img.content_type))
  const videos = images.filter((img) => isVideoMedia(img.filename, img.content_type))
  if (images.length === 0) return null

  const shown = photos.slice(0, 4)
  const hidden = photos.length - shown.length

  return (
    <>
      {photos.length > 0 && (
        <div className={cn('mt-3 grid gap-0.5', photos.length > 1 && 'grid-cols-2')}>
          {shown.map((img, i) => {
            // Tấm ngang trải hai cột: tấm duy nhất, hoặc tấm đầu của bộ ba.
            const wide = photos.length === 1 || (photos.length === 3 && i === 0)
            return (
              <button
                key={img.link_id}
                type="button"
                aria-label={`Xem ảnh ${i + 1}`}
                onClick={() => lightbox.openAt(i)}
                className={cn(
                  'relative block overflow-hidden bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                  wide && 'col-span-2',
                  photos.length > 1 && (wide ? 'aspect-[2/1]' : 'aspect-square'),
                )}
              >
                <img
                  src={img.thumb_url || img.url}
                  alt={img.filename}
                  loading="lazy"
                  className={cn(
                    photos.length === 1
                      ? // Tấm duy nhất giữ nguyên tỷ lệ gốc, chỉ chặn trần chiều cao.
                        'max-h-[480px] w-full object-cover'
                      : 'size-full object-cover',
                  )}
                />
                {hidden > 0 && i === shown.length - 1 && (
                  <span className="absolute inset-0 grid place-items-center bg-black/50 text-2xl font-semibold text-white">
                    +{hidden}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      )}

      {videos.map((video) => (
        <video
          key={video.link_id}
          src={video.url}
          controls
          playsInline
          preload="metadata"
          className="mt-3 max-h-[480px] w-full bg-black"
        >
          <track kind="captions" />
        </video>
      ))}

      {photos.length > 0 && (
        <ImageLightbox
          images={photos.map((img) => ({ url: img.url, name: img.filename }))}
          {...lightbox.bind}
        />
      )}
    </>
  )
}
