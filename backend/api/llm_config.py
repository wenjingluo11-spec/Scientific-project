"""LLM Configuration API - 管理 LLM 配置"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import httpx

from models.database import get_db
from models.llm_config import LLMConfig
from services import llm_config_service
from config import settings

router = APIRouter()


# ==================== Request/Response Models ====================

class LLMConfigCreate(BaseModel):
    name: str
    provider: str = "anthropic"
    base_url: str
    api_key: str
    default_model: str
    max_tokens: int = 4096
    timeout: int = 120


class LLMConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None


class LLMConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    base_url: str
    api_key: str  # 脱敏后的
    default_model: str
    max_tokens: int
    timeout: int
    is_primary: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class TestConnectionRequest(BaseModel):
    base_url: str
    api_key: str
    model: str = "claude-haiku-4-5"


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    response_time_ms: Optional[int] = None


# ==================== API Endpoints ====================

@router.get("/", response_model=List[LLMConfigResponse])
async def get_all_configs(db: AsyncSession = Depends(get_db)):
    """获取所有 LLM 配置（API Key 脱敏）"""
    configs = await llm_config_service.get_all_configs(db)
    return [config.to_dict() for config in configs]


@router.get("/primary", response_model=Optional[LLMConfigResponse])
async def get_primary_config(db: AsyncSession = Depends(get_db)):
    """获取当前主配置"""
    config = await llm_config_service.get_primary_config(db)
    if not config:
        # 返回默认配置信息
        return {
            "id": 0,
            "name": "默认配置",
            "provider": "anthropic",
            "base_url": settings.ANTHROPIC_BASE_URL,
            "api_key": settings.ANTHROPIC_API_KEY[:8] + "****" + settings.ANTHROPIC_API_KEY[-4:],
            "default_model": settings.DEFAULT_MODEL,
            "max_tokens": settings.MAX_TOKENS,
            "timeout": settings.API_TIMEOUT,
            "is_primary": True,
            "created_at": None,
            "updated_at": None,
        }
    return config.to_dict()


@router.get("/{config_id}", response_model=LLMConfigResponse)
async def get_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个配置"""
    config = await llm_config_service.get_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config.to_dict()


@router.post("/", response_model=LLMConfigResponse)
async def create_config(
    config_data: LLMConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新 LLM 配置"""
    try:
        config = await llm_config_service.create_config(db, config_data.dict())
        return config.to_dict()
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail=f"配置名称 '{config_data.name}' 已存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{config_id}", response_model=LLMConfigResponse)
async def update_config(
    config_id: int,
    config_data: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新 LLM 配置"""
    config = await llm_config_service.update_config(
        db, config_id, config_data.dict(exclude_unset=True)
    )
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config.to_dict()


@router.delete("/{config_id}")
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """删除 LLM 配置"""
    success = await llm_config_service.delete_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"message": "配置已删除", "success": True}


@router.post("/{config_id}/set-primary", response_model=LLMConfigResponse)
async def set_primary(config_id: int, db: AsyncSession = Depends(get_db)):
    """设置为主配置"""
    config = await llm_config_service.set_primary_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config.to_dict()


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest):
    """测试 LLM API 连接"""
    import time
    
    # 构建请求
    base_url = request.base_url.rstrip('/')
    if base_url.endswith('/v1'):
        base_url = base_url[:-3]
    
    url = f"{base_url}/v1/messages"
    
    headers = {
        "x-api-key": request.api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": request.model,
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hi"}]
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return TestConnectionResponse(
                success=True,
                message="连接成功！API 可正常使用",
                response_time_ms=elapsed_ms
            )
        else:
            return TestConnectionResponse(
                success=False,
                message=f"API 返回错误: {response.status_code} - {response.text[:200]}",
                response_time_ms=elapsed_ms
            )
            
    except httpx.TimeoutException:
        return TestConnectionResponse(
            success=False,
            message="连接超时，请检查 Base URL 是否正确"
        )
    except httpx.ConnectError:
        return TestConnectionResponse(
            success=False,
            message="无法连接到服务器，请检查 Base URL"
        )
    except Exception as e:
        return TestConnectionResponse(
            success=False,
            message=f"连接失败: {str(e)}"
        )
