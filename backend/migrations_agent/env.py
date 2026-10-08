"""Alembic của DỊCH VỤ AI (ai-CR-119) — cùng model, cùng DB URL từ settings, nhưng CHỈ quản các bảng ở
`app/core/agent_tables.py`. Bảng ERP có mặt trong metadata nhưng bị lọc bỏ: autogenerate không bao giờ đề nghị tạo /
xóa chúng ở database `agent_hub`."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.core.all_models  # noqa: F401  (đăng ký toàn bộ bảng vào Base.metadata)
from app.core.agent_tables import is_agent_table
from app.core.base_model import Base
from app.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table":
        return is_agent_table(name)
    table = getattr(obj, "table", None)
    return table is None or is_agent_table(table.name)


def run_migrations_offline() -> None:
    context.configure(url=settings.db_url, target_metadata=target_metadata, literal_binds=True, compare_type=True,
                      include_object=include_object, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.",
                                     poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True,
                          include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
