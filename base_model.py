import hashlib
import os
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator, ClassVar, TypeVar

# from db.sessions import get_session
from fastapi.exceptions import HTTPException
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import ONETOMANY, joinedload, selectinload, sessionmaker
from sqlmodel import (
    Field,
    SQLModel,
    and_,
)


class HasId(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    __table_args__ = {"schema": "main"}

    # Переменные класса для хранения конфигурации базы данных
    database_url: ClassVar[str] = ""
    engine: ClassVar[create_async_engine] = None
    async_session_factory: ClassVar[sessionmaker] = None

    @classmethod
    def configure_database(cls, database_url: str):
        cls.database_url = database_url
        cls.engine = create_async_engine(
            cls.database_url,
            echo=True,
            future=True,
            pool_size=20,
            max_overflow=20,
            pool_recycle=3600,
        )
        cls.async_session_factory = sessionmaker(
            cls.engine,
            expire_on_commit=False,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
        )

    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        async with cls.async_session_factory() as session:
            yield session

    @classmethod
    async def get_all(cls) -> list["T"]:
        async with cls.get_session() as session:
            result = await session.execute(select(cls).order_by(cls.id))
        return result.unique().scalars().all()

    @classmethod
    async def get(
        cls,
        load_paths: list[str | tuple[str, ...]] | None = None,
        suspend_error: bool = False,
        **filters,
    ) -> "T":
        """
        Получает объект модели по заданным фильтрам, с возможностью загрузки связанных данных.

        Пример использования:

            attempt = await Attempt.get(
                id=attempt_id,
                load_paths=[
                    Attempt.attempt_type,
                    (Attempt.billings, Billing.payments),
                    (Attempt.billings, Billing.billing_documents),
                ],
            )

        Параметры:
        - load_paths: список отношений для загрузки (можно использовать строки или кортежи для вложенных отношений).
        - suspend_error: если True, не выбрасывает исключение, а возвращает None, если объект не найден.
        - **filters: значения полей для фильтрации.
        """
        async with cls.get_session() as session:
            session: AsyncSession

            def build_load_path(load_path):
                """
                Рекурсивно строит loader для загрузки связей.

                :param load_path: Атрибут модели или последовательность атрибутов
                :return: loader для использования в опциях запроса
                """
                attrs = load_path if isinstance(load_path, (list, tuple)) else [load_path]

                if not attrs:
                    return None

                attr = attrs[0]

                # Проверка, что attr является релейшншипом
                if not hasattr(attr, "property") or not hasattr(attr.property, "direction"):
                    msg = "Элемент load_path должен быть релейшншипом модели"
                    raise TypeError(msg)

                is_uselist = getattr(attr.property, "uselist", False)
                loader = selectinload(attr) if is_uselist else joinedload(attr)

                if len(attrs) > 1:
                    nested_loader = build_load_path(attrs[1:])
                    loader = loader.options(nested_loader)

                return loader

            options = []
            if load_paths:
                options.extend([build_load_path(lp) for lp in load_paths])
            stmt = select(cls)
            if options:
                stmt = stmt.options(*options)

            if filters:
                for key in filters.keys():
                    if not hasattr(cls, key):
                        message = f"Модель {cls.__name__} не содержит поле {key}"
                        if not suspend_error:
                            raise HTTPException(status_code=400, detail=message)
                        else:
                            raise AttributeError(message)

                stmt = stmt.where(*(getattr(cls, key) == value for key, value in filters.items()))
            else:
                message = f"Не указаны фильтры для поиска {cls.__name__}"
                if not suspend_error:
                    raise HTTPException(status_code=400, detail=message)
                else:
                    raise ValueError(message)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()

            if obj:
                return obj
            if not suspend_error:
                raise HTTPException(status_code=404, detail=f"Не найден ресурс {cls.__name__}")
            return None

    async def delete(self) -> bool:
        async with self.get_session() as session:
            session: AsyncSession

            is_not_relations_empty = await self.__check_for_related_records(session)
            if is_not_relations_empty:
                raise HTTPException(status_code=400, detail=f"{is_not_relations_empty}")
            try:
                await session.delete(self)
                await session.commit()
            except Exception as e:
                table_name = getattr(self.__class__, "rus_table_name", self.__class__.__name__)
                raise HTTPException(
                    status_code=400,
                    detail=f"Не удалось удалить {table_name} - {e}",
                )
            return True

    async def __check_for_related_records(self, session: AsyncSession) -> list[str] | None:
        """
        Функция проверяет наличие связанных записей для данной записи модели.
        """
        mapper = inspect(self.__class__)
        related_records_info = []

        for rel in mapper.relationships:
            if rel.direction == ONETOMANY:
                related_model = rel.mapper.class_

                local_remote_pairs = rel.local_remote_pairs
                local_columns = [local for local, _ in local_remote_pairs]
                remote_columns = [remote for _, remote in local_remote_pairs]

                conditions = []
                for local_col, remote_col in zip(local_columns, remote_columns):
                    value = getattr(self, local_col.name)
                    condition = remote_col == value
                    conditions.append(condition)

                stmt = select(related_model).where(and_(*conditions)).limit(1)
                result = await session.execute(stmt)
                related_record = result.unique().scalar_one_or_none()

                if related_record:
                    related_pk = {
                        key.name: getattr(related_record, key.name)
                        for key in inspect(related_model).primary_key
                    }
                    related_pk_str = ", ".join(
                        f"{key}={value}" for key, value in related_pk.items()
                    )
                    related_table_name = getattr(
                        related_model, "rus_table_name", related_model.__name__
                    )
                    related_records_info.append(
                        f"Найдена связанная запись в модели '{related_model.__name__} ({related_table_name})' ({related_pk_str})"
                    )

        if related_records_info:
            return related_records_info
        return None

    async def add(self) -> "T":
        """
        Сохраняет текущий экземпляр в базе данных.
        Если экземпляр новый, он будет добавлен. Если он уже существует, он будет обновлен.
        """
        async with self.get_session() as session:
            session: AsyncSession
            session.add(self)
            try:
                await session.commit()
                await session.refresh(self)
            except Exception as e:
                table_name = getattr(self.__class__, "rus_table_name", self.__class__.__name__)
                raise HTTPException(
                    status_code=400,
                    detail=f"Не удалось сохранить {table_name} - {e}",
                )
        return self

    async def update(self, data: dict) -> "T":
        """
        Обновляет текущий экземпляр данными из словаря и сохраняет его в базе данных.
        """
        for key, value in data.items():
            setattr(self, key, value)
        return await self.add()


T = TypeVar("T", bound=HasId)
