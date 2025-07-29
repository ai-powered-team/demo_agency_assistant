"""
产品搜索引擎

基于 ElasticSearch 实现的产品推荐搜索引擎，支持双索引架构和四层匹配算法。
"""

import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime

from util import config, logger
from util.types import UserProfile


class ProductSearchEngine:
    """产品搜索引擎 - 基于 ElasticSearch 双索引架构"""

    def __init__(self):
        """初始化 ES 连接配置"""
        self.base_url = f"https://{config.ES_HOST}:{config.ES_PORT}"
        self.auth = aiohttp.BasicAuth(
            config.ES_USERNAME, config.ES_PASSWORD) if config.ES_USERNAME and config.ES_PASSWORD else None
        self.recommendation_index = config.ES_INDEX_PRODUCTS  # 推荐索引
        self.detail_index = config.ES_INDEX_ALL_PRODUCTS  # 详细信息索引

        # 创建连接器配置
        self.connector = aiohttp.TCPConnector(
            ssl=False,  # 忽略 SSL 证书验证
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                auth=self.auth
            )
        return self._session

    async def close(self):
        """关闭 ES 连接"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def health_check(self) -> bool:
        """检查 ES 连接健康状态"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/_cluster/health") as response:
                if response.status == 200:
                    health = await response.json()
                    logger.info(f"ES 集群状态: {health.get('status', 'unknown')}")
                    return True
                else:
                    logger.error(f"ES 健康检查失败，状态码: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"ES 健康检查失败: {e}")
            return False

    async def _ensure_connection(self) -> bool:
        """确保 ES 连接可用，如果连接断开则重新连接"""
        try:
            # 简单的连接测试
            session = await self._get_session()
            async with session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    return True
                else:
                    logger.warning(f"ES 连接测试失败，状态码: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"ES 连接测试失败: {e}")
            try:
                # 关闭旧会话并重新创建
                if self._session and not self._session.closed:
                    await self._session.close()
                self._session = None

                # 重新测试连接
                session = await self._get_session()
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        logger.info("ES 重新连接成功")
                        return True
                    else:
                        logger.error(f"ES 重新连接失败，状态码: {response.status}")
                        return False
            except Exception as reconnect_error:
                logger.error(f"ES 重新连接失败: {reconnect_error}")
                return False

    async def search_products_with_four_layer_matching(
        self,
        user_characteristics: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """基于四层匹配算法搜索产品 - 双阶段查询"""

        # 第一阶段：在推荐索引中进行四层匹配筛选
        product_ids = await self._search_recommendation_index(user_characteristics, limit)

        if not product_ids:
            return []

        # 第二阶段：从详细信息索引中获取完整产品信息
        detailed_products = await self._get_product_details(product_ids)

        return detailed_products

    async def _search_recommendation_index(
        self,
        user_characteristics: Dict[str, Any],
        limit: int
    ) -> List[str]:
        """第一阶段：在推荐索引中筛选产品ID"""

        age = user_characteristics.get('age')
        gender = user_characteristics.get('gender')
        industry = user_characteristics.get('industry')
        budget = user_characteristics.get('insurance_budget', 5000)
        user_type = user_characteristics.get('user_type')

        # 构建推荐查询
        query = {
            "size": limit,
            "_source": ["product_id"],  # 只返回 product_id
            "query": {
                "script_score": {
                    "query": {
                        "bool": {
                            "filter": self._build_hard_filters(age, gender, industry),
                            "should": self._build_soft_conditions(age, gender, industry, user_type)
                        }
                    },
                    "script": {
                        "source": self._build_scoring_script(),
                        "params": {
                            "user_age": age or 30,
                            "user_budget": budget,
                            "user_gender": gender or "不限",
                            "user_industry": industry or "其他",
                            "user_type": user_type or "unknown"
                        }
                    }
                }
            },
            "sort": [
                {"_score": {"order": "desc"}},
                {"cost_performance_score": {"order": "desc"}}
            ]
        }

        try:
            # 确保连接可用
            if not await self._ensure_connection():
                logger.error("ES 连接不可用，无法执行查询")
                return []

            # 使用 HTTP 请求执行搜索
            session = await self._get_session()
            headers = {"Content-Type": "application/json"}
            async with session.post(
                f"{self.base_url}/{self.recommendation_index}/_search",
                json=query,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"搜索请求失败，状态码: {response.status}, 错误: {error_text}")

                search_result = await response.json()

            # 提取 product_id 列表，保持排序
            product_ids = [hit['_source']['product_id']
                           for hit in search_result['hits']['hits']]
            logger.info(f"推荐索引筛选出 {len(product_ids)} 个产品")

            # 如果没有匹配到任何产品，执行兜底逻辑
            if not product_ids:
                logger.warning("没有匹配到任何产品，执行兜底逻辑")
                # 兜底返回 top 3
                product_ids = await self._fallback_search(user_characteristics, 3)

            return product_ids

        except Exception as e:
            logger.error(f"推荐索引查询失败: {e}")
            # 如果是连接错误，尝试重新连接后再试一次
            if "Connection" in str(e) or "ConnectionError" in str(e):
                logger.info("检测到连接错误，尝试重新连接后重试")
                if await self._ensure_connection():
                    try:
                        session = await self._get_session()
                        headers = {"Content-Type": "application/json"}
                        async with session.post(
                            f"{self.base_url}/{self.recommendation_index}/_search",
                            json=query,
                            headers=headers
                        ) as retry_response:
                            if retry_response.status == 200:
                                retry_result = await retry_response.json()
                                product_ids = [hit['_source']['product_id']
                                               for hit in retry_result['hits']['hits']]
                                logger.info(
                                    f"重试成功，推荐索引筛选出 {len(product_ids)} 个产品")
                                return product_ids
                    except Exception as retry_error:
                        logger.error(f"重试后仍然失败: {retry_error}")
            return []

    async def _fallback_search(
        self,
        user_characteristics: Dict[str, Any],
        limit: int = 3
    ) -> List[str]:
        """兜底逻辑：去除所有 must 约束条件，使用相同推荐算法选取 top 3"""

        age = user_characteristics.get('age')
        gender = user_characteristics.get('gender')
        industry = user_characteristics.get('industry')
        budget = user_characteristics.get('insurance_budget', 5000)
        user_type = user_characteristics.get('user_type')

        # 构建兜底查询：去除所有硬性筛选条件，只保留评分逻辑
        fallback_query = {
            "size": limit,
            "_source": ["product_id"],
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}  # 匹配所有产品，不设置任何硬性筛选条件
                    },
                    "script": {
                        "source": self._build_scoring_script(),
                        "params": {
                            "user_age": age or 30,
                            "user_budget": budget,
                            "user_gender": gender or "不限",
                            "user_industry": industry or "其他",
                            "user_type": user_type or "unknown"
                        }
                    }
                }
            },
            "sort": [
                {"_score": {"order": "desc"}},
                {"cost_performance_score": {"order": "desc"}}
            ]
        }

        try:
            # 确保连接可用
            if not await self._ensure_connection():
                logger.error("ES 连接不可用，兜底查询无法执行")
                return []

            session = await self._get_session()
            headers = {"Content-Type": "application/json"}
            async with session.post(
                f"{self.base_url}/{self.recommendation_index}/_search",
                json=fallback_query,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"兜底查询失败，状态码: {response.status}, 错误: {error_text}")

                search_result = await response.json()

            product_ids = [hit['_source']['product_id']
                           for hit in search_result['hits']['hits']]
            logger.info(f"兜底逻辑返回 {len(product_ids)} 个产品")
            return product_ids

        except Exception as e:
            logger.error(f"兜底查询也失败: {e}")
            return []

    async def _get_product_details(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """第二阶段：从详细信息索引中获取完整产品信息"""

        if not product_ids:
            return []

        # 构建批量查询
        query = {
            "size": len(product_ids),
            "query": {
                "terms": {
                    "product_id": product_ids
                }
            }
        }

        try:
            # 确保连接可用
            if not await self._ensure_connection():
                logger.error("ES 连接不可用，无法获取产品详情")
                return []

            session = await self._get_session()
            headers = {"Content-Type": "application/json"}
            async with session.post(
                f"{self.base_url}/{self.detail_index}/_search",
                json=query,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"产品详情查询失败，状态码: {response.status}, 错误: {error_text}")

                search_result = await response.json()

            # 按照原始排序重新排列结果
            products_dict = {hit['_source']['product_id']: hit['_source']
                             for hit in search_result['hits']['hits']}
            ordered_products = []

            for product_id in product_ids:
                if product_id in products_dict:
                    ordered_products.append(products_dict[product_id])

            logger.info(f"详细信息索引返回 {len(ordered_products)} 个产品详情")
            return ordered_products

        except Exception as e:
            logger.error(f"详细信息索引查询失败: {e}")
            # 如果是连接错误，尝试重新连接后再试一次
            if "Connection" in str(e) or "ConnectionError" in str(e):
                logger.info("检测到连接错误，尝试重新连接后重试")
                if await self._ensure_connection():
                    try:
                        session = await self._get_session()
                        headers = {"Content-Type": "application/json"}
                        async with session.post(
                            f"{self.base_url}/{self.detail_index}/_search",
                            json=query,
                            headers=headers
                        ) as retry_response:
                            if retry_response.status == 200:
                                retry_result = await retry_response.json()
                                products_dict = {hit['_source']['product_id']: hit['_source']
                                                 for hit in retry_result['hits']['hits']}
                                ordered_products = []
                                for product_id in product_ids:
                                    if product_id in products_dict:
                                        ordered_products.append(
                                            products_dict[product_id])
                                logger.info(
                                    f"重试成功，详细信息索引返回 {len(ordered_products)} 个产品详情")
                                return ordered_products
                    except Exception as retry_error:
                        logger.error(f"重试后仍然失败: {retry_error}")
            return []

    def _build_hard_filters(self, age: Optional[int], gender: Optional[str], _industry: Optional[str]) -> List[Dict]:
        """构建硬性筛选条件"""
        filters = []

        # 年龄筛选
        if age:
            filters.extend([
                {"range": {"age_range.min_age": {"lte": age}}},
                {"range": {"age_range.max_age": {"gte": age}}}
            ])

        # 性别筛选
        if gender:
            filters.append({
                "terms": {"gender_requirement": [gender, "不限"]}
            })

        # 职业筛选（黑名单模式）
        filters.append({
            "bool": {
                "must_not": [
                    {"terms": {"excluded_occupations": ["高危职业", "特殊职业"]}}
                ]
            }
        })

        # 地区筛选（支持全国的产品）
        filters.append({
            "bool": {
                "should": [
                    {"term": {"regions": "不限地区"}},
                    {"match": {"regions": {"query": "全国", "fuzziness": "AUTO"}}}
                ]
            }
        })

        return filters

    def _build_soft_conditions(self, age: Optional[int], _gender: Optional[str], _industry: Optional[str], user_type: Optional[str]) -> List[Dict]:
        """构建软性匹配条件"""
        conditions = []

        # 基于用户类型的偏好
        if user_type == 'tech_young':
            conditions.extend([
                {"terms": {"value_added_services": [
                    "在线问诊", "智能核保"], "boost": 2.0}},
                {"terms": {"company": ["众安保险", "蚂蚁保险"], "boost": 1.5}},
                {"range": {"renewal.guaranteed_renewal_years": {"gte": 15, "boost": 2.0}}}
            ])
        elif user_type == 'family_oriented':
            conditions.extend([
                {"terms": {"value_added_services": [
                    "就医绿通", "费用垫付"], "boost": 2.0}},
                {"range": {"coverage.general_medical.amount": {
                    "gte": 3000000, "boost": 1.5}}}
            ])
        elif user_type == 'high_income':
            conditions.extend([
                {"exists": {"field": "coverage.vip_medical", "boost": 2.0}},
                {"terms": {"company": ["太平洋健康险", "平安健康险"], "boost": 1.5}}
            ])

        # 年轻人偏好
        if age and age < 35:
            conditions.extend([
                {"range": {"renewal.guaranteed_renewal_years": {"gte": 15, "boost": 1.5}}},
                {"term": {"renewal.renewal_underwriting_required": {
                    "value": False, "boost": 1.0}}}
            ])

        return conditions

    def _build_scoring_script(self) -> str:
        """构建评分脚本"""
        return """
            double total_score = _score;
            
            // 第二层：需求匹配（保障契合度）
            double coverage_score = 0;
            double expected_general_amount = params.user_budget * 600;
            double expected_ci_amount = params.user_budget * 800;
            
            if (doc['coverage.general_medical.amount'].size() > 0) {
                double amount = doc['coverage.general_medical.amount'].value;
                coverage_score += Math.min(amount / expected_general_amount, 1.0) * 30;
            }
            
            if (doc['coverage.critical_illness.amount'].size() > 0) {
                double amount = doc['coverage.critical_illness.amount'].value;
                coverage_score += Math.min(amount / expected_ci_amount, 1.0) * 25;
            }
            
            if (doc['coverage.general_medical.deductible'].size() > 0) {
                double deductible = doc['coverage.general_medical.deductible'].value;
                double max_acceptable_deductible = params.user_budget * 2;
                coverage_score += Math.max(0, (max_acceptable_deductible - deductible) / max_acceptable_deductible) * 20;
            }
            
            if (doc['coverage.general_medical.reimbursement_rate_with_social'].size() > 0) {
                double rate = doc['coverage.general_medical.reimbursement_rate_with_social'].value;
                coverage_score += rate * 25;
            }
            
            // 第三层：偏好匹配（个性化适配）
            double preference_score = 0;
            
            if (doc['renewal.guaranteed_renewal_years'].size() > 0) {
                double years = doc['renewal.guaranteed_renewal_years'].value;
                preference_score += Math.min(years / 20.0, 1.0) * 50;
            }
            
            // 第四层：价值匹配（性价比优化）
            double value_score = 0;
            
            // 根据年龄获取保费
            double premium = 0;
            int user_age = params.user_age;
            if (user_age >= 25 && user_age < 30 && doc['premium.age_25'].size() > 0) {
                premium = doc['premium.age_25'].value;
            } else if (user_age >= 20 && user_age < 25 && doc['premium.age_20'].size() > 0) {
                premium = doc['premium.age_20'].value;
            } else if (user_age >= 30 && user_age < 35 && doc['premium.age_30'].size() > 0) {
                premium = doc['premium.age_30'].value;
            }
            
            // 预算匹配度（确保不产生负分）
            if (premium > 0) {
                if (premium <= params.user_budget) {
                    // 在预算内，给予正分
                    value_score += (params.user_budget - premium) / params.user_budget * 35;
                } else {
                    // 超出预算，降低分数但不产生负分
                    double over_budget_ratio = (premium - params.user_budget) / params.user_budget;
                    if (over_budget_ratio <= 0.2) {
                        // 轻微超预算，轻微降分
                        value_score += Math.max(0, 35 - over_budget_ratio * 50);
                    } else {
                        // 严重超预算，给予最低分但不为负
                        value_score += Math.max(0, 15 - (over_budget_ratio - 0.2) * 30);
                    }
                }
            }
            
            // 性价比评分
            if (doc['cost_performance_score'].size() > 0) {
                value_score += doc['cost_performance_score'].value * 0.4;
            }
            
            // 综合评分
            if (doc['overall_rating'].size() > 0) {
                value_score += doc['overall_rating'].value * 0.3;
            }
            
            // 确保最终分数为非负数
            double final_score = total_score + coverage_score + preference_score + value_score;
            return Math.max(0.0, final_score);
        """


def analyze_user_characteristics(user_profile: UserProfile) -> Dict[str, Any]:
    """分析用户特征，生成推荐策略参数"""
    analysis = {
        'age': None,
        'gender': user_profile.get('gender'),
        'marital_status': user_profile.get('marital_status'),
        'industry': user_profile.get('industry'),
        'annual_income': user_profile.get('annual_total_income'),
        'insurance_budget': user_profile.get('annual_insurance_budget'),
        'health_status': user_profile.get('overall_health_status'),
        'has_chronic_disease': user_profile.get('has_chronic_disease'),
        'user_type': 'unknown',
        'risk_preference': 'moderate',
        'budget_sensitivity': 'medium'
    }

    # 计算年龄
    date_of_birth = user_profile.get('date_of_birth')
    if date_of_birth:
        try:
            birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d')
            today = datetime.now()
            analysis['age'] = today.year - birth_date.year - \
                ((today.month, today.day) < (birth_date.month, birth_date.day))
        except (ValueError, TypeError) as e:
            logger.warning(f"解析出生日期失败: {e}")
            analysis['age'] = None

    # 用户类型分析（基于行业、收入、年龄等）
    if analysis['industry'] == '互联网' and analysis['age'] and analysis['age'] < 35:
        analysis['user_type'] = 'tech_young'  # 年轻互联网从业者
    elif analysis['annual_income'] and analysis['annual_income'] > 50:
        analysis['user_type'] = 'high_income'  # 高收入人群
    elif analysis['age'] and analysis['age'] < 30:
        analysis['user_type'] = 'young_professional'  # 年轻专业人士
    elif analysis['marital_status'] == '已婚' and (user_profile.get('number_of_children') or 0) > 0:
        analysis['user_type'] = 'family_oriented'  # 家庭导向

    # 风险偏好分析
    if analysis['age'] and analysis['age'] < 30:
        analysis['risk_preference'] = 'aggressive'  # 年轻人更激进
    elif analysis['has_chronic_disease'] and analysis['has_chronic_disease'] != '无':
        analysis['risk_preference'] = 'conservative'  # 有慢性病更保守
    elif analysis['annual_income'] and analysis['annual_income'] > 30:
        analysis['risk_preference'] = 'moderate_aggressive'  # 中高收入适中偏激进

    # 预算敏感度分析
    if analysis['insurance_budget'] and analysis['annual_income']:
        budget_ratio = analysis['insurance_budget'] / analysis['annual_income']
        if budget_ratio > 0.05:  # 预算占收入5%以上
            analysis['budget_sensitivity'] = 'low'
        elif budget_ratio < 0.02:  # 预算占收入2%以下
            analysis['budget_sensitivity'] = 'high'

    return analysis
