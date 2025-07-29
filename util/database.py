"""
数据库模型和管理器

提供 SQLAlchemy 模型定义和数据库操作管理器，支持 SQLite/MySQL 双环境。
"""

from typing import Optional, List, Dict, Any, cast
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import select, update
from datetime import datetime, timezone

from util import config, logger
from util.types import FeatureData, UserProfile

Base = declarative_base()


class UserProfileModel(Base):
    """用户特征表模型"""
    __tablename__ = 'user_profile'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    category_name = Column(String(255), nullable=False, index=True)
    feature_name = Column(String(255), nullable=False)
    feature_value = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    skipped = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('user_id', 'session_id', 'category_name', 'feature_name',
                         name='uq_user_session_category_feature'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
    )


class DatabaseManager:
    """数据库管理器 - 支持 SQLite/MySQL 双环境"""

    def __init__(self):
        """初始化数据库管理器"""
        self.engine = None
        self.session_factory = None
        self._is_sqlite = False

    async def initialize(self) -> async_sessionmaker:
        """初始化数据库连接"""
        try:
            # 根据环境选择数据库
            db_url = config.get_db_url()
            if db_url:
                # 生产环境使用 MySQL
                self.engine = create_async_engine(
                    db_url,
                    echo=config.DEBUG,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                self._is_sqlite = False
                logger.info("使用 MySQL 数据库")
            else:
                # 开发环境使用 SQLite
                sqlite_url = "sqlite+aiosqlite:///./ai_insurance.db"
                self.engine = create_async_engine(
                    sqlite_url,
                    echo=config.DEBUG
                )
                self._is_sqlite = True
                logger.info("使用 SQLite 数据库")

            # 创建会话工厂
            session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # 创建表
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("数据库初始化完成")
            return session_factory

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        if not self.session_factory:
            self.session_factory = await self.initialize()

        return self.session_factory()

    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")

    async def upsert_user_feature(
        self,
        user_id: int,
        session_id: int,
        category_name: str,
        feature_name: str,
        feature_value: Any,
        confidence: float,
        skipped: bool = False
    ) -> bool:
        """插入或更新用户特征"""
        try:
            async with await self.get_session() as session:
                # 构建 UPSERT 语句
                if self._is_sqlite:
                    # SQLite 使用 INSERT OR REPLACE
                    # 先尝试查找现有记录
                    existing_query = select(UserProfileModel).where(
                        UserProfileModel.user_id == user_id,
                        UserProfileModel.session_id == session_id,
                        UserProfileModel.category_name == category_name,
                        UserProfileModel.feature_name == feature_name
                    )
                    result = await session.execute(existing_query)
                    existing = result.scalar_one_or_none()

                    if existing:
                        # 更新现有记录
                        update_stmt = update(UserProfileModel).where(
                            UserProfileModel.id == existing.id
                        ).values(
                            feature_value=feature_value,
                            confidence=confidence,
                            skipped=skipped,
                            updated_at=datetime.now(timezone.utc)
                        )
                        await session.execute(update_stmt)
                    else:
                        # 插入新记录
                        new_record = UserProfileModel(
                            user_id=user_id,
                            session_id=session_id,
                            category_name=category_name,
                            feature_name=feature_name,
                            feature_value=feature_value,
                            confidence=confidence,
                            skipped=skipped
                        )
                        session.add(new_record)
                else:
                    # MySQL 使用 INSERT ... ON DUPLICATE KEY UPDATE
                    stmt = mysql_insert(UserProfileModel).values(
                        user_id=user_id,
                        session_id=session_id,
                        category_name=category_name,
                        feature_name=feature_name,
                        feature_value=feature_value,
                        confidence=confidence,
                        skipped=skipped,
                        updated_at=datetime.now(timezone.utc)
                    )
                    stmt = stmt.on_duplicate_key_update(
                        feature_value=stmt.inserted.feature_value,
                        confidence=stmt.inserted.confidence,
                        skipped=stmt.inserted.skipped,
                        updated_at=stmt.inserted.updated_at
                    )
                    await session.execute(stmt)

                await session.commit()
                return True

        except Exception as e:
            logger.error(f"更新用户特征失败: {e}")
            return False

    async def get_user_features(
        self,
        user_id: int,
        session_id: int,
        category_name: Optional[str] = None
    ) -> List[FeatureData]:
        """获取用户特征"""
        try:
            async with await self.get_session() as session:
                query = select(UserProfileModel).where(
                    UserProfileModel.user_id == user_id,
                    UserProfileModel.session_id == session_id)

                if category_name:
                    query = query.where(
                        UserProfileModel.category_name == category_name)

                result = await session.execute(query)
                features: List[FeatureData] = [
                    {
                        "category_name": cast(str, feature.category_name),
                        "feature_name": cast(str, feature.feature_name),
                        "feature_value": feature.feature_value,
                        "confidence": cast(float, feature.confidence or 0.0),
                        "skipped": cast(bool, feature.skipped or False),
                    }
                    for feature in result.scalars().all()
                ]
                return features

        except Exception as e:
            logger.error(f"获取用户特征失败: {e}")
            return []

    async def get_user_profile_summary(self, user_id: int, session_id: int) -> Dict[str, Any]:
        """获取用户画像摘要"""
        try:
            features = await self.get_user_features(user_id, session_id)

            total_features = 0
            completed_features = 0
            profile = {}

            for feature in features:
                feature_name = feature['feature_name']
                profile[feature_name] = feature
                total_features += 1
                if not feature['skipped'] and feature['confidence'] > 0:
                    completed_features += 1

            # 计算完成率
            completion_rate = completed_features / \
                total_features if total_features > 0 else 0.0

            return {
                'profile': profile,
                'completion_rate': completion_rate,
                'total_features': total_features,
                'completed_features': completed_features
            }

        except Exception as e:
            logger.error(f"获取用户画像摘要失败: {e}")
            return {
                'profile': {},
                'completion_rate': 0.0,
                'total_features': 0,
                'completed_features': 0
            }

    async def get_user_profile_for_recommendation(self, user_id: int, session_id: int) -> Dict[str, Any]:
        """获取用于产品推荐的用户画像数据"""
        try:
            # 获取用户特征摘要
            profile_summary = await self.get_user_profile_summary(user_id, session_id)

            # 转换为标准化的用户画像格式
            user_profile = self._convert_to_user_profile(
                profile_summary['profile'])

            return {
                'user_profile': user_profile,
                'completion_rate': profile_summary['completion_rate'],
                'total_features': profile_summary['total_features'],
                'completed_features': profile_summary['completed_features']
            }
        except Exception as e:
            logger.error(f"获取用户推荐画像失败: {e}")
            return {
                'user_profile': {},
                'completion_rate': 0.0,
                'total_features': 0,
                'completed_features': 0
            }

    def _convert_to_user_profile(self, profile_data: Dict[str, Any]) -> UserProfile:
        """将数据库中的特征数据转换为标准UserProfile格式

        Args:
            profile_data: 扁平结构的特征数据，格式为 {feature_name: feature_data}
                         其中 feature_data 包含 'feature_value', 'confidence', 'skipped' 等字段
        """
        user_profile: UserProfile = {}

        # 遍历所有特征数据，直接从扁平结构中提取
        for feature_name, feature_data in profile_data.items():
            if isinstance(feature_data, dict) and 'feature_value' in feature_data:
                # 检查特征是否被跳过或置信度过低
                if feature_data.get('skipped', False):
                    continue
                if feature_data.get('confidence', 0) <= 0:
                    continue

                feature_value = feature_data['feature_value']
                if feature_value is not None:
                    # 直接将特征值赋给用户画像
                    # 这里我们假设 feature_name 与 UserProfile 中的字段名一致
                    if feature_name in [
                        # 基础身份维度
                        'name', 'gender', 'date_of_birth', 'marital_status',
                        'residence_city', 'occupation_type', 'industry',
                        # 女性特殊状态维度
                        'pregnancy_status', 'childbearing_plan',
                        # 家庭结构与责任维度
                        'family_structure', 'number_of_children', 'caregiving_responsibility',
                        'monthly_household_expense', 'mortgage_balance', 'is_family_financial_support',
                        # 财务现状与目标维度
                        'annual_total_income', 'income_stability', 'annual_insurance_budget',
                        # 健康与生活习惯维度
                        'overall_health_status', 'has_chronic_disease', 'smoking_status', 'recent_medical_checkup'
                    ]:
                        user_profile[feature_name] = feature_value

        return user_profile


# 全局数据库管理器实例
db_manager = DatabaseManager()
