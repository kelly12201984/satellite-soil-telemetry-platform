# alembic/env.py
from __future__ import annotations

from logging.config import fileConfig
from configparser import NoSectionError, NoOptionError
from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config
config = context.config

# Optional logging (skip if sections not present)
try:
    if config.config_file_name:
        fileConfig(config.config_file_name, disable_existing_loggers=False)
except (KeyError, NoSectionError, NoOptionError):
    pass

# --- Load app settings and metadata ---
from app.settings import settings  # type: ignore
from app.db.base import Base       # type: ignore
from app import models             # ensure models get imported/registered

target_metadata = Base.metadata

# Point Alembic at the same DB URL the app uses
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

# ----- Limit autogenerate to our app tables only -----
APP_TABLES = {"device", "device_config", "message", "reading"}

def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in APP_TABLES
    if type_ == "index":
        tbl = getattr(obj, "table", None)
        return getattr(tbl, "name", None) in APP_TABLES
    return True
# -----------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
        include_object=include_object,  # <-- key line
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
            include_object=include_object,  # <-- key line
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
