"""
产品信息生成器

使用 LLM 从详细产品信息中生成用户友好的产品推荐信息。
"""

import json
import re
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from util import logger
from util.types import ProductInfo


async def convert_to_product_info_with_llm(
    product_detail: Dict[str, Any],
    user_characteristics: Dict[str, Any],
    llm_client: Any
) -> ProductInfo:
    """使用 LLM 将详细产品数据转换为 ProductInfo 格式"""

    # 提取关键信息用于 LLM 处理
    key_info = _extract_key_product_info(product_detail)

    # 构建 LLM prompt
    prompt = _build_product_info_prompt(key_info, user_characteristics)

    # 调用 LLM 生成产品信息
    try:
        response = await llm_client.ainvoke([
            SystemMessage(
                content="你是一个专业的保险产品分析师，需要根据产品详细信息和用户特征，生成简洁易懂的产品推荐信息。"),
            HumanMessage(content=prompt)
        ])

        # 解析 LLM 响应
        product_info = _parse_llm_response(response.content, product_detail)
        return product_info

    except Exception as e:
        logger.error(f"LLM 生成产品信息失败: {e}")
        # 降级到规则生成
        return _fallback_convert_to_product_info(product_detail, user_characteristics)


def _extract_key_product_info(product_detail: Dict[str, Any]) -> Dict[str, Any]:
    """从详细产品信息中提取关键信息"""

    key_info = {
        'product_id': product_detail.get('product_id', ''),
        'product_name': product_detail.get('product_name', product_detail.get('product_id', '')),
        'company': product_detail.get('company', ''),
        'age_limit': product_detail.get('applyRules_insureRules_Age', ''),
        'occupation_limit': product_detail.get('applyRules_insureRules_Occupation', ''),
        'region_limit': product_detail.get('applyRules_insureRules_Region', ''),
        'guaranteed_renewal': product_detail.get('renewalRules_GuaranteedRenewalLongTermCoverage', ''),
        'max_renewal_age': product_detail.get('renewalRules_MaxRenewalAge', ''),
        'value_added_services': product_detail.get('claimDescriptionList_ValueAddedService', ''),
        'deductible_info': product_detail.get('claimDescriptionList_SumInsuredAndDeductibleSharing', ''),
        'hospital_scope': product_detail.get('claimDescriptionList_HospitalScope', ''),
    }

    # 提取保障内容信息，这个信息可能为空字符串
    coverage_details = product_detail.get('coverage_details') or {}
    coverage_summary = []

    for key, value in coverage_details.items():
        if 'GeneralMedPymt' in key:
            coverage_summary.append(f"一般医疗: {value}")
        elif 'CIMedPymt' in key:
            coverage_summary.append(f"重疾医疗: {value}")

    key_info['coverage_summary'] = '; '.join(coverage_summary[:3])  # 只取前3个

    return key_info


def _build_product_info_prompt(key_info: Dict[str, Any], user_characteristics: Dict[str, Any]) -> str:
    """构建 LLM prompt"""

    user_age = user_characteristics.get('age', '未知')
    user_gender = user_characteristics.get('gender', '未知')
    user_budget = user_characteristics.get('insurance_budget', '未知')
    user_type = user_characteristics.get('user_type', '未知')

    prompt = f"""
请根据以下产品信息和用户特征，生成产品推荐信息：

产品信息：
- 产品名称：{key_info['product_name']}
- 保险公司：{key_info['company']}
- 投保年龄：{key_info['age_limit']}
- 职业限制：{key_info['occupation_limit']}
- 保证续保：{key_info['guaranteed_renewal']}
- 保障内容：{key_info['coverage_summary']}
- 增值服务：{key_info['value_added_services']}
- 免赔额信息：{key_info['deductible_info']}

用户特征：
- 年龄：{user_age}岁
- 性别：{user_gender}
- 预算：{user_budget}元/年
- 用户类型：{user_type}

请按以下JSON格式输出：
{{
    "product_name": "产品名称",
    "product_description": "产品简介（50字以内，突出核心保障和特色）",
    "product_type": "产品类型（如：医疗险、重疾险等）",
    "recommendation": "推荐理由（80字以内，结合用户特征说明为什么推荐这款产品）"
}}

要求：
1. 产品简介要简洁明了，突出核心保障
2. 推荐理由要个性化，结合用户的年龄、性别、预算等特征
3. 语言要通俗易懂，避免专业术语
4. 确保信息准确，不要编造不存在的保障内容
"""

    return prompt


def _parse_llm_response(llm_response: str, product_detail: Dict[str, Any]) -> ProductInfo:
    """解析 LLM 响应并生成 ProductInfo"""

    try:
        # 提取 JSON 部分
        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            parsed_data = json.loads(json_str)

            return ProductInfo(
                product_name=parsed_data.get('product_name', product_detail.get(
                    'product_name', product_detail.get('product_id', ''))),
                product_description=parsed_data.get('product_description', ''),
                product_type=parsed_data.get('product_type', '医疗险'),
                recommendation=parsed_data.get('recommendation', '')
            )
    except Exception as e:
        logger.error(f"解析 LLM 响应失败: {e}")

    # 解析失败时的降级处理
    return _fallback_convert_to_product_info(product_detail, {})


def _fallback_convert_to_product_info(
    product_detail: Dict[str, Any],
    user_characteristics: Dict[str, Any]
) -> ProductInfo:
    """降级的产品信息转换方法"""

    product_name = product_detail.get(
        'product_name', product_detail.get('product_id', '未知产品'))

    # 简单的描述生成
    description_parts = []
    if product_detail.get('renewalRules_GuaranteedRenewalLongTermCoverage'):
        renewal_years = product_detail['renewalRules_GuaranteedRenewalLongTermCoverage']
        description_parts.append(f"保证续保{renewal_years}")

    if product_detail.get('claimDescriptionList_ValueAddedService'):
        services = product_detail['claimDescriptionList_ValueAddedService']
        if '就医绿通' in services:
            description_parts.append("含就医绿通")

    description = "，".join(
        description_parts) if description_parts else "医疗保障计划"

    return ProductInfo(
        product_name=product_name,
        product_description=description,
        product_type='医疗险',
        recommendation='根据您的需求推荐此产品'
    )


def generate_product_recommend_response(
    products: List[ProductInfo],
    analysis_summary: Optional[str] = None
) -> Dict[str, Any]:
    """生成产品推荐响应"""

    if not products:
        return {
            "type": "product_recommendation",
            "products": [],
            "message": "抱歉，暂时没有找到合适的产品推荐，请完善您的个人信息后重试。",
            "analysis_summary": None
        }

    # 生成推荐消息
    product_count = len(products)
    if product_count == 1:
        message = f"根据您的个人情况，为您推荐了 {product_count} 款优质保险产品。"
    else:
        message = f"根据您的个人情况，为您精选了 {product_count} 款优质保险产品，按推荐度排序。"

    return {
        "type": "product_recommendation",
        "products": [dict(p) for p in products],
        "message": message,
        "analysis_summary": analysis_summary
    }
