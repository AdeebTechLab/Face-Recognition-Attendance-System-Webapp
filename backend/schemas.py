from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class StudentCreate(BaseModel):
    roll_number: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    department: str = Field(..., min_length=2, max_length=100)

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None

class FrameCaptureRequest(BaseModel):
    roll_number: str
    image_base64: str

class TrainRequest(BaseModel):
    tolerance: float = Field(0.50, ge=0.35, le=0.65)

class RecognizeRequest(BaseModel):
    image_base64: str
    tolerance: float = Field(0.50, ge=0.35, le=0.65)
    auto_mark: bool = True

class ManualAttendanceRequest(BaseModel):
    roll_number: str
    face_distance: float
    verification_token: str