import time
from typing import List, Set, Dict

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase

from property import Property


class Base(DeclarativeBase):
    pass


class DBProperty(Base):
    """
    Mapping for SQLAlchemy to the table.
    If we add more tables it might be worth extracting this to a different package to keep things clean.
    """

    def __repr__(self) -> str:
        return """DBProperty(
            Property_id: {self.property_id},
            Price: {self.price},
            Available from: {self.available_from},
            Description: {self.description},
            Post code: {self.post_code},
            Bedrooms: {self.bedrooms},
            Bathrooms: {self.bathrooms},
            Score: {self.score},
            Score reasons: {self.score_reasons}
            Date unix: {self.date_unix}
        )
        """

    __tablename__ = "properties"

    property_id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[int] = mapped_column()
    available_from: Mapped[str] = mapped_column()
    has_garden: Mapped[bool] = mapped_column()
    description: Mapped[str] = mapped_column()
    post_code: Mapped[str] = mapped_column()
    bedrooms: Mapped[int] = mapped_column()
    bathrooms: Mapped[int] = mapped_column()
    score: Mapped[int] = mapped_column()
    score_reasons: Mapped[str] = mapped_column()
    date_unix: Mapped[int] = mapped_column()


class DbConnOrm:
    """
    Class for DB operations. Allows retrieval of seen properties and insertion of newly discovered ones.
    This might be augmented in the future with other methods as it may require.

    Ideas:
    1) A cleanup job will be needed to remove from the db properties that have been rented
    2) CRUD will be needed if I built an UI on top of this data. But at that point probably I'll not be using sqlite anymore
    """

    def __init__(self, db_name:str, echo=False):
        self.engine = create_engine(f"sqlite:///{db_name}", echo=echo)
        Base.metadata.create_all(self.engine)

    def get_latest_properties(self, limit: int) -> Set[int]:
        with Session(self.engine) as session:
            stmt = select(DBProperty.property_id).order_by(DBProperty.date_unix.desc()).limit(limit)
            return set(session.scalars(stmt))

    def insert_properties(self, properties: Dict[int, Property]) -> None:
        current_time = int(time.time())
        orm = self.__convert_dao_to_orm(list(properties.values()), current_time)
        with Session(self.engine) as session:
            session.add_all(orm)
            session.commit()

    def __convert_dao_to_orm(self, properties: List[Property], current_time: int) -> List[DBProperty]:
        orm_list = []
        for property_dao in properties:
            orm_list.append(DBProperty(
                property_id=property_dao.property_id,
                price=property_dao.property_details.price,
                available_from=property_dao.property_details.available_from,
                has_garden=property_dao.property_details.has_garden,
                description=property_dao.property_details.description,
                post_code=property_dao.property_details.post_code,
                bedrooms=property_dao.property_details.bedrooms,
                bathrooms=property_dao.property_details.bathrooms,
                score=property_dao.score,
                score_reasons="\n".join(property_dao.score_reasons),
                date_unix=current_time,
            ))
        return orm_list
