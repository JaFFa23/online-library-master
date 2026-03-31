from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    # Позволяет создавать схемы из ORM-объектов через model_validate(obj)
    model_config = ConfigDict(from_attributes=True, extra="ignore")
