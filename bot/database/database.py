from sqlalchemy.exc import IntegrityError
from models.user import User
from models.portfolio import Portfolio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from aiogram.types import Message
from datetime import datetime
from repo import TickerPortfolio, JsonSerializer

async def db_add_to_db(item, message:Message, session:AsyncSession):
    """Добавление сущности в бд"""
    
    session.add(item)
    try:
            
        await session.commit()
        await session.refresh(item)
        return item
    except IntegrityError as ex:
        await session.rollback()
        await message.answer('Произошла ошибка.')
        await message.answer(ex)
    
# регистрация юзера
async def db_register_user(message:Message, session:AsyncSession):
    print(f"start {message.from_user.id}")
    existing_user = await db_get_user_by_tg_id(message.from_user.id, session=session)
    if existing_user:
        return
    username = message.from_user.username if message.from_user.username else 'username'

    name = message.from_user.full_name if message.from_user.username else 'name'
    
    user = User(tg_id=int(message.from_user.id), username=username, name=name)

    empty_dict =  {
    "ir_stock": [],
    "crypto": [],
    "ru_stock": [],
    "ir_index": [],
    "ru_index": []
    }

    portfolio = Portfolio(user=user, serialized_portfolio=JsonSerializer.cast_to_string(empty_dict))
    
    session.add(user)
    session.add(portfolio)
    
    try:
        print(123)
        await session.commit()
        await session.refresh(user)
        await session.refresh(portfolio)
        return True
    except IntegrityError:
        await session.rollback()
        return False
    

async def db_update_portfolio(session: AsyncSession, portfolio_upd: TickerPortfolio, user_tg_id: int):
    existing_user = await db_get_user_by_tg_id(user_tg_id, session=session)
    if existing_user:
        portfolio_from_db = await db_get_portfolio_by_user_id(existing_user.id, session)
        if(portfolio_from_db):
            portfolio_dict = JsonSerializer.load_object_from_string(portfolio_from_db.serialized_portfolio)
            portfolio = await TickerPortfolio.desirialize_from_dict(portfolio_dict)
            await portfolio.update_portfolio(portfolio_upd)
            serialized = await portfolio.serialize_to_string()
            portfolio_from_db.serialized_portfolio = serialized
        try:
            await session.commit()
            await session.refresh(portfolio_from_db)
            return True
        except IntegrityError:
            await session.rollback()
            return False
        
async def db_update_portfolio_dict(session: AsyncSession, portfolio: Portfolio, new_portfolio_dict: dict):
    serialized = JsonSerializer.cast_to_string(new_portfolio_dict)
    portfolio.serialized_portfolio = serialized
    try:
        await session.commit()
        await session.refresh(portfolio)
        return True
    except IntegrityError:
        await session.rollback()
        return False

async def db_get_all_users(message:Message, session:AsyncSession):

    """ получение всех юзеров """
    
    sql = select(User)
    users_sql = await session.execute(sql)
    users = users_sql.scalars()
    
    users_list = '\n'.join([f'{index+1}. {item.tg_id}' for index, item in enumerate(users)])    
    
    return users_list

async def db_get_user_by_tg_id(tg_id:int, session:AsyncSession):
    sql = select(User).where(User.tg_id==tg_id)
    user_sql = await session.execute(sql)
    return user_sql.scalar()

async def db_get_portfolio_by_user_id(user_id, session: AsyncSession):
    sql = select(Portfolio).where(Portfolio.id==user_id)
    portfolio_sql = await session.execute(sql)
    return portfolio_sql.scalar()


async def db_get_portfolio_by_user_tg_id(tg_id: int, session: AsyncSession):
    sql = select(User).where(User.tg_id==tg_id)
    user_sql = await session.execute(sql)
    user = user_sql.scalar()
    if(user):
        sql = select(Portfolio).where(Portfolio.id==user.id)
        portfolio_sql = await session.execute(sql)
        return portfolio_sql.scalar()
    return None

async def db_get_portfolio_by_user(session: AsyncSession, user: User):
    sql = select(Portfolio).where(Portfolio.id==user.id)
    portfolio_sql = await session.execute(sql)
    return portfolio_sql.scalar()

async def db_get_all_users_with_enabled_notifications(session: AsyncSession) -> list[User]:
    sql = select(User).where(User.notifications_enabled==True)
    users_sql = await session.execute(sql)
    return users_sql.all()

async def db_set_user_notifications(session: AsyncSession, user: User, value:bool = True):
    user.notifications_enabled = value
    try:
        await session.commit()
        await session.refresh(user)
        return True
    except IntegrityError:
        await session.rollback()
        return False
    
async def db_set_user_notifications_time(session: AsyncSession, user: User, value:str):
    user.notifications_time = value
    try:
        await session.commit()
        await session.refresh(user)
        return True
    except IntegrityError:
        await session.rollback()
        return False
    
async def db_set_user_job_id(session: AsyncSession, user: User, value):
    user.job_id = value
    try:
        await session.commit()
        await session.refresh(user)
        return True
    except IntegrityError:
        await session.rollback()
        return False