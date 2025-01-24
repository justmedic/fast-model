from main import FastModel
import asyncio


FastModel.configure_database("postgresql+asyncpg://postgres:123@localhost/teste")


class Postffff(FastModel, table=True):
    __tablename__ = "postffff"
    title: str


async def start():
    await FastModel.create_tables()


asyncio.run(start())
