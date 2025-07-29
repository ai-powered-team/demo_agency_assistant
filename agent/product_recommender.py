"""
保险产品推荐器

使用 LangGraph 实现保险产品推荐的业务逻辑。
"""

from typing import AsyncGenerator, List, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from util import (
    config, logger, ProductRecommendationRequest, AgentResponse,
    ThinkingResponse, ErrorResponse, UserProfile,
    ProductInfo, ProductRecommendResponse
)
from util.database import db_manager
from util.product_search import ProductSearchEngine, analyze_user_characteristics
from util.product_generator import convert_to_product_info_with_llm, generate_product_recommend_response


class ProductRecommenderState(TypedDict):
    """产品推荐器状态类"""
    user_id: int
    session_id: int
    custom_profile: Optional[UserProfile]
    user_characteristics: Optional[Dict[str, Any]]
    searched_products: Optional[List[Dict[str, Any]]]
    recommended_products: Optional[List[ProductInfo]]
    recommendation_response: Optional[ProductRecommendResponse]


class ProductRecommender:
    """保险产品推荐器类"""

    def __init__(self):
        """初始化推荐器"""
        self.llm = ChatOpenAI(
            api_key=SecretStr(
                config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None,
            base_url=config.OPENAI_BASE_URL,
            model=config.OPENAI_MODEL,
            temperature=0.7
        )
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph[ProductRecommenderState, ProductRecommenderState, ProductRecommenderState]:
        """构建 LangGraph 工作流"""
        workflow = StateGraph(ProductRecommenderState)

        # 添加节点
        workflow.add_node("analyze_user_profile", self._analyze_user_profile)
        workflow.add_node("search_products", self._search_products)
        workflow.add_node("generate_recommendations",
                          self._generate_recommendations)

        # 设置入口点
        workflow.set_entry_point("analyze_user_profile")

        # 添加边
        workflow.add_edge("analyze_user_profile", "search_products")
        workflow.add_edge("search_products", "generate_recommendations")
        workflow.add_edge("generate_recommendations", END)

        return workflow.compile()

    async def _analyze_user_profile(self, state: ProductRecommenderState) -> ProductRecommenderState:
        """分析用户画像和特征"""
        logger.info("开始分析用户画像和特征")

        try:
            user_id = state["user_id"]
            session_id = state["session_id"]
            custom_profile = state.get("custom_profile")

            # 获取用户特征数据
            if custom_profile:
                # 使用自定义画像
                user_profile = custom_profile
                logger.info(f"使用自定义用户画像进行推荐，用户ID: {user_id}")
            else:
                # 从数据库读取用户特征
                profile_data = await db_manager.get_user_profile_for_recommendation(user_id, session_id)
                user_profile = profile_data.get('user_profile', {})
                logger.info(
                    f"从数据库读取用户画像，完成率: {profile_data.get('completion_rate', 0):.2%}")

            # 分析用户特征
            user_characteristics = analyze_user_characteristics(user_profile)
            state["user_characteristics"] = user_characteristics

            logger.info(f"用户特征分析完成: {user_characteristics}")

        except Exception as e:
            logger.error(f"用户画像分析失败: {e}")
            # 使用默认特征
            state["user_characteristics"] = {
                'age': 30,
                'gender': '不限',
                'user_type': 'unknown',
                'insurance_budget': 5000
            }

        return state

    async def _search_products(self, state: ProductRecommenderState) -> ProductRecommenderState:
        """搜索保险产品"""
        logger.info("开始搜索保险产品")

        try:
            user_characteristics = state.get("user_characteristics") or {}

            # 执行双阶段 ES 查询
            search_engine = ProductSearchEngine()
            try:
                # 第一阶段：推荐索引筛选 + 第二阶段：详细信息获取
                detailed_products = await search_engine.search_products_with_four_layer_matching(
                    user_characteristics,
                    limit=10  # 查询更多产品以便筛选
                )
                logger.info(f"双阶段查询返回 {len(detailed_products)} 个详细产品信息")

                state["searched_products"] = detailed_products

            finally:
                await search_engine.close()

        except Exception as e:
            logger.error(f"产品搜索失败: {e}")
            # 使用空列表作为后备
            state["searched_products"] = []

        return state

    async def _generate_recommendations(self, state: ProductRecommenderState) -> ProductRecommenderState:
        """生成推荐结果"""
        logger.info("生成最终推荐结果")

        try:
            user_characteristics = state.get("user_characteristics") or {}
            detailed_products = state.get("searched_products") or []

            # 使用 LLM 转换为 ProductInfo 格式
            recommended_products = []

            for product_detail in detailed_products[:5]:  # 只处理前5个产品
                try:
                    product_info = await convert_to_product_info_with_llm(
                        product_detail,
                        user_characteristics,
                        self.llm
                    )
                    recommended_products.append(product_info)
                    logger.info(f"成功生成产品推荐: {product_info['product_name']}")
                except Exception as e:
                    logger.error(
                        f"LLM 生成产品信息失败: {e}, 产品: {product_detail.get('product_id', 'unknown')}")
                    continue

            # 生成分析摘要
            analysis_summary = f"基于您的个人特征分析，为您推荐了 {len(recommended_products)} 款产品"

            # 生成推荐响应
            recommend_response = generate_product_recommend_response(
                products=recommended_products,
                analysis_summary=analysis_summary
            )

            state["recommended_products"] = recommended_products
            state["recommendation_response"] = ProductRecommendResponse(
                **recommend_response)

        except Exception as e:
            logger.error(f"生成推荐结果失败: {e}")
            # 生成错误响应
            error_response = ProductRecommendResponse(
                type="product_recommendation",
                products=[],
                message="推荐生成过程中出现错误，请稍后重试。",
                analysis_summary=None
            )
            state["recommendation_response"] = error_response
            state["recommended_products"] = []

        return state

    async def recommend_products(self, request: ProductRecommendationRequest) -> AsyncGenerator[AgentResponse, None]:
        """执行产品推荐"""
        try:
            # 初始化状态
            initial_state: ProductRecommenderState = {
                "user_id": request["user_id"],
                "session_id": request["session_id"],
                "custom_profile": request.get("custom_profile"),
                "user_characteristics": None,
                "searched_products": None,
                "recommended_products": None,
                "recommendation_response": None
            }

            # 执行工作流
            async for event in self.workflow.astream(initial_state):
                for node_name, node_output in event.items():
                    if node_name == "analyze_user_profile":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在分析您的个人特征和保险需求...",
                            step="user_analysis"
                        )
                    elif node_name == "search_products":
                        yield ThinkingResponse(
                            type="thinking",
                            content="正在搜索匹配的保险产品...",
                            step="product_search"
                        )
                    elif node_name == "generate_recommendations":
                        # 返回最终的产品推荐响应
                        recommendation_response = node_output.get(
                            "recommendation_response")
                        if recommendation_response:
                            yield ProductRecommendResponse(**recommendation_response)
                        else:
                            yield ErrorResponse(
                                type="error",
                                error="推荐生成失败",
                                details="未能生成有效的推荐结果"
                            )

        except Exception as e:
            logger.error(f"产品推荐过程中发生错误: {e}")
            yield ErrorResponse(
                type="error",
                error="推荐过程中发生错误",
                details=str(e)
            )
