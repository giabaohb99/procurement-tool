import AttachmentGallery from './AttachmentGallery'

// Section quản lý ẢNH sản phẩm (hiện dưới form ở trang chi tiết product).
// Wrapper mỏng quanh AttachmentGallery (entity="product") — giữ nguyên hành vi trang products.
export default function ProductImages({ productId }: { productId: number }) {
  return (
    <AttachmentGallery
      entity="product"
      entityId={productId}
      title="Ảnh sản phẩm"
      maxHint="JPG, PNG, WEBP · tối đa 5MB/ảnh · có thể chọn nhiều"
    />
  )
}
