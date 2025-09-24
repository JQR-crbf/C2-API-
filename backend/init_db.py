#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建数据库表和初始化管理员账户
"""

from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import User, UserRole
from auth_utils import get_password_hash
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """创建数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
        return True
    except Exception as e:
        logger.error(f"数据库表创建失败：{str(e)}")
        return False

def create_admin_user(db: Session):
    """创建默认管理员账户"""
    try:
        # 检查是否已存在管理员账户
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing_admin:
            logger.info(f"管理员账户已存在：{existing_admin.username}")
            return True
        
        # 创建默认管理员账户
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"默认管理员账户创建成功：{admin_user.username}")
        logger.info("默认管理员登录信息：")
        logger.info("  用户名: admin")
        logger.info("  密码: admin123")
        logger.info("  邮箱: admin@example.com")
        
        return True
        
    except Exception as e:
        logger.error(f"创建管理员账户失败：{str(e)}")
        db.rollback()
        return False

def create_demo_user(db: Session):
    """创建演示用户账户"""
    try:
        # 检查是否已存在演示用户
        existing_user = db.query(User).filter(User.username == "demo").first()
        if existing_user:
            logger.info(f"演示用户已存在：{existing_user.username}")
            return True
        
        # 创建演示用户账户
        demo_user = User(
            username="demo",
            email="demo@example.com",
            password_hash=get_password_hash("demo123"),
            role=UserRole.USER,
            is_active=True
        )
        
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        
        logger.info(f"演示用户账户创建成功：{demo_user.username}")
        logger.info("演示用户登录信息：")
        logger.info("  用户名: demo")
        logger.info("  密码: demo123")
        logger.info("  邮箱: demo@example.com")
        
        return True
        
    except Exception as e:
        logger.error(f"创建演示用户失败：{str(e)}")
        db.rollback()
        return False

def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    # 创建数据库表
    if not create_tables():
        logger.error("数据库初始化失败：无法创建表")
        return False
    
    # 创建数据库会话
    db = SessionLocal()
    try:
        # 创建管理员账户
        if not create_admin_user(db):
            logger.error("数据库初始化失败：无法创建管理员账户")
            return False
        
        # 创建演示用户
        if not create_demo_user(db):
            logger.error("数据库初始化失败：无法创建演示用户")
            return False
        
        logger.info("数据库初始化完成！")
        logger.info("")
        logger.info("=== 系统账户信息 ===")
        logger.info("管理员账户：")
        logger.info("  用户名: admin")
        logger.info("  密码: admin123")
        logger.info("")
        logger.info("演示用户账户：")
        logger.info("  用户名: demo")
        logger.info("  密码: demo123")
        logger.info("")
        logger.info("请在生产环境中修改默认密码！")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化异常：{str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n数据库初始化成功！")
        exit(0)
    else:
        print("\n数据库初始化失败！")
        exit(1)