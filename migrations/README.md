# Migrations (Alembic)

Phase 0 dùng create_all (tự tạo bảng khi seed). Khi cần version DB:
  alembic init -t generic .
  alembic revision --autogenerate -m "init"
  alembic upgrade head
