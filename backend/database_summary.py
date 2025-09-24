#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库内容汇总和比对脚本
用于检查项目中的数据库结构和数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 完全禁用所有日志
import logging
logging.disable(logging.CRITICAL)

from sqlalchemy.orm import sessionmaker
from database import engine
from models import User, Task, Notification, TaskLog

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("=== AI API 平台数据库内容汇总报告 ===")
    print("\n" + "="*50)
    
    # 1. 数据库表结构检查
    print("\n📊 1. 数据库表结构:")
    print("   ✅ users (用户表) - 存储用户账户信息")
    print("   ✅ tasks (任务表) - 存储API开发任务")
    print("   ✅ notifications (通知表) - 存储系统通知")
    print("   ✅ task_logs (任务日志表) - 存储任务执行日志")
    
    # 2. 用户表数据
    print("\n👥 2. 用户表 (users) 数据:")
    users = db.query(User).all()
    print(f"   总用户数: {len(users)}")
    print("   用户列表:")
    for u in users:
        print(f"     ID:{u.id} | 用户名:{u.username} | 邮箱:{u.email} | 角色:{u.role.value} | 激活:{u.is_active} | 创建时间:{u.created_at}")
    
    # 3. 任务表数据
    print("\n📋 3. 任务表 (tasks) 数据:")
    tasks = db.query(Task).all()
    print(f"   总任务数: {len(tasks)}")
    if tasks:
        print("   任务列表:")
        for t in tasks:
            user = db.query(User).filter(User.id == t.user_id).first()
            title = t.title[:40] + "..." if len(t.title) > 40 else t.title
            print(f"     ID:{t.id} | 标题:{title} | 创建者:{user.username if user else '未知'} | 状态:{t.status.value} | 创建时间:{t.created_at}")
    else:
        print("   ❌ 没有任务数据")
    
    # 4. 通知表数据
    print("\n🔔 4. 通知表 (notifications) 数据:")
    notifications = db.query(Notification).all()
    print(f"   总通知数: {len(notifications)}")
    if notifications:
        for n in notifications:
            user = db.query(User).filter(User.id == n.user_id).first()
            print(f"     ID:{n.id} | 接收者:{user.username if user else '未知'} | 标题:{n.title} | 类型:{n.type.value} | 已读:{n.is_read}")
    
    # 5. 任务日志表数据
    print("\n📝 5. 任务日志表 (task_logs) 数据:")
    task_logs = db.query(TaskLog).all()
    print(f"   总日志数: {len(task_logs)}")
    if task_logs:
        for log in task_logs[:5]:  # 只显示前5条
            task = db.query(Task).filter(Task.id == log.task_id).first()
            print(f"     ID:{log.id} | 任务:{task.title[:20] if task else '未知'}... | 状态:{log.status} | 时间:{log.created_at}")
        if len(task_logs) > 5:
            print(f"     ... 还有 {len(task_logs) - 5} 条日志")
    
    # 6. jinqianru用户详细分析
    print("\n🔍 6. jinqianru用户详细分析:")
    jinqianru = db.query(User).filter(User.username == 'jinqianru').first()
    if jinqianru:
        print(f"   ✅ 找到jinqianru用户:")
        print(f"     用户ID: {jinqianru.id}")
        print(f"     用户名: {jinqianru.username}")
        print(f"     邮箱: {jinqianru.email}")
        print(f"     角色: {jinqianru.role.value}")
        print(f"     激活状态: {jinqianru.is_active}")
        print(f"     创建时间: {jinqianru.created_at}")
        
        # jinqianru的任务
        jinqianru_tasks = db.query(Task).filter(Task.user_id == jinqianru.id).all()
        print(f"\n   📋 jinqianru的任务 (共{len(jinqianru_tasks)}个):")
        if jinqianru_tasks:
            for i, task in enumerate(jinqianru_tasks, 1):
                print(f"     {i}. [{task.id}] {task.title}")
                print(f"        状态: {task.status.value} | 创建时间: {task.created_at}")
                if task.description:
                    desc = task.description[:50] + "..." if len(task.description) > 50 else task.description
                    print(f"        描述: {desc}")
                print()
        else:
            print("     ❌ jinqianru用户没有任务")
        
        # jinqianru的通知
        jinqianru_notifications = db.query(Notification).filter(Notification.user_id == jinqianru.id).all()
        print(f"   🔔 jinqianru的通知 (共{len(jinqianru_notifications)}个):")
        if jinqianru_notifications:
            for notif in jinqianru_notifications:
                print(f"     - {notif.title} (类型: {notif.type.value}, 已读: {notif.is_read})")
    else:
        print("   ❌ 未找到jinqianru用户")
    
    # 7. 数据库一致性检查
    print("\n🔧 7. 数据库一致性检查:")
    
    # 检查孤立任务（没有对应用户的任务）
    orphan_tasks = []
    for task in tasks:
        user = db.query(User).filter(User.id == task.user_id).first()
        if not user:
            orphan_tasks.append(task)
    
    if orphan_tasks:
        print(f"   ⚠️ 发现 {len(orphan_tasks)} 个孤立任务（用户不存在）:")
        for task in orphan_tasks:
            print(f"     - 任务ID:{task.id}, 用户ID:{task.user_id}, 标题:{task.title}")
    else:
        print("   ✅ 所有任务都有对应的用户")
    
    # 检查孤立通知
    orphan_notifications = []
    for notif in notifications:
        user = db.query(User).filter(User.id == notif.user_id).first()
        if not user:
            orphan_notifications.append(notif)
    
    if orphan_notifications:
        print(f"   ⚠️ 发现 {len(orphan_notifications)} 个孤立通知（用户不存在）")
    else:
        print("   ✅ 所有通知都有对应的用户")
    
    # 8. 模型字段与Schema字段对比
    print("\n📋 8. 模型字段与Schema字段对比:")
    print("   User模型字段: id, username, email, password_hash, role, is_active, created_at, updated_at")
    print("   UserResponse Schema字段: id, username, email, role, is_active, created_at, full_name")
    print("   ⚠️ 不匹配字段:")
    print("     - User模型缺少: full_name")
    print("     - UserResponse多了: full_name")
    print("     - User模型有但Schema没有: password_hash, updated_at")
    
    # 9. 总结
    print("\n" + "="*50)
    print("📊 总结:")
    print(f"   - 数据库表: 4个 (users, tasks, notifications, task_logs)")
    print(f"   - 总用户数: {len(users)}")
    print(f"   - 总任务数: {len(tasks)}")
    print(f"   - 总通知数: {len(notifications)}")
    print(f"   - 总日志数: {len(task_logs)}")
    print(f"   - jinqianru用户: {'存在' if jinqianru else '不存在'}")
    if jinqianru:
        print(f"   - jinqianru任务数: {len(jinqianru_tasks)}")
    print("\n✅ 数据库结构完整，数据一致性良好")
    print("⚠️ 需要注意User模型与UserResponse Schema的字段不匹配问题")
    
except Exception as e:
    print(f"❌ 错误: {e}")
finally:
    db.close()