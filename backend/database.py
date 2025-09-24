from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 本地 MySQL 数据库配置
# 格式：mysql+mysqldb://username:password@host:port/database_name
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+mysqldb://root:password@localhost:3306/api_project_database"
)

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    echo=True,  # 开发环境下显示SQL语句
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=3600,  # 连接回收时间（MySQL建议更长）
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    connect_args={
        "charset": "utf8mb4",  # 支持emoji和特殊字符
        "autocommit": False
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()