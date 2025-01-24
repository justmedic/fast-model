from main import FastModel
import asyncio


FastModel.configure_database("postgresql+asyncpg://postgres:123@localhost/teste")


class Postffff(FastModel, table=True):
    __tablename__ = "postffff"
    title: str


async def start():
    # await FastModel.create_tables()
    a: Postffff = await Postffff.get(title="df", suspend_error=True)
    print(a)
    await a.delete()


asyncio.run(start())
