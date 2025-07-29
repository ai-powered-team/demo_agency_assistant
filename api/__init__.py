"""
API 接口层模块

定义所有对外的 HTTP 接口。
"""

from fastapi import APIRouter
from .profile_analysis import router as profile_router
from .product_recommendation import router as product_router
from .agency_communication import router as agency_router
from .agency_recommendation import router as agency_recommend_router
from .agency_assistance import router as agency_assistant_router

# 创建主路由
router = APIRouter()

# 注册各个子路由
router.include_router(profile_router, prefix="/profile", tags=["用户画像分析"])
router.include_router(product_router, prefix="/product", tags=["保险产品推荐"])
router.include_router(agency_router, prefix="/agency", tags=["保险经纪人沟通"])
router.include_router(agency_recommend_router,
                      prefix="/agency", tags=["保险经纪人推荐"])
router.include_router(agency_assistant_router,
                      prefix="/agency", tags=["智能对话助理"])

__all__ = ["router"]
