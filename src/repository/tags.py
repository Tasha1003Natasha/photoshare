from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.tag import Tag


async def get_or_create_tags(names: list[str], db: AsyncSession):
    if len(names) > 5:
        raise HTTPException(status_code=422, detail="Maximum of 5 tags")

    normalized = list(dict.fromkeys(name.strip().lower() for name in names))

    if any(not name for name in normalized):
        raise HTTPException(status_code=422, detail="The tag cannot be empty.")

    tags = []

    for name in normalized:
        result = await db.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()

        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
            await db.flush()

        tags.append(tag)

    return tags
