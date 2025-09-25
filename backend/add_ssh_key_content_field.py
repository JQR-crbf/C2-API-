#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import engine
from sqlalchemy import text

def add_ssh_key_content_field():
    """添加ssh_key_content字段到deployment_sessions表"""
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text('DESCRIBE deployment_sessions'))
            columns = [row[0] for row in result.fetchall()]
            
            if 'ssh_key_content' in columns:
                print('ssh_key_content字段已存在，无需添加')
                return True
            
            # 添加ssh_key_content字段
            print('正在添加ssh_key_content字段...')
            conn.execute(text('ALTER TABLE deployment_sessions ADD COLUMN ssh_key_content TEXT'))
            conn.commit()
            
            print('✅ ssh_key_content字段添加成功！')
            
            # 验证字段是否添加成功
            result = conn.execute(text('DESCRIBE deployment_sessions'))
            print('\n更新后的表结构:')
            print('-' * 50)
            for row in result.fetchall():
                field, type_, null, key, default, extra = row
                print(f'{field}: {type_} ({null}) {key} {default} {extra}')
            
            return True
            
    except Exception as e:
        print(f'错误: {e}')
        return False

if __name__ == '__main__':
    add_ssh_key_content_field()