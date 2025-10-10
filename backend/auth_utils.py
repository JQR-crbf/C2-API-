from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# JWT配置
SECRET_KEY = "your-secret-key-here-change-in-production"  # 生产环境需要更改
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30天

# 使用bcrypt密码哈希算法
# 明确指定使用bcrypt库，避免passlib的自动检测导致的72字节错误
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b"  # 使用现代bcrypt格式，避免detect_wrap_bug检测
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 - 使用更快的bcrypt算法"""
    # bcrypt限制密码不能超过72字节，与加密时保持一致
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希 - 使用更快的bcrypt算法"""
    # bcrypt限制密码不能超过72字节，确保安全截断
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # 截断到72字节，确保不会截断在UTF-8字符中间
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def decode_token(token: str) -> Optional[dict]:
    """解码访问令牌（与verify_token功能相同）"""
    return verify_token(token)

def create_user_token(user_id: int, username: str, role: str) -> str:
    """为用户创建令牌"""
    token_data = {
        "user_id": user_id,
        "username": username,
        "role": role
    }
    return create_access_token(token_data)