from pydantic import BaseModel, Field
from typing import List, Optional

class CreateConversationRequestSchema(BaseModel):
    isGroup: bool = Field(False, alias="isGroup")
    conversationName: Optional[str] = Field(None, alias="conversationName")
    targetUserId: Optional[str] = Field(None, alias="targetUserId")
    memberIds: Optional[List[str]] = Field(None, alias="memberIds")

class UpdateConversationRequestSchema(BaseModel):
    conversationName: Optional[str] = Field(None, alias="conversationName")
    avatarUrl: Optional[str] = Field(None, alias="avatarUrl")

class AddMemberRequestSchema(BaseModel):
    conversationId: int = Field(..., alias="conversationId")
    newMemberId: str = Field(..., alias="newMemberId")

class RemoveMemberRequestSchema(BaseModel):
    conversationId: int = Field(..., alias="conversationId")
    memberIdToRemove: str = Field(..., alias="memberIdToRemove")

class LeaveGroupRequestSchema(BaseModel):
    conversationId: int = Field(..., alias="conversationId")

class TransferOwnerRequestSchema(BaseModel):
    conversationId: int = Field(..., alias="conversationId")
    newOwnerId: str = Field(..., alias="newOwnerId")

class SendMessageRequestSchema(BaseModel):
    conversationId: int = Field(..., alias="conversationId")
    messageContent: str = Field(..., alias="messageContent")
    messageType: str = Field("text", alias="messageType")

class EditMessageRequestSchema(BaseModel):
    newContent: str = Field(..., alias="newContent")




