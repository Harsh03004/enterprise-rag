from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collection import Collection


def create_collection(
    db: Session,
    user_id: int,
    name: str,
) -> Collection:
    collection = Collection(
        user_id=user_id,
        name=name,
    )

    db.add(collection)
    db.commit()
    db.refresh(collection)

    return collection


def get_collection(
    db: Session,
    collection_id: int,
    user_id: int,
) -> Collection | None:
    statement = select(Collection).where(
        Collection.id == collection_id,
        Collection.user_id == user_id,
    )

    return db.scalar(statement)


def get_collections(
    db: Session,
    user_id: int,
) -> list[Collection]:
    statement = (
        select(Collection)
        .where(
            Collection.user_id == user_id
        )
        .order_by(
            Collection.created_at.desc()
        )
    )

    return list(db.scalars(statement).all())


def update_collection(
    db: Session,
    collection_id: int,
    user_id: int,
    name: str,
) -> Collection | None:
    collection = get_collection(
        db=db,
        collection_id=collection_id,
        user_id=user_id,
    )

    if collection is None:
        return None

    collection.name = name

    db.commit()
    db.refresh(collection)

    return collection


def delete_collection(
    db: Session,
    collection_id: int,
    user_id: int,
) -> bool:
    collection = get_collection(
        db=db,
        collection_id=collection_id,
        user_id=user_id,
    )

    if collection is None:
        return False

    db.delete(collection)
    db.commit()

    return True