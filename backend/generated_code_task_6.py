# 任务ID: 6
# 任务标题: 商品库存管理API
# 生成时间: 2025-09-24 11:42:08

# === 数据模型 (models/stock.py) ===
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base

class ProductStock(Base):
    """商品库存模型"""
    __tablename__ = "product_stocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    product_id = Column(Integer, nullable=False, comment="商品ID")
    product_name = Column(String(200), nullable=False, comment="商品名称")
    current_stock = Column(Integer, default=0, comment="当前库存数量")
    reserved_stock = Column(Integer, default=0, comment="预留库存数量")
    alert_threshold = Column(Integer, default=10, comment="库存预警阈值")
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now(), comment="最后更新时间")
    
    # 创建索引
    __table_args__ = (
        Index("idx_product_id", "product_id", unique=True),
    )
    
    @property
    def available_stock(self):
        """可用库存 = 当前库存 - 预留库存"""
        return self.current_stock - self.reserved_stock
    
    @property
    def is_low_stock(self):
        """是否库存不足"""
        return self.available_stock <= self.alert_threshold
```

# === 数据模式 (schemas/stock.py) ===
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class StockBase(BaseModel):
    """库存基础模式"""
    product_id: int = Field(..., description="商品ID", gt=0)

class StockCreate(StockBase):
    """创建库存请求模式"""
    product_name: str = Field(..., description="商品名称", max_length=200)
    current_stock: int = Field(0, description="当前库存数量", ge=0)
    reserved_stock: int = Field(0, description="预留库存数量", ge=0)
    alert_threshold: int = Field(10, description="库存预警阈值", ge=1)
    
    @validator('reserved_stock')
    def validate_reserved_stock(cls, v, values):
        if 'current_stock' in values and v > values['current_stock']:
            raise ValueError('预留库存不能大于当前库存')
        return v

class StockUpdate(BaseModel):
    """更新库存请求模式"""
    quantity: Optional[int] = Field(None, description="库存数量")
    alert_threshold: Optional[int] = Field(None, description="库存预警阈值", ge=1)

class StockResponse(BaseModel):
    """库存响应模式"""
    product_id: int
    product_name: str
    current_stock: int
    reserved_stock: int
    alert_threshold: int
    available_stock: int
    is_low_stock: bool
    last_updated: datetime
    
    class Config:
        from_attributes = True

class StockQuery(BaseModel):
    """库存查询模式"""
    low_stock_only: bool = Field(False, description="是否只查询低库存商品")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页大小", ge=1, le=100)
```

# === 服务层 (services/stock_service.py) ===
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Tuple
import logging

from app.models.stock import ProductStock
from app.schemas.stock import StockCreate, StockUpdate, StockQuery

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_stock(self, stock_in: StockCreate) -> ProductStock:
        """创建商品库存记录"""
        try:
            # 检查是否已存在
            existing = self.db.query(ProductStock).filter(
                ProductStock.product_id == stock_in.product_id
            ).first()
            if existing:
                raise ValueError(f"商品ID {stock_in.product_id} 的库存记录已存在")
            
            db_stock = ProductStock(**stock_in.dict())
            self.db.add(db_stock)
            self.db.commit()
            self.db.refresh(db_stock)
            logger.info(f"创建商品 {stock_in.product_id} 的库存记录成功")
            return db_stock
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建库存记录失败: {str(e)}")
            raise
    
    def get_stock(self, product_id: int) -> Optional[ProductStock]:
        """获取商品库存信息"""
        return self.db.query(ProductStock).filter(
            ProductStock.product_id == product_id
        ).first()
    
    def update_stock(self, product_id: int, stock_update: StockUpdate) -> Optional[ProductStock]:
        """更新商品库存"""
        try:
            db_stock = self.get_stock(product_id)
            if not db_stock:
                return None
            
            update_data = stock_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_stock, field, value)
            
            self.db.commit()
            self.db.refresh(db_stock)
            logger.info(f"更新商品 {product_id} 的库存成功")
            return db_stock
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新库存失败: {str(e)}")
            raise
    
    def get_stock_list(self, query: StockQuery) -> Tuple[List[ProductStock], int]:
        """获取库存列表"""
        db_query = self.db.query(ProductStock)
        
        # 筛选低库存商品
        if query.low_stock_only:
            db_query = db_query.filter(
                ProductStock.current_stock - ProductStock.reserved_stock <= ProductStock.alert_threshold
            )
        
        total = db_query.count()
        offset = (query.page - 1) * query.page_size
        items = db_query.order_by(desc(ProductStock.last_updated)).offset(offset).limit(query.page_size).all()
        
        return items, total
```

# === 路由层 (api/v1/stock.py) ===
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.services.stock_service import StockService
from app.schemas.stock import (
    StockCreate, StockUpdate, StockQuery,
    StockResponse, StockBase
)
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/",
    response_model=ApiResponse,
    summary="创建商品库存",
    description="创建新的商品库存记录"
)
async def create_stock(
    stock: StockCreate,
    db: Session = Depends(get_db)
):
    try:
        service = StockService(db)
        result = service.create_stock(stock)
        return ApiResponse(
            code=200,
            message="创建库存记录成功",
            data=StockResponse.from_orm(result).dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建库存记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建库存记录失败")

@router.get(
    "/{product_id}",
    response_model=ApiResponse,
    summary="获取商品库存",
    description="根据商品ID获取库存信息"
)
async def get_stock(
    product_id: int,
    db: Session = Depends(get_db)
):
    try:
        service = StockService(db)
        result = service.get_stock(product_id)
        if not result:
            raise HTTPException(status_code=404, detail="商品库存记录不存在")
        
        return ApiResponse(
            code=200,
            message="查询成功",
            data=StockResponse.from_orm(result).dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询库存失败: {str(e)}")
        raise HTTPException(status_code=500, detail="查询库存失败")

@router.put(
    "/{product_id}",
    response_model=ApiResponse,
    summary="更新商品库存",
    description="更新商品库存信息"
)
async def update_stock(
    product_id: int,
    stock: StockUpdate,
    db: Session = Depends(get_db)
):
    try:
        service = StockService(db)
        result = service.update_stock(product_id, stock)
        if not result:
            raise HTTPException(status_code=404, detail="商品库存记录不存在")
        
        return ApiResponse(
            code=200,
            message="更新成功",
            data=StockResponse.from_orm(result).dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新库存失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新库存失败")

@router.post(
    "/list",
    response_model=ApiResponse,
    summary="获取库存列表",
    description="获取商品库存列表，支持分页和低库存筛选"
)
async def get_stock_list(
    query: StockQuery,
    db: Session = Depends(get_db)
):
    try:
        service = StockService(db)
        items, total = service.get_stock_list(query)
        
        return ApiResponse(
            code=200,
            message="查询成功",
            data={
                "items": [StockResponse.from_orm(item).dict() for item in items],
                "total": total,
                "page": query.page,
                "page_size": query.page_size
            }
        )
    except Exception as e:
        logger.error(f"查询库存列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="查询库存列表失败")
```