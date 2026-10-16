"""Pydantic request and response schemas shared by API routes."""
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# Models (camelCase on the wire, snake_case in Python)

# --------------------------------------------------------------------------------

# Purpose: Define the CamelModel data/model type.
class CamelModel(BaseModel):

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)





TransactionType = Literal["EXPENSE", "INCOME"]





# Purpose: Define the CategorizeRequest data/model type.
class CategorizeRequest(CamelModel):

    model_config = ConfigDict(

        alias_generator=to_camel,

        populate_by_name=True,

        json_schema_extra={"example": {

            "description": "Swiggy order",

            "merchant": "Swiggy",

            "type": "EXPENSE",

            "userId": "Copy userId from GET /auth/user-id",

        }},

    )

    description: str = Field(..., min_length=1, max_length=500)

    merchant: Optional[str] = Field(None, max_length=200, description="Optional merchant name to improve matching")

    type: TransactionType = "EXPENSE"

    user_id: Optional[str] = Field(

        None, description="If given, the response also contains the matching categoryId for this user."

    )





# Purpose: Define the CategorizeResponse data/model type.
class CategorizeResponse(CamelModel):

    description: str

    type: TransactionType

    category: str

    category_id: Optional[str] = None

    matched_keyword: Optional[str] = None

    confidence: float = Field(ge=0, le=1, description="Rule-based confidence, not a calibrated ML probability")





# Purpose: Define the AnomalyRequest data/model type.
class AnomalyRequest(CamelModel):

    model_config = ConfigDict(

        alias_generator=to_camel,

        populate_by_name=True,

        json_schema_extra={"example": {"multiplier": 2.0}},

    )

    # Public requests derive the owner from the verified Bearer JWT. Optional

    # userId remains supported for trusted NestJS-to-FastAPI internal calls.

    user_id: Optional[str] = Field(None, description="Optional for internal NestJS calls; public calls use the authenticated JWT user")

    multiplier: float = Field(2.0, gt=1, description="Flag expenses above multiplier x category average")





# Purpose: Define the AnomalyItem data/model type.
class AnomalyItem(CamelModel):

    transaction_id: str

    description: str

    category: str

    category_id: str

    amount: float

    date: date

    category_average: float

    times_average: float

    severity: Literal["low", "medium", "high"]

    reason: str





# Purpose: Define the AnomalyResponse data/model type.
class AnomalyResponse(CamelModel):

    user_id: str

    multiplier: float

    anomalies: list[AnomalyItem]





# Purpose: Define the PredictRequest data/model type.
class PredictRequest(CamelModel):

    model_config = ConfigDict(

        alias_generator=to_camel,

        populate_by_name=True,

        json_schema_extra={"example": {"months": 3}},

    )

    # Public requests derive the owner from the verified Bearer JWT. Optional

    # userId remains supported for trusted NestJS-to-FastAPI internal calls.

    user_id: Optional[str] = Field(None, description="Optional for internal NestJS calls; public calls use the authenticated JWT user")

    months: int = Field(3, ge=1, le=12, description="How many completed months to average")

    as_of: Optional[date] = Field(None, description="Pretend today is this date (default: today, UTC)")





# Purpose: Define the PredictionItem data/model type.
class PredictionItem(CamelModel):

    category: str

    category_id: str

    predicted_amount: float





# Purpose: Define the PredictionBasis data/model type.
class PredictionBasis(CamelModel):

    start: date

    end: date

    months: int





# Purpose: Define the PredictResponse data/model type.
class PredictResponse(CamelModel):

    user_id: str

    year: int

    month: int

    total_predicted: float

    based_on: PredictionBasis

    predictions: list[PredictionItem]





# Purpose: Define the DuplicateItem data/model type.
class DuplicateItem(CamelModel):

    first_transaction_id: str

    second_transaction_id: str

    first_description: str

    second_description: str

    amount: float

    first_date: date

    second_date: date

    days_apart: int

    reason: str





# Purpose: Define the DuplicateResponse data/model type.
class DuplicateResponse(CamelModel):

    user_id: str

    window_days: int

    count: int

    duplicates: list[DuplicateItem]





# --------------------------------------------------------------------------------

