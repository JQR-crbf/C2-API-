#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 数据库连接测试脚本
用于验证本地MySQL数据库连接是否正常
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def test_mysql_connection():
    """
    测试MySQL数据库连接
    """
    print("🔍 开始测试MySQL数据库连接...")
    print("=" * 50)
    
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取数据库连接字符串
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            print("❌ 错误：未找到DATABASE_URL环境变量")
            print("请检查.env文件是否存在且配置正确")
            return False
            
        print(f"📋 数据库连接字符串: {database_url[:50]}...")
        
        # 创建数据库引擎
        print("🔧 创建数据库引擎...")
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False
            }
        )
        
        # 测试连接
        print("🔗 测试数据库连接...")
        with engine.connect() as connection:
            # 执行简单查询
            result = connection.execute(text("SELECT 1 as test_value"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                print("✅ 数据库连接成功！")
                
                # 获取MySQL版本信息
                version_result = connection.execute(text("SELECT VERSION() as version"))
                mysql_version = version_result.fetchone()[0]
                print(f"📊 MySQL版本: {mysql_version}")
                
                # 获取当前数据库名
                db_result = connection.execute(text("SELECT DATABASE() as db_name"))
                db_name = db_result.fetchone()[0]
                print(f"🗄️ 当前数据库: {db_name}")
                
                # 检查字符集
                charset_result = connection.execute(text(
                    "SELECT @@character_set_database as charset, @@collation_database as collation"
                ))
                charset_info = charset_result.fetchone()
                print(f"🔤 字符集: {charset_info[0]}, 排序规则: {charset_info[1]}")
                
                # 测试表创建权限
                print("\n🧪 测试表操作权限...")
                try:
                    # 创建测试表
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS test_connection (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            test_message VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """))
                    
                    # 插入测试数据
                    connection.execute(text("""
                        INSERT INTO test_connection (test_message) 
                        VALUES ('MySQL连接测试成功')
                    """))
                    
                    # 查询测试数据
                    test_data = connection.execute(text(
                        "SELECT test_message FROM test_connection ORDER BY id DESC LIMIT 1"
                    ))
                    message = test_data.fetchone()[0]
                    print(f"✅ 表操作测试成功: {message}")
                    
                    # 清理测试表
                    connection.execute(text("DROP TABLE test_connection"))
                    print("🧹 清理测试数据完成")
                    
                    connection.commit()
                    
                except SQLAlchemyError as table_error:
                    print(f"⚠️ 表操作权限测试失败: {table_error}")
                    print("请检查MySQL用户是否有CREATE、INSERT、SELECT、DROP权限")
                
                return True
            else:
                print("❌ 数据库连接测试失败")
                return False
                
    except SQLAlchemyError as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n🔧 可能的解决方案:")
        print("1. 检查MySQL服务是否正在运行")
        print("2. 检查数据库名称、用户名、密码是否正确")
        print("3. 检查MySQL端口是否为3306")
        print("4. 确保已安装mysqlclient: pip install mysqlclient")
        print("5. 检查防火墙设置")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def main():
    """
    主函数
    """
    print("🚀 MySQL数据库连接测试工具")
    print("=" * 50)
    
    success = test_mysql_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过！MySQL数据库配置正确。")
        print("现在可以运行 python main.py 启动应用了！")
        sys.exit(0)
    else:
        print("💥 测试失败！请检查配置后重试。")
        sys.exit(1)

if __name__ == "__main__":
    main()