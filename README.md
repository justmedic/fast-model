# PREFACE

The project is at a very early stage, but it is already usable. I should clarify that this is my first experience writing libraries and I plan to finish it for a few more months to bring it to perfection. The essence of this library is in super fast deployment of the backend on fastapi with ready-made CRUD operations and admin panel from sqlmodel. This is the very first dev version, but you can already use it for your projects. This library is not suitable for large projects where high code transparency is required, but it will do for small/medium projects where complex database operations are not required. But since fasmodel has sqlmodel (sqlalchemy + pydantic) under the box, you will still be able to use the capabilities of these libraries.


# FastModel

FastModel is a lightweight ORM extension that simplifies database interactions in your Python applications. It provides an easy-to-use interface for common database operations, leveraging the power of SQLModel (https://github.com/tiangolo/sqlmodel) and SQLAlchemy (https://www.sqlalchemy.org/) under the hood.

## Features

- Simplified database configuration: Easily configure your database connection with a single line.
- CRUD operations: Quickly perform Create, Read, Update, and Delete operations with minimal code.
- Asynchronous support: Built-in support for asynchronous database operations using asyncio.
- Automatic table creation: Automatically create database tables from your models.
- Relationship management: Easily define and load relationships between models.

## Getting Started

### Installation

I'll add this to pip in the near future, for now use cloning the repository

### Basic Usage

#### 1. Configure the Database

First, configure the database connection using the configure_database method. This sets up the engine that will be used for all database operations.
```
from fastmodel import FastModel

FastModel.configure_database("postgresql+asyncpg://username:password@localhost/database_name")
```

#### 2. Define Your Models

Create your models by inheriting from FastModel and setting table=True. You can define your fields using standard SQLModel field types.

```
from fastmodel import FastModel
from sqlmodel import Field, Relationship
from typing import List, Optional

class ChannelType(FastModel, table=True):
    __tablename__ = "channel_types"
    name: str

class Channel(FastModel, table=True):
    __tablename__ = "channels"

    url: str
    tg_id: str
    name: str
    sub_channel_id: Optional[int] = Field(default=None, foreign_key="channels.id")
    channel_type_id: Optional[int] = Field(default=None, foreign_key="channel_types.id")
    channel_type: Optional[ChannelType] = Relationship()
```

#### 3. Create Tables

Before performing any operations, you need to create the tables in your database. You can do this using the create_tables method.

```
import asyncio

async def init_db():
    await FastModel.create_tables()

asyncio.run(init_db())

```

#### 4. Perform CRUD Operations

##### Add an Instance

Create a new instance and save it to the database using the add method.

```
async def create_channel():
    channel_type = ChannelType(name="News")
    await channel_type.add()

    channel = Channel(
        url="https://t.me/news_channel",
        tg_id="12345",
        name="News Channel",
        channel_type_id=channel_type.id
    )
    await channel.add()

asyncio.run(create_channel())
```

##### Get an Instance

Retrieve an instance from the database using the get method. You can also load related data using the load_paths parameter. (You can also specify any condition in get on the fields that are in the model.)

```
async def get_channel():
    channel = await Channel.get(id=1, name = "test_name", load_paths=[Channel.channel_type])
    print(channel.name)
    print(channel.channel_type.name)

asyncio.run(get_channel())
```

##### Update an Instance

Update an existing instance using the update method. Pass a dictionary with the fields you want to update.

```
async def update_channel():
    channel = await Channel.get(id=1)
    await channel.update({"name": "Updated News Channel"})

asyncio.run(update_channel())
```

##### Delete an Instance

Delete an instance from the database using the delete method.

```
async def delete_channel():
    channel = await Channel.get(id=1)
    await channel.delete()

asyncio.run(delete_channel())
```

#### 5. Working with Relationships

You can define relationships between your models using sqlmodel.Relationship. To load related data, use the load_paths parameter in your get method.

```
async def get_channel_with_relations():
    channel = await Channel.get(
        id=1,
        load_paths=[
            Channel.channel_type,
            # Add more relationships if needed
        ]
    )
    print(channel.name)
    print(channel.channel_type.name)

asyncio.run(get_channel_with_relations())
```

## Under the Hood

FastModel is built on top of SQLModel (https://github.com/tiangolo/sqlmodel), which combines the power of SQLAlchemy and Pydantic. It leverages SQLAlchemy's asynchronous capabilities to provide non-blocking database operations using asyncio.

- SQLModel: Provides the base for model definitions, combining SQLAlchemy's ORM features with Pydantic's data validation.
- SQLAlchemy: Handles the actual database interactions and query generation.
- AsyncIO: Enables asynchronous execution, allowing your application to perform other tasks while waiting for the database.

## Advantages

- Ease of Use: Simplifies common database operations with straightforward methods.
- Asynchronous Support: Improves performance in applications where non-blocking operations are crucial.
- Flexible Relationships: Easily define and navigate relationships between models.
- Automatic Migrations: Automatically handles table creation based on your models.
- Reduced Boilerplate: Minimizes the amount of code needed to interact with the database.

## API Reference

### FastModel.configure_database(database_url: str)

Configures the database connection for all models.

- database_url: The database URL string.

### FastModel.create_tables()

Asynchronously creates all tables defined by your models in the database.

### add()

Asynchronously saves the current instance to the database. If the instance is new, it will be added. If it already exists (i.e., has an id), it will be updated.

```
async def add(self) -> "FastModel":
    """
    Saves the current instance to the database.
    If the instance is new, it will be added. If it already exists, it will be updated.
    """
```

### update(data: dict)

```
Asynchronously updates the current instance with data from a dictionary and saves it to the database.

async def update(self, data: dict) -> "FastModel":
    """
    Updates the current instance with data from a dictionary and saves it to the database.
    """
```

### get(id: int, load_paths: list = None)

Asynchronously retrieves an instance of the model from the database by id. You can optionally load related data using load_paths.

- id: The primary key of the instance to retrieve.
- load_paths: A list of relationships to load.

```
@classmethod
async def get(cls, id: int, load_paths: list = None) -> Optional["FastModel"]:
    """
    Retrieves an instance from the database by its primary key.
    """
```

### delete()

Asynchronously deletes the current instance from the database.

```
async def delete(self):
    """
    Deletes the current instance from the database.
    """
```

## Example Project

Below is a complete example demonstrating how to use FastModel in your application.

```
from fastmodel import FastModel
from sqlmodel import Field, Relationship
from typing import Optional
import asyncio

# Configure the database
FastModel.configure_database("postgresql+asyncpg://postgres:123@localhost/testdb")

# Define your models
class ChannelType(FastModel, table=True):
    __tablename__ = "channel_types"
    name: str

class Channel(FastModel, table=True):
    __tablename__ = "channels"

    url: str
    tg_id: str
    name: str
    channel_type_id: Optional[int] = Field(default=None, foreign_key="channel_types.id")
    channel_type: Optional[ChannelType] = Relationship()

# Initialize the database
async def init_db():
    await FastModel.create_tables()

# Create and add instances
async def create_instances():
    channel_type = ChannelType(name="Technology")
    await channel_type.add()

    channel = Channel(
        url="https://t.me/tech_channel",
        tg_id="54321",
        name="Tech Channel",
        channel_type_id=channel_type.id
    )
    await channel.add()

# Retrieve and update instances
async def retrieve_and_update():
    # Retrieve the channel and load related channel_type
    channel = await Channel.get(id=1, load_paths=[Channel.channel_type])
    print(f"Channel Name: {channel.name}")

ChatGPT + Midjourney, [24.01.2025 16:49]

    print(f"Channel Type: {channel.channel_type.name}")

    # Update the channel name
    await channel.update({"name": "Updated Tech Channel"})
    print(f"Updated Channel Name: {channel.name}")

# Delete an instance
async def delete_instance():
    channel = await Channel.get(id=1)
    await channel.delete()
    print("Channel deleted.")

# Run the asynchronous functions
async def main():
    await init_db()
    await create_instances()
    await retrieve_and_update()
    await delete_instance()

asyncio.run(main())
```

## Conclusion

FastModel provides a convenient and efficient way to interact with your database using asynchronous operations. By reducing boilerplate code and simplifying model definitions, it allows you to focus on the core functionality of your application.

For more information and advanced usage, please refer to the official documentation (link to be provided).

## License

This project is licensed under the MIT License.

---

Note: This is a basic overview to get you started with FastModel. For detailed usage and advanced configurations, please consult the full documentation.
