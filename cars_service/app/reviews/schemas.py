from pydantic import BaseModel, Field, ConfigDict


class BaseReview(BaseModel):
    comment: str

    model_config = ConfigDict(from_attributes=True)


class ReviewOut(BaseReview):
    id: int
    stars: int
    car_id: int
    parent_id: int | None = None
    sub_reviews: list['ReviewOut']


class ReviewIn(BaseReview):
    car_id: int
    stars: int = Field(ge=0, le=10)
    parent_id: int | None = None


class ReviewUpdate(BaseReview):
    comment: str | None = None
    stars: int | None = Field(ge=0, le=10, default=None)
