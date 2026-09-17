from typing import Optional

from pydantic import BaseModel


class NutritionInfo(BaseModel):
    calories_kcal: float
    carbs_g: float
    sugar_g: float
    fiber_g: float
    vitamin_c_mg: float
    potassium_mg: float


class FruitInfo(BaseModel):
    display_name: str
    nutrition: NutritionInfo
    health_benefits: list[str]
    usage_suggestions: list[str]


class PredictionResponse(BaseModel):
    accepted: bool
    message: str
    label: Optional[str] = None
    confidence: Optional[float] = None
    ripeness: Optional[str] = None
    ripeness_note: Optional[str] = None
    ripeness_method: Optional[str] = None
    info: Optional[FruitInfo] = None
    speech_text: Optional[str] = None
