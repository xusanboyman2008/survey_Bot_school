from sqlalchemy import Column, Integer, Boolean, String, select, ForeignKey, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+asyncpg://postgres:DJDTHujJufIyqEaRVFCklZwAsuPDKocG@turntable.proxy.rlwy.net:45747/railway"
# DATABASE_URL = "sqlite+aiosqlite:///database.sqlite3"
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "User"
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)  # Changed to BigInteger
    status = Column(Boolean, default=False)

class Survey(Base):
    __tablename__ = "Survey"
    id = Column(Integer, primary_key=True)
    user_tg_id = Column(BigInteger, ForeignKey("User.tg_id"))  # Changed to BigInteger
    first_name = Column(String)
    last_name = Column(String)
    classroom = Column(String)
    subjects = Column(String)
    date = Column(String)
    place = Column(String)
    weekdays = Column(String)
    education_name = Column(String)

async def create_user(tg_id):
    async with async_session() as session:
        async with session.begin():
            data = await session.execute(select(User).where(User.tg_id == tg_id))
            r = data.scalar_one_or_none()
            if r:
                return r.status
            new_user = User(tg_id=tg_id)
            session.add(new_user)
            await session.commit()
            return False


async def get_survey():
    async with async_session() as session:
        result = await session.execute(select(Survey))
        surveys = result.scalars().all()

        # Load all attributes into memory before closing session
        for survey in surveys:
            var = survey.subjects
            var = survey.weekdays
            var = survey.first_name
            var = survey.last_name
            var = survey.classroom
            var = survey.date
            var = survey.place
            var = survey.education_name
            var = survey.user_tg_id

        return surveys

async def change_status(tg_id):
    async with async_session() as session:
        async with session.begin():
            r = await session.execute(select(User).where(User.tg_id == tg_id))
            l = r.scalar_one_or_none()
            if l:
                l.status = True
                return True


async def create_survey(tg_id, first_name, last_name, classroom, subjects, date, place, weekdays, education_name):
    async with async_session() as session:
        async with session.begin():
            r = await session.execute(select(Survey).where(Survey.user_tg_id == tg_id))
            data = r.scalar_one_or_none()

            if data:
                # Update existing survey
                data.first_name = first_name
                data.last_name = last_name
                data.subjects = str(subjects)
                data.classroom = classroom
                data.date = date
                data.place = place
                data.weekdays = str(weekdays)
                data.education_name = education_name
                await change_status(tg_id)
                return data  # No need to commit here, session.begin() handles it

            # Create new survey
            new_survey = Survey(
                user_tg_id=tg_id,
                first_name=first_name,
                last_name=last_name,
                classroom=classroom,
                subjects=str(subjects),
                date=date,
                place=place,
                weekdays=str(weekdays),
                education_name=education_name
            )
            await change_status(tg_id)
            session.add(new_survey)
            await session.commit()
            return

async def init():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # Drop all tables first
        await conn.run_sync(Base.metadata.create_all)  # Recreate tables with fixes
