# AI保险平台产品推荐系统 - ES索引设计规范

## 1. 索引概述

本系统采用双索引架构，分别用于产品推荐筛选和详细信息存储：

### 1.1 推荐索引

**索引名称**: `insurance_products`
**数据源**: `/data/products/table_main_translated/` 目录下的产品JSON文件
**索引用途**: 支持保险产品推荐系统的四层匹配算法，包含用于筛选和评分的关键字段

### 1.2 详细信息索引

**索引名称**: `all_products`
**数据源**: `/data/products/table_main_translated/` 目录下的产品JSON文件
**索引用途**: 存储产品的完整详细信息，用于根据 product_id 获取具体产品内容

## 2. 索引映射定义

### 2.1 推荐索引 (insurance_products) 映射

```json
{
  "mappings": {
    "properties": {
      "product_id": {"type": "keyword"},
      "product_name": {"type": "text", "analyzer": "ik_max_word"},
      "company": {"type": "keyword"},
      "product_type": {"type": "keyword"},
      "status": {"type": "keyword"},
      "update_time": {"type": "date"},
      
      "age_range": {
        "properties": {
          "min_age": {"type": "integer"},
          "max_age": {"type": "integer"}
        }
      },
      "occupation_types": {"type": "keyword"},
      "excluded_occupations": {"type": "keyword"},
      "regions": {"type": "keyword"},
      "excluded_regions": {"type": "keyword"},
      "gender_requirement": {"type": "keyword"},
      "social_security_requirement": {"type": "keyword"},
      
      "coverage": {
        "properties": {
          "general_medical": {
            "properties": {
              "amount": {"type": "long"},
              "deductible": {"type": "long"},
              "reimbursement_rate_with_social": {"type": "float"},
              "reimbursement_rate_without_social": {"type": "float"}
            }
          },
          "critical_illness": {
            "properties": {
              "amount": {"type": "long"},
              "deductible": {"type": "long"},
              "disease_count": {"type": "integer"},
              "reimbursement_rate_with_social": {"type": "float"},
              "reimbursement_rate_without_social": {"type": "float"}
            }
          },
          "special_disease": {
            "properties": {
              "amount": {"type": "long"},
              "deductible": {"type": "long"},
              "disease_count": {"type": "integer"},
              "reimbursement_rate_with_social": {"type": "float"},
              "reimbursement_rate_without_social": {"type": "float"}
            }
          },
          "external_drug": {
            "properties": {
              "amount": {"type": "long"},
              "deductible": {"type": "long"},
              "drug_count": {"type": "integer"},
              "reimbursement_rate": {"type": "float"}
            }
          },
          "proton_heavy_ion": {
            "properties": {
              "amount": {"type": "long"},
              "deductible": {"type": "long"},
              "reimbursement_rate": {"type": "float"}
            }
          },
          "vip_medical": {
            "properties": {
              "amount": {"type": "long"},
              "deductible": {"type": "long"},
              "reimbursement_rate": {"type": "float"}
            }
          },
          "maternity": {
            "properties": {
              "amount": {"type": "long"},
              "deductible": {"type": "long"},
              "reimbursement_rate": {"type": "float"}
            }
          }
        }
      },
      
      "renewal": {
        "properties": {
          "guaranteed_renewal_years": {"type": "integer"},
          "max_renewal_age": {"type": "integer"},
          "renewal_underwriting_required": {"type": "boolean"},
          "rate_adjustable": {"type": "boolean"}
        }
      },
      
      "premium": {
        "properties": {
          "age_0": {"type": "float"},
          "age_5": {"type": "float"},
          "age_10": {"type": "float"},
          "age_15": {"type": "float"},
          "age_20": {"type": "float"},
          "age_25": {"type": "float"},
          "age_30": {"type": "float"},
          "age_35": {"type": "float"},
          "age_40": {"type": "float"},
          "age_45": {"type": "float"},
          "age_50": {"type": "float"},
          "age_55": {"type": "float"},
          "age_60": {"type": "float"},
          "age_65": {"type": "float"},
          "age_70": {"type": "float"}
        }
      },
      
      "value_added_services": {"type": "keyword"},
      "product_tags": {"type": "keyword"},
      "target_groups": {"type": "keyword"},
      
      "overall_rating": {"type": "float"},
      "cost_performance_score": {"type": "float"},
      "coverage_completeness_score": {"type": "float"},
      "renewal_stability_score": {"type": "float"},
      "service_quality_score": {"type": "float"}
    }
  },
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "analysis": {
      "analyzer": {
        "ik_max_word": {
          "type": "ik_max_word"
        }
      }
    }
  }
}
```

### 2.2 详细信息索引 (all_products) 映射

```json
{
  "mappings": {
    "properties": {
      "product_id": {"type": "keyword"},
      "product_name": {"type": "text", "analyzer": "ik_max_word"},
      "company": {"type": "keyword"},

      // 投保规则原始字段
      "applyRules_insureRules_Age": {"type": "text"},
      "applyRules_insureRules_InsuredPerson": {"type": "keyword"},
      "applyRules_insureRules_Gender": {"type": "keyword"},
      "applyRules_insureRules_Occupation": {"type": "text"},
      "applyRules_insureRules_Region": {"type": "text"},
      "applyRules_insureRules_SocialSecurity": {"type": "text"},
      "applyRules_insureRules_BMI": {"type": "text"},
      "applyRules_insureRules_OtherFactorsID": {"type": "text"},

      // 申请须知字段
      "appNotice_WaitingPeriod": {"type": "text"},
      "appNotice_CoolingOffPeriod": {"type": "text"},
      "appNotice_GracePeriod": {"type": "text"},
      "appNotice_UnderwritingSupport": {"type": "keyword"},
      "appNotice_UnderwritingMethod": {"type": "text"},
      "appNotice_ClaimDuringWaitingPeriod": {"type": "text"},

      // 续保规则字段
      "renewalRules_RenewalProvision": {"type": "keyword"},
      "renewalRules_MaxRenewalAge": {"type": "text"},
      "renewalRules_GuaranteedRenewalLongTermCoverage": {"type": "text"},
      "renewalRules_DiscontinuationRenewal": {"type": "text"},
      "renewalRules_RenewalRate": {"type": "text"},
      "renewalRules_RenewalUnderwriting": {"type": "text"},

      // 理赔说明字段
      "claimDescriptionList_SumInsuredAndDeductibleSharing": {"type": "text"},
      "claimDescriptionList_ValueAddedService": {"type": "text"},
      "claimDescriptionList_UnderwritingDiscount": {"type": "text"},
      "claimDescriptionList_OtherCircumstances": {"type": "text"},
      "claimDescriptionList_HospitalScope": {"type": "text"},

      // 免责条款字段
      "excuseClause_ViolationOfLaw": {"type": "text"},
      "excuseClause_SpecDiseaseOrTreatment": {"type": "text"},
      "excuseClause_PreExistingCondition": {"type": "text"},
      "excuseClause_ForceMajeure": {"type": "text"},
      "excuseClause_HighRiskActivityOrOccupation": {"type": "text"},
      "excuseClause_NonCompliance": {"type": "text"},
      "excuseClause_IntentionalInjury": {"type": "text"},
      "excuseClause_OtherCircumstances": {"type": "text"},
      "excuseClause_SpecDrugOrDevice": {"type": "text"},

      // 产品条款字段
      "productClauses": {"type": "text"},

      // 核保规则字段
      "uwRuleDataData_isOccupy_UnderwritingHold": {"type": "keyword"},
      "uwRuleDataData_dataAging_SupplementaryMaterialTimeline": {"type": "text"},
      "uwRuleDataData_birthdayTracing_BirthdayPolicyBackdating": {"type": "text"},
      "uwRuleDataData_diseaseSituation_MultipleDiseasesUnderwriting": {"type": "text"},
      "uwRuleDataData_medicalCard_MedicalInsuranceCardLending": {"type": "text"},
      "uwRuleDataData_reconsiderationRule_ReconsiderationRule": {"type": "text"},

      // 在线核保字段
      "onlineMarkingRule_OnlineUnderwritingTraceRule": {"type": "keyword"},
      "onlineConclusionValidity_OnlineUnderwritingTimelineAndValidity": {"type": "text"},
      "onlineManualProcess_OnlineUnderwritingProcess": {"type": "text"},

      // 保障内容动态字段（以 None_ 开头的字段）
      "coverage_details": {"type": "object", "enabled": false},  // 存储所有保障相关的动态字段

      // 元数据
      "file_name": {"type": "keyword"},
      "last_updated": {"type": "date"}
    }
  },
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "analysis": {
      "analyzer": {
        "ik_max_word": {
          "type": "ik_max_word"
        }
      }
    }
  }
}
```

## 3. 字段映射规则

### 3.1 产品ID字段说明

**product_id 字段**:

- 类型：字符串 (keyword)
- 来源：ES 数据中已包含的 product_id 字段
- 用途：作为推荐索引和详细信息索引之间的关联键
- 注意：两个索引中的 product_id 必须保持完全一致

### 3.2 直接映射字段

以下字段可直接从原始JSON数据提取：

| 目标字段 | 原始字段路径 | 数据类型 | 说明 |
|---------|-------------|----------|------|
| `product_id` | ES 数据中的 product_id 字段 | keyword | 产品唯一标识 |
| `product_name` | 从产品数据中提取 | text | 产品名称 |
| `company` | 从产品数据中提取 | keyword | 保险公司名称 |
| `file_name` | 原始文件名（用于追溯） | keyword | 原始文件名 |

### 3.3 需要预处理的字段（仅用于推荐索引）

#### 3.3.1 年龄范围字段 (`age_range`)

**原始字段**: `applyRules_insureRules_Age`
**原始格式示例**:

- `"18-65周岁"`
- `"出生满28天-65周岁"`
- `"0-70周岁"`

**处理逻辑**:

```python
import re

def extract_age_range(age_text):
    if not age_text:
        return {"min_age": 0, "max_age": 100}
    
    # 处理"出生满X天"的情况
    if "出生满" in age_text and "天" in age_text:
        min_age = 0
    else:
        # 提取最小年龄
        min_match = re.search(r'(\d+)(?:周岁|岁)', age_text)
        min_age = int(min_match.group(1)) if min_match else 0
    
    # 提取最大年龄
    max_match = re.search(r'-(\d+)(?:周岁|岁)', age_text)
    max_age = int(max_match.group(1)) if max_match else 100
    
    return {"min_age": min_age, "max_age": max_age}
```

#### 3.3.2 职业字段 (`occupation_types`, `excluded_occupations`)

**原始字段**: `applyRules_insureRules_Occupation`
**原始格式示例**:

- `"1-4类职业"`
- `"除高危职业外"`
- `"1-6类职业（除特殊职业）"`

**处理逻辑**:

```python
def process_occupation(occupation_text):
    occupation_types = []
    excluded_occupations = []
    
    if not occupation_text:
        return occupation_types, excluded_occupations
    
    # 提取包含的职业类型
    if "1-4类" in occupation_text:
        occupation_types.extend(["1类职业", "2类职业", "3类职业", "4类职业"])
    elif "1-6类" in occupation_text:
        occupation_types.extend(["1类职业", "2类职业", "3类职业", "4类职业", "5类职业", "6类职业"])
    
    # 提取排除的职业类型
    if "高危职业" in occupation_text or "除高危" in occupation_text:
        excluded_occupations.append("高危职业")
    if "特殊职业" in occupation_text or "除特殊" in occupation_text:
        excluded_occupations.append("特殊职业")
    
    return occupation_types, excluded_occupations
```

#### 3.3.3 地区字段 (`regions`, `excluded_regions`)

**原始字段**: `applyRules_insureRules_Region`
**原始格式示例**:

- `"中国大陆"`
- `"除西藏、新疆外"`
- `"全国"`

**处理逻辑**:

```python
def process_region(region_text):
    regions = []
    excluded_regions = []
    
    if not region_text:
        return ["不限地区"], []
    
    if "中国大陆" in region_text or "全国" in region_text:
        regions.append("不限地区")
    
    # 提取排除的地区
    if "除" in region_text:
        excluded_match = re.findall(r'除([^外]+)外', region_text)
        for excluded in excluded_match:
            excluded_regions.extend([r.strip() for r in excluded.split('、')])
    
    return regions, excluded_regions
```

#### 3.3.4 保障内容字段 (`coverage.*`)

**原始字段**: 以 `None_` 开头的动态字段，如 `None_GeneralMedPymt_GeneralHosp_planA`

**金额字段处理**:

```python
def parse_amount(amount_text):
    if not amount_text or amount_text == "不限":
        return 99999999  # 表示无限额

    # 提取数字和单位
    match = re.search(r'(\d+(?:\.\d+)?)([万亿]?)', amount_text)
    if not match:
        return 0

    number = float(match.group(1))
    unit = match.group(2)

    if unit == "万":
        return int(number * 10000)
    elif unit == "亿":
        return int(number * 100000000)
    else:
        return int(number)
```

**报销比例处理**:

```python
def parse_reimbursement_rate(rate_text):
    if not rate_text:
        return 0.0, 0.0

    # 处理"有社保X%，无社保Y%"格式
    social_match = re.search(r'有社保(\d+)%', rate_text)
    no_social_match = re.search(r'无社保(\d+)%', rate_text)

    with_social = float(social_match.group(1)) / 100 if social_match else 0.0
    without_social = float(no_social_match.group(1)) / 100 if no_social_match else 0.0

    # 如果只有一个百分比，假设是有社保的比例
    if with_social == 0.0 and without_social == 0.0:
        single_match = re.search(r'(\d+)%', rate_text)
        if single_match:
            with_social = float(single_match.group(1)) / 100

    return with_social, without_social
```

#### 3.3.5 费率表字段 (`premium.*`)

**原始字段**: 从 `productClauses` 中的费率表PDF文件解析
**处理逻辑**: 从复杂的费率表中提取标准年龄段的保费

```python
def extract_premium_by_age(rate_data):
    premium_dict = {}
    standard_ages = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70]

    # 这里需要根据实际的费率表结构进行解析
    # 假设费率表是按年龄-保费的键值对存储
    for age in standard_ages:
        # 查找最接近的年龄对应的保费
        closest_age = find_closest_age_in_rate_table(rate_data, age)
        premium_dict[f"age_{age}"] = rate_data.get(closest_age, 0.0)

    return premium_dict

def find_closest_age_in_rate_table(rate_data, target_age):
    # 实现查找最接近年龄的逻辑
    available_ages = [int(age) for age in rate_data.keys() if age.isdigit()]
    if not available_ages:
        return None

    return min(available_ages, key=lambda x: abs(x - target_age))
```

### 3.4 需要LLM生成的字段（仅用于推荐索引）

#### 3.4.1 增值服务字段 (`value_added_services`)

**数据来源**: 产品描述文本、保障条款等
**LLM Prompt**:

```text
你是一个保险产品分析专家。请从以下产品信息中提取标准化的增值服务类型。

产品信息：
{product_description}

请从以下标准增值服务列表中选择适用的服务类型：
- 就医绿通
- 费用垫付
- 在线问诊
- 重疾绿通
- 智能核保
- 人工核保
- 特药服务
- 海外医疗
- 质子重离子
- 专家会诊

输出格式：JSON数组，例如：["就医绿通", "费用垫付", "在线问诊"]

如果没有明确的增值服务信息，请返回空数组：[]
```

#### 3.4.2 产品标签字段 (`product_tags`)

**数据来源**: 产品名称、描述、特色等
**LLM Prompt**:

```text
你是一个保险产品分类专家。请为以下保险产品生成标准化标签。

产品名称：{product_name}
产品描述：{product_description}
投保规则：{apply_rules}

请从以下标签库中选择3-5个最适合的标签：

基础标签：
- 基础保障
- 全面保障
- 高端保障
- 经济实惠
- 性价比高

特色标签：
- 长期保证续保
- 免赔额低
- 报销比例高
- 保额充足
- 核保宽松
- 慢病版
- 创新产品
- 热销产品
- 经典产品

人群标签：
- 年轻人首选
- 家庭保障
- 女性专属
- 老年友好
- 儿童专属

输出格式：JSON数组，例如：["基础保障", "性价比高", "年轻人首选"]
```

#### 3.4.3 目标人群字段 (`target_groups`)

**数据来源**: 投保规则、产品特色等
**LLM Prompt**:

```text
你是一个保险产品用户画像专家。请根据以下产品信息分析目标用户群体。

产品信息：
- 产品名称：{product_name}
- 年龄限制：{age_limit}
- 职业限制：{occupation_limit}
- 保障特色：{coverage_features}
- 保费水平：{premium_level}

请从以下用户群体中选择2-4个最匹配的目标群体：

年龄群体：
- 年轻群体(18-30岁)
- 中年群体(30-45岁)
- 中老年群体(45-60岁)
- 老年群体(60岁以上)

职业群体：
- 企业员工
- 自由职业者
- 学生群体
- 退休人员

收入群体：
- 经济型用户
- 中等收入用户
- 高收入用户

家庭状况：
- 单身群体
- 新婚夫妇
- 有子女家庭
- 空巢家庭

输出格式：JSON数组，例如：["年轻群体(18-30岁)", "企业员工", "经济型用户"]
```

### 3.5 评分字段生成（仅用于推荐索引）

评分字段需要基于产品的各项指标计算得出：

#### 3.5.1 性价比评分 (`cost_performance_score`)

```python
def calculate_cost_performance_score(product_data):
    # 基于保额/保费比率、免赔额、报销比例等计算
    coverage_amount = product_data.get('coverage', {}).get('general_medical', {}).get('amount', 0)
    premium = product_data.get('premium', {}).get('age_30', 0)  # 使用30岁保费作为基准
    deductible = product_data.get('coverage', {}).get('general_medical', {}).get('deductible', 0)

    if premium == 0:
        return 0.0

    # 保额保费比
    amount_premium_ratio = coverage_amount / premium if premium > 0 else 0

    # 免赔额惩罚（免赔额越高，评分越低）
    deductible_penalty = max(0, 1 - deductible / 20000)  # 2万免赔额为基准

    # 综合评分（0-5分）
    score = min(5.0, (amount_premium_ratio / 1000) * deductible_penalty)
    return round(score, 2)
```

#### 3.5.2 保障完整性评分 (`coverage_completeness_score`)

```python
def calculate_coverage_completeness_score(product_data):
    coverage = product_data.get('coverage', {})

    # 检查各项保障是否存在
    coverage_items = [
        'general_medical',
        'critical_illness',
        'special_disease',
        'external_drug',
        'proton_heavy_ion',
        'vip_medical'
    ]

    available_count = sum(1 for item in coverage_items if coverage.get(item, {}).get('amount', 0) > 0)
    completeness_ratio = available_count / len(coverage_items)

    return round(completeness_ratio * 5.0, 2)  # 0-5分
```

#### 3.5.3 续保稳定性评分 (`renewal_stability_score`)

```python
def calculate_renewal_stability_score(product_data):
    renewal = product_data.get('renewal', {})

    guaranteed_years = renewal.get('guaranteed_renewal_years', 0)
    max_renewal_age = renewal.get('max_renewal_age', 0)
    no_underwriting = not renewal.get('renewal_underwriting_required', True)
    rate_stable = not renewal.get('rate_adjustable', True)

    # 保证续保年限评分（20年满分）
    years_score = min(2.0, guaranteed_years / 10)

    # 最大续保年龄评分
    age_score = min(1.0, max_renewal_age / 80) if max_renewal_age > 0 else 0

    # 续保条件评分
    condition_score = (1.0 if no_underwriting else 0) + (1.0 if rate_stable else 0)

    total_score = years_score + age_score + condition_score
    return round(min(5.0, total_score), 2)
```

### 3.6 续保相关字段生成 (`renewal`)

续保相关字段是产品推荐系统中的关键偏好匹配因子，由于续保条款的表述方式复杂多样，需要使用 LLM 来准确解析和提取结构化信息。

#### 3.6.1 原始字段说明

基于 `data/products/table_main_translated/` 中的产品数据，续保相关的原始字段包括：

- `renewalRules_RenewalProvision`: 续保条款（"有"/"无"）
- `renewalRules_MaxRenewalAge`: 最大续保年龄（如"至105岁"、"至100岁"、"无"）
- `renewalRules_GuaranteedRenewalLongTermCoverage`: 保证续保期（如"20年"、"无"）
- `renewalRules_DiscontinuationRenewal`: 停售续保规则
- `renewalRules_RenewalRate`: 续保费率调整规则
- `renewalRules_RenewalUnderwriting`: 续保核保要求

#### 3.6.2 LLM 提取方法

使用 LLM 解析续保条款的优势：

- 能够理解复杂的自然语言表述
- 处理多种表达方式和特殊情况
- 提取隐含的业务逻辑关系
- 保证解析结果的一致性和准确性

```python
def extract_renewal_fields_with_llm(product_data):
    """使用 LLM 从原始数据中提取续保相关字段"""

    # 收集所有续保相关的原始文本
    renewal_texts = {
        'renewal_provision': product_data.get('renewalRules_RenewalProvision', ''),
        'max_renewal_age': product_data.get('renewalRules_MaxRenewalAge', ''),
        'guaranteed_coverage': product_data.get('renewalRules_GuaranteedRenewalLongTermCoverage', ''),
        'discontinuation_renewal': product_data.get('renewalRules_DiscontinuationRenewal', ''),
        'renewal_rate': product_data.get('renewalRules_RenewalRate', ''),
        'renewal_underwriting': product_data.get('renewalRules_RenewalUnderwriting', '')
    }

    # 构建 LLM 提示词
    prompt = f"""
请分析以下保险产品的续保条款信息，提取结构化的续保相关字段：

续保条款: {renewal_texts['renewal_provision']}
最大续保年龄: {renewal_texts['max_renewal_age']}
保证续保期: {renewal_texts['guaranteed_coverage']}
停售续保规则: {renewal_texts['discontinuation_renewal']}
续保费率规则: {renewal_texts['renewal_rate']}
续保核保要求: {renewal_texts['renewal_underwriting']}

请提取以下字段并以JSON格式返回：
1. guaranteed_renewal_years: 保证续保年限（整数，如果是"20年"则返回20，如果无保证续保则返回0，如果是"终身"则返回999）
2. max_renewal_age: 最大续保年龄（整数，如果是"至105岁"则返回105，如果无限制则返回0，如果是"终身"则返回999）
3. renewal_underwriting_required: 是否需要续保核保（布尔值，优先考虑保证续保期内的规则）
4. rate_adjustable: 费率是否可调整（布尔值，如果明确说明费率不可调则返回false，否则返回true）

注意事项：
- 对于复杂的分段规则（如"保障期内/保证续保期内"和"保障期外/保证续保期外"），优先考虑保证续保期内的规则
- 如果信息不明确，采用保守估计（对用户不利的假设）
- 确保返回的是有效的JSON格式

返回格式：
{{
    "guaranteed_renewal_years": 数字,
    "max_renewal_age": 数字,
    "renewal_underwriting_required": 布尔值,
    "rate_adjustable": 布尔值
}}
"""

    # 调用 LLM API
    try:
        response = call_llm_api(prompt)
        renewal_data = json.loads(response)

        # 数据验证和清理
        renewal_data = validate_and_clean_renewal_data(renewal_data)

        return renewal_data

    except Exception as e:
        logger.error(f"LLM 提取续保字段失败: {e}")
        # 返回保守的默认值
        return {
            'guaranteed_renewal_years': 0,
            'max_renewal_age': 0,
            'renewal_underwriting_required': True,
            'rate_adjustable': True
        }

def validate_and_clean_renewal_data(renewal_data):
    """验证和清理 LLM 提取的续保数据"""

    # 确保字段存在并设置默认值
    defaults = {
        'guaranteed_renewal_years': 0,
        'max_renewal_age': 0,
        'renewal_underwriting_required': True,
        'rate_adjustable': True
    }

    for key, default_value in defaults.items():
        if key not in renewal_data:
            renewal_data[key] = default_value

    # 数据类型转换和范围检查
    renewal_data['guaranteed_renewal_years'] = max(0, min(999, int(renewal_data['guaranteed_renewal_years'])))
    renewal_data['max_renewal_age'] = max(0, min(999, int(renewal_data['max_renewal_age'])))
    renewal_data['renewal_underwriting_required'] = bool(renewal_data['renewal_underwriting_required'])
    renewal_data['rate_adjustable'] = bool(renewal_data['rate_adjustable'])

    return renewal_data
```

#### 3.6.3 LLM 提示词优化

针对不同复杂度的续保条款，可以使用不同的提示词策略：

```python
def get_renewal_extraction_prompt(renewal_texts, complexity_level='standard'):
    """根据复杂度获取相应的提示词"""

    base_prompt = f"""
分析以下保险产品续保条款：

{format_renewal_texts(renewal_texts)}

提取字段：guaranteed_renewal_years, max_renewal_age, renewal_underwriting_required, rate_adjustable
"""

    if complexity_level == 'simple':
        # 简单产品的提示词
        return base_prompt + """
这是一个标准的保险产品，请直接提取明确的数值和规则。
"""

    elif complexity_level == 'complex':
        # 复杂产品的提示词
        return base_prompt + """
这个产品有复杂的续保规则，可能包含：
- 分段规则（保证续保期内外不同）
- 特殊条件（如产品停售、公司经营状况等）
- 模糊表述（如"原则上"、"一般情况下"等）

请仔细分析并提取最核心的续保条件，优先考虑对用户最有利的解释。
"""

    else:  # standard
        return base_prompt + """
请准确提取续保相关信息，注意区分保证续保期内外的不同规则。
"""

def format_renewal_texts(renewal_texts):
    """格式化续保文本用于 LLM 输入"""
    formatted = []
    for key, value in renewal_texts.items():
        if value and value.strip():
            formatted.append(f"{key}: {value}")
    return "\n".join(formatted)
```

#### 3.6.4 批量处理和质量控制

```python
def batch_extract_renewal_fields(products_data, batch_size=10):
    """批量提取续保字段，包含质量控制"""

    results = []
    failed_products = []

    for i in range(0, len(products_data), batch_size):
        batch = products_data[i:i+batch_size]

        for product in batch:
            try:
                # 提取续保字段
                renewal_data = extract_renewal_fields_with_llm(product)

                # 质量检查
                quality_score = assess_renewal_data_quality(renewal_data, product)

                if quality_score >= 0.8:  # 质量阈值
                    results.append({
                        'product_id': product['product_id'],
                        'renewal': renewal_data,
                        'quality_score': quality_score
                    })
                else:
                    # 质量不达标，记录并使用默认值
                    failed_products.append({
                        'product_id': product['product_id'],
                        'reason': 'Low quality score',
                        'quality_score': quality_score
                    })

            except Exception as e:
                failed_products.append({
                    'product_id': product.get('product_id', 'unknown'),
                    'reason': str(e)
                })

    return results, failed_products

def assess_renewal_data_quality(renewal_data, original_product):
    """评估提取的续保数据质量"""
    score = 1.0

    # 检查逻辑一致性
    if (renewal_data['guaranteed_renewal_years'] > 0 and
        renewal_data['renewal_underwriting_required']):
        score -= 0.2  # 保证续保期内通常不需要核保

    # 检查数值合理性
    if renewal_data['guaranteed_renewal_years'] > 50:
        score -= 0.3  # 保证续保年限过长

    if (renewal_data['max_renewal_age'] > 0 and
        renewal_data['max_renewal_age'] < 60):
        score -= 0.3  # 最大续保年龄过低

    # 检查与原始文本的一致性
    original_text = original_product.get('renewalRules_GuaranteedRenewalLongTermCoverage', '')
    if ('20年' in original_text and renewal_data['guaranteed_renewal_years'] != 20):
        score -= 0.4  # 与原始文本不一致

    return max(0.0, score)
```

## 4. 数据处理流程

### 4.1 双索引处理步骤

#### 4.1.1 详细信息索引 (all_products) 处理

1. **读取原始JSON文件**
2. **基础字段提取**：product_id, product_name, company, file_name
3. **原始字段保存**：保存所有原始字段到 all_products 索引
4. **动态字段处理**：将以 `None_` 开头的保障字段存储到 `coverage_details` 对象中
5. **数据验证**：完整性检查
6. **写入 all_products 索引**

#### 4.1.2 推荐索引 (insurance_products) 处理

1. **读取原始JSON文件**
2. **基础字段提取**：直接映射的字段
3. **规则引擎处理**：年龄、职业、地区等结构化字段
4. **LLM增强处理**：增值服务、标签、目标人群、续保条件解析
   - 使用 LLM 解析复杂的续保条款文本
   - 提取结构化的续保相关字段
   - 生成产品特色标签和目标人群
5. **评分计算**：各项评分指标（包括续保稳定性评分）
6. **数据验证**：完整性和合理性检查
7. **写入 insurance_products 索引**

### 4.2 批处理脚本示例

```python
def process_product_file_for_all_products(file_path):
    """处理产品文件并写入 all_products 索引"""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # 确保 product_id 存在
    if 'product_id' not in raw_data:
        raise ValueError(f"产品数据中缺少 product_id 字段: {file_path}")

    # 基础字段
    file_name = os.path.basename(file_path)
    all_products_data = {
        'product_id': raw_data['product_id'],
        'product_name': raw_data.get('product_name', raw_data['product_id']),
        'company': raw_data.get('company', ''),
        'file_name': file_name,
        'last_updated': datetime.now().isoformat()
    }

    # 保存所有原始字段
    all_products_data.update(raw_data)

    # 处理动态保障字段
    coverage_details = {}
    for key, value in raw_data.items():
        if key.startswith('None_'):
            coverage_details[key] = value
    all_products_data['coverage_details'] = coverage_details

    return all_products_data

def process_product_file_for_recommendation(file_path):
    """处理产品文件并写入 insurance_products 索引"""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # 确保 product_id 存在
    if 'product_id' not in raw_data:
        raise ValueError(f"产品数据中缺少 product_id 字段: {file_path}")

    # 基础字段提取
    processed_data = extract_basic_fields(raw_data)

    # 规则引擎处理
    processed_data.update(process_structured_fields(raw_data))

    # LLM增强处理（包括续保字段提取）
    llm_enhanced_data = llm_enhance_fields(raw_data)
    processed_data.update(llm_enhanced_data)

    # 从LLM增强结果中提取续保字段
    processed_data['renewal'] = llm_enhanced_data.get('renewal', {})

    # 评分计算（包括续保稳定性评分）
    processed_data.update(calculate_scores(processed_data))

    # 数据验证
    validate_data(processed_data)

    return processed_data

def batch_process_products(products_dir):
    """批量处理产品文件，同时写入两个索引"""
    for file_name in os.listdir(products_dir):
        if file_name.endswith('_main.json'):
            file_path = os.path.join(products_dir, file_name)
            try:
                # 处理并写入 all_products 索引
                all_products_data = process_product_file_for_all_products(file_path)
                index_to_elasticsearch(all_products_data, 'all_products')

                # 处理并写入 insurance_products 索引
                recommendation_data = process_product_file_for_recommendation(file_path)
                index_to_elasticsearch(recommendation_data, 'insurance_products')

                print(f"Successfully processed: {file_name}")
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
```

## 5. 查询使用方式

### 5.1 推荐查询流程

1. **第一步**：在 `insurance_products` 索引中执行四层匹配查询
2. **第二步**：获取匹配产品的 `product_id` 列表
3. **第三步**：使用 `product_id` 列表在 `all_products` 索引中批量查询详细信息
4. **第四步**：结合用户特征和产品详细信息，通过 LLM 生成最终的 `ProductInfo`

### 5.2 查询示例

```python
# 第一步：推荐查询
recommendation_query = {
    "size": 10,
    "_source": ["product_id", "overall_rating", "cost_performance_score"],
    "query": {
        # 四层匹配查询...
    }
}

# 第二步：获取 product_id 列表
recommendation_results = es_client.search(index="insurance_products", body=recommendation_query)
product_ids = [hit["_source"]["product_id"] for hit in recommendation_results["hits"]["hits"]]

# 第三步：批量查询详细信息
detail_query = {
    "query": {
        "terms": {
            "product_id": product_ids
        }
    }
}
detail_results = es_client.search(index="all_products", body=detail_query)

# 第四步：通过 LLM 生成 ProductInfo
for detail in detail_results["hits"]["hits"]:
    product_detail = detail["_source"]
    product_info = generate_product_info_with_llm(product_detail, user_characteristics)
```

### 5.3 续保字段处理完整示例

```python
def complete_renewal_processing_example():
    """基于 LLM 的续保字段处理完整示例"""

    # 示例原始数据（来自实际产品文件）
    raw_product_data = {
        "product_id": "好医保长期医疗险（20年版）",
        "renewalRules_RenewalProvision": "有",
        "renewalRules_MaxRenewalAge": "至100岁",
        "renewalRules_GuaranteedRenewalLongTermCoverage": "20年",
        "renewalRules_DiscontinuationRenewal": "保证续保期内可续保(保障期内/保证续保期内)\n可转续其他产品(保障期外/保证续保期外)",
        "renewalRules_RenewalRate": "可调整(保障期内/保证续保期内)\n可调整(保障期外/保证续保期外)",
        "renewalRules_RenewalUnderwriting": "无需审核(保障期内/保证续保期内)\n需审核(保障期外/保证续保期外)"
    }

    # 第一步：使用 LLM 提取续保字段
    renewal_fields = extract_renewal_fields_with_llm(raw_product_data)
    print("LLM 提取的续保字段:", renewal_fields)
    # 预期输出: {
    #   'guaranteed_renewal_years': 20,
    #   'max_renewal_age': 100,
    #   'renewal_underwriting_required': False,  # LLM 理解保证续保期内无需核保
    #   'rate_adjustable': True
    # }

    # 第二步：质量评估
    quality_score = assess_renewal_data_quality(renewal_fields, raw_product_data)
    print("数据质量评分:", quality_score)
    # 预期输出: 1.0 (高质量)

    # 第三步：计算续保稳定性评分
    renewal_score = calculate_renewal_stability_score({'renewal': renewal_fields})
    print("续保稳定性评分:", renewal_score)
    # 预期输出: 4.25 (20年保证续保 + 100岁续保年龄 + 无需核保 + 费率可调)

    # 第四步：构建推荐索引数据
    recommendation_data = {
        "product_id": raw_product_data["product_id"],
        "renewal": renewal_fields,
        "renewal_stability_score": renewal_score,
        "data_quality_score": quality_score,
        # ... 其他字段
    }

    return recommendation_data

# LLM 处理复杂续保条款的示例
def llm_complex_renewal_example():
    """LLM 处理复杂续保条款的示例"""

    # 复杂的续保条款示例
    complex_product = {
        "product_id": "复杂续保条款产品",
        "renewalRules_GuaranteedRenewalLongTermCoverage": "在保险公司持续经营且产品未停售的情况下，保证续保至被保险人99周岁",
        "renewalRules_RenewalUnderwriting": "保证续保期内，无需重新核保，但保险公司有权根据整体赔付情况调整费率",
        "renewalRules_RenewalRate": "费率调整需经监管部门批准，且单次调整幅度不超过30%",
        "renewalRules_DiscontinuationRenewal": "如产品停售，可转投保险公司其他同类产品"
    }

    # LLM 能够理解复杂的自然语言表述
    renewal_fields = extract_renewal_fields_with_llm(complex_product)
    print("复杂条款提取结果:", renewal_fields)
    # LLM 预期能够理解：
    # - "保证续保至99周岁" 意味着长期保证续保
    # - "无需重新核保" 意味着续保核保要求为 False
    # - "有权调整费率" 意味着费率可调整为 True

    return renewal_fields

# 批量处理示例
def batch_processing_example():
    """批量处理续保字段的示例"""

    products_data = [
        {"product_id": "产品A", "renewalRules_GuaranteedRenewalLongTermCoverage": "20年"},
        {"product_id": "产品B", "renewalRules_GuaranteedRenewalLongTermCoverage": "无"},
        {"product_id": "产品C", "renewalRules_GuaranteedRenewalLongTermCoverage": "终身保证续保"},
    ]

    # 批量处理
    results, failed_products = batch_extract_renewal_fields(products_data)

    print(f"成功处理: {len(results)} 个产品")
    print(f"处理失败: {len(failed_products)} 个产品")

    for result in results:
        print(f"产品 {result['product_id']}: 质量评分 {result['quality_score']}")

    return results, failed_products
```

## 6. 注意事项

1. **数据一致性**：确保两个索引中的 `product_id` 完全一致
2. **缺失值处理**：对于缺失的字段使用合理的默认值
3. **性能优化**：批量处理时注意内存使用和ES写入频率
4. **错误处理**：记录处理失败的文件和原因，便于后续修复
5. **版本控制**：保留原始数据和处理版本的对应关系
6. **索引同步**：确保两个索引的数据保持同步更新

### 6.1 续保字段处理特殊注意事项

1. **LLM 调用成本控制**：
   - 续保字段提取需要调用 LLM，注意控制 API 调用成本
   - 可以考虑批量处理以提高效率
   - 对于简单明确的续保条款，可以先尝试规则匹配，失败后再使用 LLM

2. **LLM 输出质量保证**：
   - 设计详细的提示词，确保 LLM 理解业务逻辑
   - 实施多层验证机制，包括格式验证、数值范围检查、逻辑一致性检查
   - 建立人工审核机制，对质量评分低的结果进行人工复核

3. **保证续保期内外规则区分**：
   - 在提示词中明确要求 LLM 优先考虑保证续保期内的规则
   - 对于复杂的分段规则，提供具体的解析指导
   - 在推荐算法中主要使用保证续保期内的规则

4. **特殊值处理**：
   - 使用 999 表示"终身"或"无限制"
   - 使用 0 表示"无"或"不适用"
   - 在提示词中明确这些特殊值的使用规则

5. **数据质量监控**：
   - 建立 LLM 提取结果的质量评估体系
   - 监控提取失败率和质量评分分布
   - 定期更新提示词以提高提取准确性

6. **业务逻辑一致性**：
   - 保证续保期内通常不需要核保，LLM 应该能理解这一业务逻辑
   - 费率调整规则与保证续保期的关系需要在提示词中说明
   - 续保稳定性评分应该与实际业务价值相符

7. **容错和降级机制**：
   - 当 LLM 调用失败时，提供合理的默认值
   - 建立规则引擎作为 LLM 的备用方案
   - 记录所有处理异常，便于后续优化
