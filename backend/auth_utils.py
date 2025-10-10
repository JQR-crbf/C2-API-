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
# 直接导入bcrypt库，绕过passlib的版本检测问题
import bcrypt

# 使用原生bcrypt而不是passlib包装，避免detect_wrap_bug检测问题
def _bcrypt_hash(password: str) -> str:
    """使用原生bcrypt加密密码"""
    password_bytes = password.encode('utf-8')
    # bcrypt限制72字节
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def _bcrypt_verify(password: str, hashed: str) -> bool:
    """使用原生bcrypt验证密码"""
    password_bytes = password.encode('utf-8')
    # bcrypt限制72字节
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return bcrypt.checkpw(password_bytes, hashed.encode('utf-8'))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 - 使用原生bcrypt"""
    return _bcrypt_verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希 - 使用原生bcrypt"""
    return _bcrypt_hash(password)

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