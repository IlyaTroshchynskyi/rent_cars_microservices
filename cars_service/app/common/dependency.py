from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session

db_dependency = Annotated[AsyncSession, Depends(get_session)]
