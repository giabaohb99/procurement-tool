// Cờ bật/tắt tính năng theo môi trường (baked lúc build Vite qua build arg).
// Phiếu hỗ trợ (ticket): tắt khi VITE_FEATURE_TICKET=off.
// - prod (docker-compose.production.yml) mặc định "off" → ẩn
// - dev (docker-compose.dev.yml) và chạy local mặc định bật
export const TICKET_ENABLED = import.meta.env.VITE_FEATURE_TICKET !== 'off'
