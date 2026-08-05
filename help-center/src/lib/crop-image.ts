// Cắt ảnh bằng canvas cho ô chọn icon: nhận vùng cắt do react-easy-crop trả về
// (toạ độ theo pixel ẢNH GỐC) rồi xuất ra File PNG vuông đã thu nhỏ, sẵn sàng upload.

/** Vùng cắt theo pixel của ảnh gốc — trùng kiểu `Area` của react-easy-crop. */
export interface CropArea {
  x: number
  y: number
  width: number
  height: number
}

/** Cạnh ảnh icon sau khi cắt. 256px đủ nét cho ô 48px ở màn hình 2x mà file vẫn nhẹ. */
const OUTPUT_SIZE = 256

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Không đọc được ảnh'))
    img.src = src
  })
}

/**
 * Cắt `imageSrc` theo `area` rồi trả về File PNG vuông cạnh OUTPUT_SIZE.
 *
 * Giữ nền trong suốt (PNG) để icon hợp với nền thẻ sáng lẫn nền teal nhạt.
 */
export async function cropImageToFile(
  imageSrc: string,
  area: CropArea,
  fileName = 'icon.png',
): Promise<File> {
  const image = await loadImage(imageSrc)

  const canvas = document.createElement('canvas')
  canvas.width = OUTPUT_SIZE
  canvas.height = OUTPUT_SIZE

  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Trình duyệt không hỗ trợ canvas')

  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(
    image,
    area.x, area.y, area.width, area.height,   // vùng lấy từ ảnh gốc
    0, 0, OUTPUT_SIZE, OUTPUT_SIZE,            // vẽ full khung canvas
  )

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
  if (!blob) throw new Error('Không tạo được ảnh sau khi cắt')

  return new File([blob], fileName, { type: 'image/png' })
}
