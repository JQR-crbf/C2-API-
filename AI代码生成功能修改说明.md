# AI代码生成功能修改说明

## 修改概述

根据用户需求，已将系统从**自动AI代码生成**模式改为**手动聊天生成代码**模式。

## 修改内容

### 1. 任务创建时不再自动触发AI代码生成

**文件：** `backend/routers/tasks.py`
**修改位置：** 第78行
**修改内容：**
```python
# 修改前
asyncio.create_task(trigger_ai_generation(new_task.id))

# 修改后（已注释）
# 注释掉自动触发AI代码生成，改为手动聊天生成
# asyncio.create_task(trigger_ai_generation(new_task.id))
```

### 2. 任务处理器不再自动处理SUBMITTED状态的任务

**文件：** `backend/services/task_processor.py`

**修改1 - 获取待处理任务：** 第62-68行
```python
# 修改前
Task.status.in_([
    TaskStatus.SUBMITTED,
    TaskStatus.AI_GENERATING
])

# 修改后
Task.status.in_([
    # TaskStatus.SUBMITTED,  # 不再自动处理已提交的任务
    TaskStatus.AI_GENERATING
])
```

**修改2 - 任务处理逻辑：** 第87-90行
```python
# 修改前
if task.status == TaskStatus.SUBMITTED:
    await self._handle_submitted_task(task, db)
elif task.status == TaskStatus.AI_GENERATING:

# 修改后
# 注释掉自动处理SUBMITTED状态，改为手动聊天生成代码
# if task.status == TaskStatus.SUBMITTED:
#     await self._handle_submitted_task(task, db)
if task.status == TaskStatus.AI_GENERATING:
```

## 功能变化

### 修改前的工作流程
1. 用户创建任务 → 任务状态：`SUBMITTED`
2. 系统自动触发AI代码生成 → 任务状态：`AI_GENERATING`
3. AI服务生成代码 → 任务状态：`CODE_SUBMITTED`
4. 等待管理员审核

### 修改后的工作流程
1. 用户创建任务 → 任务状态：`SUBMITTED`
2. **任务保持SUBMITTED状态，等待手动操作**
3. 用户通过聊天界面手动生成代码
4. 手动将生成的代码关联到任务
5. 等待管理员审核

## 保留的功能

以下功能仍然保留，可以手动触发：

1. **重新生成代码API：** `POST /api/tasks/{task_id}/regenerate`
   - 仍然可以手动触发AI代码生成
   - 需要用户主动调用

2. **AI服务功能：** `services/ai_service.py`
   - 所有AI功能都保留
   - 可以通过API手动调用

3. **trigger_ai_generation函数：**
   - 函数本身保留
   - 只是不再自动调用

## 验证结果

✅ **测试通过：**
- 创建新任务ID 9："测试手动AI生成"
- 任务状态保持为 `submitted`
- 等待10秒后状态仍为 `submitted`
- 确认不会自动进入AI代码生成流程

## 后续建议

1. **开发聊天界面：** 创建AI助手聊天功能，让用户可以通过对话生成代码
2. **手动关联功能：** 提供将聊天生成的代码关联到具体任务的功能
3. **状态管理：** 考虑添加新的任务状态来区分手动和自动生成的代码

## 回滚方法

如果需要恢复自动AI代码生成功能，只需：
1. 取消注释 `routers/tasks.py` 第78行
2. 取消注释 `services/task_processor.py` 第64行和第87-89行
3. 重启后端服务

---

**修改时间：** 2025-09-28
**修改人：** AI助手
**影响范围：** 任务创建和自动处理流程