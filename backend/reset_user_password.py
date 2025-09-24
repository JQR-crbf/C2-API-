from sqlalchemy.orm import sessionmaker
from database import engine
from models import User
from auth_utils import get_password_hash

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def reset_user_password():
    db = SessionLocal()
    try:
        # 查找用户
        user = db.query(User).filter(User.username == "jinqianru").first()
        
        if user:
            # 重置密码为123456
            new_password = "123456"
            user.password_hash = get_password_hash(new_password)
            db.commit()
            print(f"✅ 用户 {user.username} 的密码已重置为: {new_password}")
        else:
            print("❌ 未找到用户jinqianru")
            
    except Exception as e:
        print(f"❌ 重置密码失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_user_password()