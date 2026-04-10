from pydantic import BaseModel, Field

class AddContactRequestSchema(BaseModel):
    colleagueId: str = Field(..., alias="colleagueId", description="UUID của đồng nghiệp cần thêm")

class BlockUserRequestSchema(BaseModel):
    targetUserId: str = Field(..., alias="targetUserId", description="UUID của người dùng cần chặn")

class UpdateProfileRequestSchema(BaseModel):
    fullName: str = Field(None, alias="fullName")
    phoneNumber: str = Field(None, alias="phoneNumber")
    dateOfBirth: str = Field(None, alias="dateOfBirth")
    position: str = Field(None, alias="position")
    avatarUrl: str = Field(None, alias="avatarUrl")
