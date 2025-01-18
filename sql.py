from datetime import datetime

from alembic import op
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import String,  Integer, Column,  DateTime
from sqlalchemy import func
from sqlalchemy import select, update, delete

database_url = 'sqlite+aiosqlite:///db.sqlite3' # 'postgresql+asyncpg://romblin@localhost/db.sqlite3'
engine = create_async_engine(url=database_url)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)

# with op.batch_alter_table("raffle") as batch_op:
#     batch_op.add_column(Column('time_start', String(64)))
#     batch_op.drop_column('time_start')

# базовый класс
class Base(AsyncAttrs, DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True)
    first_name = Column(String(64))
    user_name = Column(String(64), nullable=True)
    channel = Column(String, nullable=True)


class Channel(Base):
    __tablename__ = "channel"
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(Integer)
    name = Column(String(64))
    channel_telegram_id = Column(String(64), nullable=True)


class Participant(Base):
    __tablename__ = "participant"
    id = Column(Integer, primary_key=True)
    channel_telegram_id = Column(String(64), nullable=True)
    participant_telegram_id = Column(Integer)
    participant_name = Column(String(64))
    participant_user_name = Column(String(64))
    post_id = Column(String(64), nullable=True)


class Raffle(Base):
    __tablename__ = "raffle"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    text_raffle = Column(String, nullable=True)
    media_raffle = Column(String(64), nullable=True)
    text_button = Column(String(64))
    channel_for_subscription = Column(String, nullable=True)
    number_winners = Column(Integer)
    status = Column(String(64))
    number_participants = Column(Integer)
    pablish_channal = Column(String)
    time_start = Column(String(64))
    time_end = Column(String(64), nullable=True)
    max_participants = Column(Integer, nullable=True)


class BaseDAO:
    model = None

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        """
        Асинхронно находит и возвращает один экземпляр модели по указанным критериям или None.

        Аргументы:
            **filter_by: Критерии фильтрации в виде именованных параметров.

        Возвращает:
            Экземпляр модели или None, если ничего не найдено.
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)

            result = await session.execute(query)
            return result.scalars().all()#.scalar_one_or_none()

    @classmethod
    async def find_all(cls, **filter_by):
        """
        Асинхронно находит и возвращает все экземпляры модели, удовлетворяющие указанным критериям.

        Аргументы:
            **filter_by: Критерии фильтрации в виде именованных параметров.

        Возвращает:
            Список экземпляров модели.
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        """
        Асинхронно находит и возвращает один экземпляр модели по указанным критериям или None.

        Аргументы:
            data_id: Критерии фильтрации в виде идентификатора записи.

        Возвращает:
            Экземпляр модели или None, если ничего не найдено.
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def add(cls, **values):
        """
        Асинхронно создает новый экземпляр модели с указанными значениями.

        Аргументы:
            **values: Именованные параметры для создания нового экземпляра модели.

        Возвращает:
            Созданный экземпляр модели.
        """
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return new_instance

    @classmethod
    async def update(cls, id, **values):
        """
        Асинхронно обновляет экземпляры модели с указанными значениями.

        Аргументы:
            telegram_id: id пользователя в программе телеграм
            **values: Именованные параметры для обновления экземпляра модели.
        """
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values)

                stmt = (
                    update(cls.model).
                    filter_by(id=id).
                    values(**values))
                await session.execute(stmt)
                await session.commit()
                # try:
                #     await session.commit()
                # except SQLAlchemyError as e:
                #     await session.rollback()
                #     raise e
                # return session.is_modified(new_instance)

    @classmethod
    async def delete(cls,  **values):
        """
                Асинхронно удаляет экземпляры модели с указанными значениями.

                Аргументы:
                    **values: Именованные параметры для удаления экземпляра модели.

                """
        async with async_session_maker() as session:
            async with session.begin():
                stmt = delete(cls.model).filter_by(**values)  # where
                await session.execute(stmt)
                await session.commit()


class UserDAO(BaseDAO):
    model = User


class RaffleDAO(BaseDAO):
    model = Raffle


class ChannelDAO(BaseDAO):
    model = Channel


class ParticipantDAO(BaseDAO):
    model = Participant
