from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Optional

class RegisterRequestSchema(BaseModel):
    email: EmailStr
    password: str
    fullName: str = Field(..., alias="fullName")
    phone: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        if not re.search("[a-z]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 chữ thường')
        if not re.search("[A-Z]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 chữ hoa')
        if not re.search("[@#$%^&+=!]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt (@#$%^&+=!)')
        return v

class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str

class Verify2FARequestSchema(BaseModel):
    email: EmailStr
    otpCode: str = Field(..., alias="otpCode", min_length=6, max_length=10)

class ResendOTPRequestSchema(BaseModel):
    email: EmailStr

class ForgotPasswordRequestSchema(BaseModel):
    email: EmailStr

class ResetPasswordRequestSchema(BaseModel):
    email: EmailStr
    otpCode: str = Field(..., alias="otpCode")
    newPassword: str = Field(..., alias="newPassword")

    @field_validator('newPassword')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        if not re.search("[a-z]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 chữ thường')
        if not re.search("[A-Z]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 chữ hoa')
        if not re.search("[@#$%^&+=!]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt (@#$%^&+=!)')
        return v

class ChangePasswordRequestSchema(BaseModel):
    oldPassword: str = Field(..., alias="oldPassword")
    newPassword: str = Field(..., alias="newPassword")

    @field_validator('newPassword')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        if not re.search("[a-z]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 chữ thường')
        if not re.search("[A-Z]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 chữ hoa')
        if not re.search("[@#$%^&+=!]", v):
            raise ValueError('Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt (@#$%^&+=!)')
        return v
