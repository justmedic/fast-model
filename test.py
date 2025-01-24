from main import FastModel
import asyncio
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship


FastModel.configure_database("postgresql+asyncpg://postgres:123@localhost/teste")


class ChanelType(FastModel, table=True):
    __tablename__ = "chanel_types"
    name: str


class Chanel(FastModel, table=True):
    __tablename__ = "chanels"

    url: str
    tg_id: str
    name: str
    sub_chanel_id: int | None = Field(default=None, foreign_key="main.chanels.id")
    chanel_type_id: int | None = Field(default=None, foreign_key="main.chanel_types.id")
    chanel_type: "ChanelType" = Relationship(
        sa_relationship=RelationshipProperty(
            primaryjoin="ChanelType.id==Chanel.chanel_type_id",
        ),
    )


async def start():
    # await FastModel.create_tables()
    a: Chanel = await Chanel.get(id=1, load_paths=[Chanel.chanel_type])
    print(a)
    print(a.chanel_type.name)


asyncio.run(start())
