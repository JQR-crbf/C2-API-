# API接口开发指南

本文档基于现有项目架构，为开发者提供快速开发新API接口的完整指南。

## 项目架构概述

本项目采用分层架构设计，遵循以下模式：

```
请求 → 路由层(Router) → 服务层(Service) → 数据访问层(Model) → 数据库
       ↓
    数据验证(Schema) ← 响应格式化
```

### 核心分层说明

1. **路由层** (`app/api/v1/`): 处理HTTP请求，参数验证，调用服务层
2. **服务层** (`app/services/`): 业务逻辑处理，数据操作
3. **模型层** (`app/models/`): 数据库表结构定义
4. **数据模式层** (`app/schemas/`): 请求/响应数据验证和序列化
5. **数据库层** (`app/database*.py`): 数据库连接和会话管理

## 常见问题解答

### 问题1：按照这个开发指南开发的接口是Swagger框架下的吗？会在页面直接显示出来吗？

**答案：是的！本项目基于FastAPI框架，自动集成Swagger UI文档系统。**

#### Swagger访问地址：
- **Swagger UI**: `http://localhost:8000/docs` - 交互式API文档界面
- **ReDoc**: `http://localhost:8000/redoc` - 另一种文档展示风格
- **OpenAPI JSON**: `http://localhost:8000/openapi.json` - API规范的JSON格式

#### 自动显示特性：
1. **自动生成**: 你开发的每个接口都会自动出现在Swagger页面中
2. **实时更新**: 代码修改后，文档会自动更新
3. **交互测试**: 可以直接在Swagger页面测试接口
4. **参数说明**: 自动显示请求参数、响应格式等
5. **分组显示**: 按照tags自动分组（如"用户管理"、"产品管理"等）

#### 如何让你的接口在Swagger中显示：
```python
# 在路由定义中添加描述信息
@router.post(
    "/",
    response_model=ApiResponse,
    summary="创建记录",  # 这会显示在Swagger中
    description="创建新的记录",  # 详细描述
    tags=["你的模块名称"]  # 分组标签
)
```

### 问题2：开发的接口要保存在项目的哪个文件夹下？

**答案：按照项目架构，新接口文件应该保存在以下位置：**

#### 文件保存位置规范：
```
app/
├── models/
│   └── your_model.py          # 数据模型文件
├── schemas/
│   └── your_schema.py         # 数据验证模式文件
├── services/
│   └── your_service.py        # 业务逻辑服务文件
└── api/
    └── v1/
        └── your_api.py        # API路由文件（重点！）
```

#### 具体保存规则：
1. **API路由文件**: 必须保存在 `app/api/v1/` 目录下
2. **文件命名**: 使用小写字母和下划线，如 `user_management.py`
3. **导入注册**: 在 `app/api/v1/__init__.py` 中导入并注册
4. **主应用注册**: 在 `app/main.py` 中添加路由

#### 注册示例：
```python
# 1. 在 app/api/v1/__init__.py 中添加
from .your_api import router as your_api_router

api_router.include_router(
    your_api_router,
    prefix="/your-endpoint",
    tags=["你的模块名称"]
)

# 2. 在 app/main.py 中添加（如果需要）
from app.api.v1 import your_api
app.include_router(your_api.router, prefix="/api/v1/your-endpoint", tags=["你的模块名称"])
```

### 问题3：我之后如果还想要增加API接口功能，只需要新增代码就好了吗？还有哪些地方需要改动呢？

**答案：主要是新增代码，但需要在以下5个地方进行修改：**

#### 必须新增的文件/代码：
1. **数据模型** (`app/models/your_model.py`) - 定义数据库表结构
2. **数据模式** (`app/schemas/your_schema.py`) - 定义请求/响应格式
3. **服务层** (`app/services/your_service.py`) - 实现业务逻辑
4. **路由层** (`app/api/v1/your_api.py`) - 定义API接口

#### 必须修改的文件：
5. **路由注册** (`app/api/v1/__init__.py` 和 `app/main.py`) - 注册新的路由

#### 可能需要修改的文件：
- **数据库配置** (`app/database*.py`) - 如果需要新的数据库连接
- **配置文件** (`app/config.py`) - 如果需要新的配置项
- **依赖注入** (`app/api/deps.py`) - 如果需要特殊的权限验证

### 问题4：如果我新增API接口功能，需要提供哪些内容呢？

**开发新接口需要提供以下内容：**

#### 1. 业务需求信息
- **功能描述**: 接口的具体功能和用途
- **输入参数**: 需要接收哪些参数，参数类型和验证规则
- **输出结果**: 返回什么数据，数据格式要求
- **业务逻辑**: 具体的处理流程和规则

#### 2. 数据库相关
- **建表语句**: 如果需要新表，提供完整的CREATE TABLE语句
- **数据库连接**: 使用哪个数据库（主库/中东库/新库）
- **数据关系**: 与现有表的关联关系

#### 3. 接口规范
- **接口路径**: 如 `/api/v1/your-endpoint`
- **HTTP方法**: GET/POST/PUT/DELETE
- **权限要求**: 是否需要登录，需要什么权限
- **分页需求**: 是否需要分页，默认页大小

#### 4. 性能要求
- **响应时间**: 期望的响应时间
- **并发量**: 预期的并发访问量
- **缓存策略**: 是否需要缓存

## 快速开发模板

### 步骤1：创建数据模型 (`app/models/your_model.py`)

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base  # 或 app.database_middle_east import MiddleEastBase

class YourModel(Base):  # 或 MiddleEastBase
    """你的数据模型描述"""
    __tablename__ = "your_table_name"
    
    # 主键
    id = Column(Integer, primary_key=True, comment="主键ID")
    
    # 业务字段（根据需求修改）
    name = Column(String(100), nullable=False, comment="名称")
    description = Column(Text, nullable=True, comment="描述")
    status = Column(Integer, default=1, comment="状态：1-启用，0-禁用")
    
    # 时间字段
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<YourModel(id={self.id}, name='{self.name}')>"
    
    class Config:
        from_attributes = True
```

### 步骤2：创建数据模式 (`app/schemas/your_schema.py`)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# 请求模式
class YourModelCreate(BaseModel):
    """创建请求模式"""
    name: str = Field(..., description="名称", max_length=100)
    description: Optional[str] = Field(None, description="描述")
    status: int = Field(1, description="状态：1-启用，0-禁用")

class YourModelUpdate(BaseModel):
    """更新请求模式"""
    name: Optional[str] = Field(None, description="名称", max_length=100)
    description: Optional[str] = Field(None, description="描述")
    status: Optional[int] = Field(None, description="状态：1-启用，0-禁用")

class YourModelQuery(BaseModel):
    """查询请求模式"""
    name: Optional[str] = Field(None, description="名称关键词")
    status: Optional[int] = Field(None, description="状态筛选")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页大小", ge=1, le=100)

# 响应模式
class YourModelResponse(BaseModel):
    """响应模式"""
    id: int = Field(..., description="主键ID")
    name: str = Field(..., description="名称")
    description: Optional[str] = Field(None, description="描述")
    status: int = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True

# 通用响应模式
class ApiResponse(BaseModel):
    """API统一响应格式"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")
```

### 步骤3：创建服务层 (`app/services/your_service.py`)

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Tuple
import logging

from app.models.your_model import YourModel
from app.schemas.your_schema import YourModelCreate, YourModelUpdate, YourModelQuery
from app.database import BaseRepository  # 或使用对应的基础仓库类

logger = logging.getLogger(__name__)

class YourService(BaseRepository):
    """你的业务服务类"""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create(self, obj_in: YourModelCreate) -> YourModel:
        """创建记录"""
        try:
            db_obj = YourModel(**obj_in.dict())
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"创建记录成功: {db_obj.id}")
            return db_obj
        except Exception as e:
            logger.error(f"创建记录失败: {str(e)}")
            self.db.rollback()
            raise
    
    def get_by_id(self, id: int) -> Optional[YourModel]:
        """根据ID获取记录"""
        return self.db.query(YourModel).filter(YourModel.id == id).first()
    
    def get_list(self, query: YourModelQuery) -> Tuple[List[YourModel], int]:
        """获取列表（支持分页和筛选）"""
        db_query = self.db.query(YourModel)
        
        # 筛选条件
        if query.name:
            db_query = db_query.filter(YourModel.name.ilike(f"%{query.name}%"))
        if query.status is not None:
            db_query = db_query.filter(YourModel.status == query.status)
        
        # 获取总数
        total = db_query.count()
        
        # 分页和排序
        offset = (query.page - 1) * query.page_size
        items = db_query.order_by(desc(YourModel.created_at)).offset(offset).limit(query.page_size).all()
        
        return items, total
    
    def update(self, id: int, obj_in: YourModelUpdate) -> Optional[YourModel]:
        """更新记录"""
        try:
            db_obj = self.get_by_id(id)
            if not db_obj:
                return None
            
            update_data = obj_in.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"更新记录成功: {id}")
            return db_obj
        except Exception as e:
            logger.error(f"更新记录失败: {str(e)}")
            self.db.rollback()
            raise
    
    def delete(self, id: int) -> bool:
        """删除记录"""
        try:
            db_obj = self.get_by_id(id)
            if not db_obj:
                return False
            
            self.db.delete(db_obj)
            self.db.commit()
            logger.info(f"删除记录成功: {id}")
            return True
        except Exception as e:
            logger.error(f"删除记录失败: {str(e)}")
            self.db.rollback()
            raise
```

### 步骤4：创建路由层 (`app/api/v1/your_api.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db  # 或 get_middle_east_db
from app.services.your_service import YourService
from app.schemas.your_schema import (
    YourModelCreate, YourModelUpdate, YourModelQuery,
    YourModelResponse, ApiResponse
)
from app.api.deps import get_current_active_user  # 如果需要权限验证
from app.models.user import User  # 如果需要权限验证

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

@router.post(
    "/",
    response_model=ApiResponse,
    summary="创建记录",
    description="创建新的记录"
)
async def create_item(
    item: YourModelCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user)  # 如果需要权限验证
):
    """创建记录接口"""
    try:
        service = YourService(db)
        result = service.create(item)
        
        return ApiResponse(
            code=200,
            message="创建成功",
            data={
                "id": result.id,
                "name": result.name
            }
        )
    except Exception as e:
        logger.error(f"创建记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建记录失败"
        )

@router.get(
    "/{item_id}",
    response_model=ApiResponse,
    summary="获取记录详情",
    description="根据ID获取记录详情"
)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """获取记录详情接口"""
    try:
        service = YourService(db)
        result = service.get_by_id(item_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记录不存在"
            )
        
        return ApiResponse(
            code=200,
            message="查询成功",
            data={
                "id": result.id,
                "name": result.name,
                "description": result.description,
                "status": result.status,
                "created_at": result.created_at.isoformat(),
                "updated_at": result.updated_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询记录失败"
        )

@router.post(
    "/list",
    response_model=ApiResponse,
    summary="获取记录列表",
    description="获取记录列表，支持分页和筛选"
)
async def get_item_list(
    query: YourModelQuery,
    db: Session = Depends(get_db)
):
    """获取记录列表接口"""
    try:
        service = YourService(db)
        items, total = service.get_list(query)
        
        # 构造响应数据
        items_data = [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "status": item.status,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat()
            }
            for item in items
        ]
        
        # 计算分页信息
        total_pages = (total + query.page_size - 1) // query.page_size
        
        return ApiResponse(
            code=200,
            message=f"查询成功，共找到 {total} 条记录",
            data={
                "items": items_data,
                "total": total,
                "page": query.page,
                "page_size": query.page_size,
                "total_pages": total_pages,
                "has_next": query.page < total_pages,
                "has_prev": query.page > 1
            }
        )
    except Exception as e:
        logger.error(f"查询列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询列表失败"
        )

@router.put(
    "/{item_id}",
    response_model=ApiResponse,
    summary="更新记录",
    description="根据ID更新记录"
)
async def update_item(
    item_id: int,
    item: YourModelUpdate,
    db: Session = Depends(get_db)
):
    """更新记录接口"""
    try:
        service = YourService(db)
        result = service.update(item_id, item)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记录不存在"
            )
        
        return ApiResponse(
            code=200,
            message="更新成功",
            data={
                "id": result.id,
                "name": result.name
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新记录失败"
        )

@router.delete(
    "/{item_id}",
    response_model=ApiResponse,
    summary="删除记录",
    description="根据ID删除记录"
)
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """删除记录接口"""
    try:
        service = YourService(db)
        success = service.delete(item_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="记录不存在"
            )
        
        return ApiResponse(
            code=200,
            message="删除成功",
            data={"id": item_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除记录失败"
        )
```

### 步骤5：注册路由

#### 5.1 在 `app/api/v1/__init__.py` 中添加：

```python
# 在文件顶部导入
from .your_api import router as your_api_router

# 在路由注册部分添加
api_router.include_router(
    your_api_router,
    prefix="/your-endpoint",  # 根据业务需求修改
    tags=["你的模块名称"]
)
```

#### 5.2 在 `app/main.py` 中添加：

```python
# 在导入部分添加
from app.api.v1 import your_api

# 在路由注册部分添加
app.include_router(your_api.router, prefix="/api/v1/your-endpoint", tags=["你的模块名称"])
```

## 问题3：还有哪些要注意的地方

### 1. 数据库相关注意事项

#### 数据库选择
- **主数据库**: 用于用户认证、系统配置等核心功能
- **中东数据库**: 专门用于中东用户相关业务
- **新数据库**: 如果业务独立，可以考虑新建数据库

#### 数据库连接配置
```python
# 如果需要新的数据库连接，在 app/config.py 中添加
NEW_DATABASE_URL: str = "mysql+pymysql://user:password@host:port/dbname"

# 创建对应的数据库连接文件 app/database_new.py
```

#### 表设计原则
- 遵循数据库设计规范（第三范式）
- 添加必要的索引提升查询性能
- 预留扩展字段（如 `extra_data` JSON字段）
- 统一时间字段命名（`created_at`, `updated_at`）

### 2. 性能优化注意事项

#### 查询优化
```python
# 使用索引字段进行查询
# 避免全表扫描
# 合理使用分页
# 考虑使用缓存

# 示例：添加缓存装饰器
from app.core.cache import cached_query

@cached_query(ttl=300)  # 缓存5分钟
def get_popular_items(self):
    return self.db.query(YourModel).filter(YourModel.status == 1).all()
```

#### 数据库连接池
```python
# 在数据库配置中优化连接池参数
engine = create_engine(
    database_url,
    pool_size=20,        # 连接池大小
    max_overflow=40,     # 最大溢出连接
    pool_timeout=30,     # 连接超时
    pool_recycle=1800    # 连接回收时间
)
```

### 3. 安全注意事项

#### 权限控制
```python
# 根据业务需求选择合适的权限验证
from app.api.deps import (
    get_current_active_user,    # 需要登录
    get_current_superuser,      # 需要超级管理员权限
    # 或自定义权限验证函数
)
```

#### 数据验证
```python
# 在 Schema 中添加严格的数据验证
from pydantic import validator, Field

class YourModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('名称不能为空')
        return v.strip()
```

#### SQL注入防护
```python
# 使用 SQLAlchemy ORM，避免拼接SQL
# 正确方式
query = db.query(YourModel).filter(YourModel.name == name)

# 错误方式（容易SQL注入）
# query = db.execute(f"SELECT * FROM table WHERE name = '{name}'")
```

### 4. 错误处理和日志

#### 统一异常处理
```python
# 在服务层添加详细的异常处理
try:
    # 业务逻辑
    pass
except SpecificException as e:
    logger.error(f"具体错误: {str(e)}")
    raise HTTPException(status_code=400, detail="具体错误信息")
except Exception as e:
    logger.error(f"未知错误: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="服务器内部错误")
```

#### 日志记录
```python
# 在关键操作点添加日志
logger.info(f"用户 {user_id} 创建了记录 {record_id}")
logger.warning(f"查询结果过多: {total_count} 条")
logger.error(f"数据库操作失败: {str(e)}")
```

### 5. 测试相关

#### 创建测试文件
```python
# tests/test_your_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_item():
    response = client.post(
        "/api/v1/your-endpoint/",
        json={"name": "测试名称", "description": "测试描述"}
    )
    assert response.status_code == 200
    assert response.json()["code"] == 200

def test_get_item():
    # 测试获取记录
    pass
```

### 6. 文档和注释

#### API文档
- 在路由函数中添加详细的 docstring
- 使用 Pydantic 的 `Field` 添加字段描述
- 在 `summary` 和 `description` 中提供清晰的接口说明

#### 代码注释
- 复杂业务逻辑添加注释说明
- 数据库字段添加 `comment` 参数
- 重要配置项添加说明注释

## 开发检查清单

### 开发前检查
- [ ] 确认业务需求和接口规范
- [ ] 设计数据库表结构
- [ ] 确定权限和安全要求
- [ ] 评估性能需求

### 开发中检查
- [ ] 创建数据模型（Model）
- [ ] 创建数据模式（Schema）
- [ ] 实现服务层（Service）
- [ ] 实现路由层（Router）
- [ ] 注册路由
- [ ] 添加错误处理
- [ ] 添加日志记录

### 开发后检查
- [ ] 单元测试通过
- [ ] API文档生成正确
- [ ] 性能测试达标
- [ ] 安全检查通过
- [ ] 代码审查完成

## 常见问题解决

### 1. 数据库连接问题
```bash
# 检查数据库连接
python -c "from app.database import engine; print(engine.execute('SELECT 1').scalar())"
```

### 2. 路由注册问题
```bash
# 检查路由是否注册成功
curl http://localhost:8000/docs
# 在 Swagger UI 中查看是否有新的接口
```

### 3. 权限验证问题
```python
# 临时禁用权限验证进行测试
# current_user: User = Depends(get_current_active_user)  # 注释掉这行
```

### 4. 数据验证问题
```python
# 在 Schema 中添加调试信息
class YourModelCreate(BaseModel):
    name: str
    
    @validator('name')
    def debug_name(cls, v):
        print(f"验证名称: {v}")  # 调试用，生产环境删除
        return v
```

## 完整开发示例

### 示例：创建"任务管理"API接口

假设我们要创建一个任务管理功能，包括创建任务、查询任务列表、更新任务状态等。

#### 第1步：创建数据模型文件
**文件位置**: `app/models/task.py`
```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Task(Base):
    """任务数据模型"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, comment="任务ID")
    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, nullable=True, comment="任务描述")
    status = Column(Integer, default=1, comment="状态：1-待处理，2-进行中，3-已完成")
    priority = Column(Integer, default=2, comment="优先级：1-高，2-中，3-低")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
```

#### 第2步：创建数据模式文件
**文件位置**: `app/schemas/task.py`
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    title: str = Field(..., description="任务标题", max_length=200)
    description: Optional[str] = Field(None, description="任务描述")
    priority: int = Field(2, description="优先级：1-高，2-中，3-低")

class TaskQuery(BaseModel):
    status: Optional[int] = Field(None, description="状态筛选")
    priority: Optional[int] = Field(None, description="优先级筛选")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页大小", ge=1, le=100)

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: int
    priority: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### 第3步：创建服务层文件
**文件位置**: `app/services/task_service.py`
```python
from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskQuery

class TaskService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, task_data: TaskCreate) -> Task:
        db_task = Task(**task_data.dict())
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
    
    def get_tasks(self, query: TaskQuery):
        db_query = self.db.query(Task)
        
        if query.status:
            db_query = db_query.filter(Task.status == query.status)
        if query.priority:
            db_query = db_query.filter(Task.priority == query.priority)
        
        total = db_query.count()
        offset = (query.page - 1) * query.page_size
        tasks = db_query.offset(offset).limit(query.page_size).all()
        
        return tasks, total
```

#### 第4步：创建API路由文件
**文件位置**: `app/api/v1/tasks.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskQuery, TaskResponse
from app.schemas.common import ApiResponse

router = APIRouter()

@router.post(
    "/",
    response_model=ApiResponse,
    summary="创建任务",
    description="创建新的任务"
)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):
    service = TaskService(db)
    result = service.create_task(task)
    
    return ApiResponse(
        code=200,
        message="任务创建成功",
        data={"id": result.id, "title": result.title}
    )

@router.post(
    "/list",
    response_model=ApiResponse,
    summary="获取任务列表",
    description="获取任务列表，支持分页和筛选"
)
async def get_task_list(
    query: TaskQuery,
    db: Session = Depends(get_db)
):
    service = TaskService(db)
    tasks, total = service.get_tasks(query)
    
    return ApiResponse(
        code=200,
        message=f"查询成功，共{total}条记录",
        data={
            "items": [TaskResponse.from_orm(task).dict() for task in tasks],
            "total": total,
            "page": query.page,
            "page_size": query.page_size
        }
    )
```

#### 第5步：注册路由
**在 `app/api/v1/__init__.py` 中添加**:
```python
from .tasks import router as tasks_router

api_router.include_router(
    tasks_router,
    prefix="/tasks",
    tags=["任务管理"]
)
```

#### 第6步：访问Swagger文档
启动应用后，访问 `http://localhost:8000/docs`，你会看到：
- 新增了"任务管理"分组
- 包含"创建任务"和"获取任务列表"两个接口
- 可以直接在页面测试接口功能

## 总结

通过遵循本指南，你可以快速开发出符合项目架构规范的API接口。关键要点：

1. **遵循分层架构**: Model → Service → Router → Schema
2. **统一响应格式**: 使用 `ApiResponse` 统一返回格式
3. **完善错误处理**: 添加详细的异常处理和日志记录
4. **注重性能**: 合理使用分页、索引和缓存
5. **保证安全**: 添加权限验证和数据验证
6. **完善测试**: 编写单元测试确保代码质量

如果在开发过程中遇到问题，可以参考现有的 `middle_east_user` 模块作为最佳实践示例。