from pydantic import BaseModel
from typing import Optional

class PointsOfMapCreate(BaseModel):
    name: str
    level: int
    poi_type: int
    latitude: float
    longitude: float
    description: str

class PointsOfMapUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    poi_type: Optional[int] = None
    latitude: Optional[float] = None
    longitude:Optional[float] = None
    description: Optional[str] = None
