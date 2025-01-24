import asyncio

from sqladmin import Admin, ModelView
from sqlmodel import SQLModel

from base_model import HasId

pending_admin_views: list[type[ModelView]] = []
admin_instance: Admin | None = None


class FastModelMeta(type(HasId)):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        if name != "FastModel":
            admin_view_class = type(f"{name}Admin", (ModelView,), {"model": cls})

            if admin_instance is not None:
                admin_instance.add_view(admin_view_class)
            else:
                pending_admin_views.append(admin_view_class)
        return cls


class FastModel(HasId, metaclass=FastModelMeta):
    @classmethod
    async def create_tables(cls):
        if cls.engine is None:
            raise Exception(
                "Database engine is not configured. Call FastModel.configure_database() first."
            )
        async with cls.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
