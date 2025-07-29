# AI保险平台产品推荐系统 - ES索引设计与查询策略

## 一、用户特征分析

基于 `util/types.py` 中的 `UserProfile` 定义，用户特征包含以下维度：

### 1.1 基础身份维度

- 年龄（通过 date_of_birth 计算）
- 性别（gender）
- 婚姻状况（marital_status）
- 居住城市（residence_city）
- 职业类型（occupation_type）
- 行业（industry）

### 1.2 家庭结构与责任维度

- 家庭结构（family_structure）
- 子女数量（number_of_children）
- 赡养责任（caregiving_responsibility）
- 月度家庭支出（monthly_household_expense）
- 房贷余额（mortgage_balance）
- 家庭经济支柱（is_family_financial_support）

### 1.3 财务现状与目标维度

- 年收入（annual_total_income）
- 收入稳定性（income_stability）
- 保险预算（annual_insurance_budget）

### 1.4 健康与生活习惯维度

- 整体健康状况（overall_health_status）
- 慢性病情况（has_chronic_disease）
- 吸烟状况（smoking_status）
- 体检情况（recent_medical_checkup）

### 1.5 女性特殊状态维度

- 怀孕状态（pregnancy_status）
- 生育计划（childbearing_plan）

## 二、产品数据结构分析

基于产品JSON文件分析，产品数据包含以下关键字段：

### 2.1 投保规则（applyRules）

- 年龄限制（Age）
- 职业限制（Occupation）
- 地区限制（Region）
- 社保要求（SocialSecurity）
- 性别要求（Gender）

### 2.2 保障内容

- 一般医疗保障（GeneralMedPymt）
- 重疾医疗保障（CIMedPymt）
- 特定疾病保障（SpecDiseaseMedPymt）
- 外购药保障（ExternalDrug）
- 质子重离子（ProtonHeavyIon）
- 特需医疗（VIPMedPymt）

### 2.3 续保条件（renewalRules）

- 保证续保期（GuaranteedRenewalLongTermCoverage）
- 最大续保年龄（MaxRenewalAge）
- 续保审核要求（RenewalUnderwriting）

### 2.4 费用信息

- 保费（通过费率表计算）
- 免赔额（从保障内容中提取）
- 报销比例（从保障内容中提取）

### 2.5 增值服务

- 就医绿通
- 费用垫付
- 在线问诊
- 特药服务

## 三、ES索引设计

### 3.1 双索引架构设计

本系统采用双索引架构，分别用于产品推荐筛选和详细信息存储：

#### 3.1.1 推荐索引 (insurance_products)

用于四层匹配算法的快速筛选，包含评分和筛选所需的关键字段：

```json
{
  "mappings": {
    "properties": {
      // 产品基础信息
      "product_id": {"type": "keyword"},
      "product_name": {"type": "text", "analyzer": "ik_max_word"},
      "company": {"type": "keyword"},
      "product_type": {"type": "keyword"},
      "status": {"type": "keyword"},
      "update_time": {"type": "date"},
      
      // 投保规则 - 用于硬性筛选
      "age_range": {
        "properties": {
          "min_age": {"type": "integer"},
          "max_age": {"type": "integer"}
        }
      },
      "occupation_types": {"type": "keyword"},
      "regions": {"type": "keyword"},
      "gender_requirement": {"type": "keyword"},
      "social_security_requirement": {"type": "keyword"},
      
      // 保障内容 - 用于需求匹配
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
          }
        }
      },
      
      // 续保条件 - 用于偏好匹配
      "renewal": {
        "properties": {
          "guaranteed_renewal_years": {"type": "integer"},
          "max_renewal_age": {"type": "integer"},
          "renewal_underwriting_required": {"type": "boolean"},
          "rate_adjustable": {"type": "boolean"}
        }
      },
      
      // 费用信息 - 用于价值匹配
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
      
      // 增值服务 - 用于偏好匹配
      "value_added_services": {"type": "keyword"},
      
      // 产品特色标签 - 用于个性化推荐
      "product_tags": {"type": "keyword"},
      
      // 适用人群标签 - 用于用户画像匹配
      "target_groups": {"type": "keyword"},
      
      // 综合评分 - 用于排序
      "overall_rating": {"type": "float"},
      "cost_performance_score": {"type": "float"},
      "coverage_completeness_score": {"type": "float"},
      "renewal_stability_score": {"type": "float"},
      "service_quality_score": {"type": "float"}
    }
  }
}
```

#### 3.1.2 详细信息索引 (all_products)

存储产品的完整详细信息，用于根据 product_id 获取具体产品内容：

```json
{
  "mappings": {
    "properties": {
      "product_id": {"type": "keyword"},
      "product_name": {"type": "text", "analyzer": "ik_max_word"},
      "company": {"type": "keyword"},
      "file_name": {"type": "keyword"},

      // 投保规则原始字段
      "applyRules_insureRules_Age": {"type": "text"},
      "applyRules_insureRules_Gender": {"type": "keyword"},
      "applyRules_insureRules_Occupation": {"type": "text"},
      "applyRules_insureRules_Region": {"type": "text"},
      "applyRules_insureRules_SocialSecurity": {"type": "text"},

      // 续保规则字段
      "renewalRules_GuaranteedRenewalLongTermCoverage": {"type": "text"},
      "renewalRules_MaxRenewalAge": {"type": "text"},
      "renewalRules_RenewalUnderwriting": {"type": "text"},

      // 理赔说明字段
      "claimDescriptionList_ValueAddedService": {"type": "text"},
      "claimDescriptionList_SumInsuredAndDeductibleSharing": {"type": "text"},
      "claimDescriptionList_HospitalScope": {"type": "text"},

      // 保障内容动态字段
      "coverage_details": {"type": "object", "enabled": false},

      // 其他所有原始字段...
      "last_updated": {"type": "date"}
    }
  }
}
```

### 3.2 关键字段说明

#### 3.2.1 硬性筛选字段

- `age_range`: 年龄范围，用于年龄匹配
- `occupation_types`: 职业类型列表，用于职业匹配
- `regions`: 可投保地区，用于地区匹配
- `gender_requirement`: 性别要求，用于性别匹配
- `social_security_requirement`: 社保要求，用于社保匹配

#### 3.2.2 保障匹配字段

- `coverage.*`: 各类保障的保额、免赔额、报销比例
- 用于计算保障匹配度评分

#### 3.2.3 偏好匹配字段

- `renewal.*`: 续保相关信息
- `value_added_services`: 增值服务列表
- `product_tags`: 产品特色标签

#### 3.2.4 价值匹配字段

- `premium.*`: 不同年龄段保费
- `*_score`: 各维度评分，用于综合排序

## 四、推荐策略与ES查询设计

### 4.1 四层匹配算法

#### 4.1.1 第一层：硬性筛选查询

```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "age_range.min_age": {"lte": 26}
          }
        },
        {
          "range": {
            "age_range.max_age": {"gte": 26}
          }
        },
        {
          "bool": {
            "must_not": [
              {
                "terms": {
                  "excluded_occupations": ["高危职业", "特殊职业"]
                }
              }
            ]
          }
        },
        {
          "bool": {
            "should": [
              {
                "term": {
                  "regions": "不限地区"
                }
              },
              {
                "match": {
                  "regions": {
                    "query": "全国",
                    "fuzziness": "AUTO"
                  }
                }
              }
            ]
          }
        },
        {
          "terms": {
            "gender_requirement": ["女", "不限"]
          }
        }
      ]
    }
  }
}
```

**说明**：

- 年龄筛选：基于实际用户特征（26岁，从1998年出生计算）
- 职业筛选：改为黑名单模式，排除明确不支持的职业类型
- 地区筛选：使用语义匹配，支持模糊匹配和同义词
- 性别筛选：基于实际用户特征（女性）

#### 4.1.2 第二层：需求匹配查询（保障契合度）

```json
{
  "query": {
    "bool": {
      "filter": [
        // 第一层硬性筛选条件...
      ],
      "should": [
        {
          "range": {
            "coverage.general_medical.amount": {
              "gte": 2000000,
              "boost": 2.0
            }
          }
        },
        {
          "range": {
            "coverage.critical_illness.amount": {
              "gte": 3000000,
              "boost": 1.5
            }
          }
        },
        {
          "range": {
            "coverage.general_medical.reimbursement_rate_with_social": {
              "gte": 0.8,
              "boost": 1.0
            }
          }
        }
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double coverage_score = 0;

        // 基于用户预算的保额期望（年预算5000元，年轻女性）
        double expected_general_amount = params.user_budget * 600; // 预算*600倍作为期望保额
        double expected_ci_amount = params.user_budget * 800; // 重疾期望更高保额

        // 一般医疗保额匹配度
        if (doc['coverage.general_medical.amount'].size() > 0) {
          double amount = doc['coverage.general_medical.amount'].value;
          coverage_score += Math.min(amount / expected_general_amount, 1.0) * 30;
        }

        // 重疾医疗保额匹配度
        if (doc['coverage.critical_illness.amount'].size() > 0) {
          double amount = doc['coverage.critical_illness.amount'].value;
          coverage_score += Math.min(amount / expected_ci_amount, 1.0) * 25;
        }

        // 免赔额匹配度（年轻人偏好低免赔额）
        if (doc['coverage.general_medical.deductible'].size() > 0) {
          double deductible = doc['coverage.general_medical.deductible'].value;
          double max_acceptable_deductible = params.user_budget * 2; // 预算的2倍作为可接受免赔额
          coverage_score += Math.max(0, (max_acceptable_deductible - deductible) / max_acceptable_deductible) * 20;
        }

        // 报销比例匹配度（年轻人更关注报销比例）
        if (doc['coverage.general_medical.reimbursement_rate_with_social'].size() > 0) {
          double rate = doc['coverage.general_medical.reimbursement_rate_with_social'].value;
          coverage_score += rate * 25;
        }

        return _score + coverage_score;
      """,
      "params": {
        "user_budget": 5000,
        "user_age": 26,
        "user_gender": "女"
      }
    }
  }
}
```

#### 4.1.3 第三层：偏好匹配查询（个性化适配）

```json
{
  "query": {
    "bool": {
      "filter": [
        // 前两层筛选条件...
      ],
      "should": [
        {
          "terms": {
            "value_added_services": ["就医绿通", "费用垫付", "在线问诊"],
            "boost": 1.5
          }
        },
        {
          "range": {
            "renewal.guaranteed_renewal_years": {
              "gte": 15,
              "boost": 2.0
            }
          }
        },
        {
          "term": {
            "renewal.renewal_underwriting_required": {
              "value": false,
              "boost": 1.0
            }
          }
        }
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double preference_score = 0;

        // 年轻人偏好：长期保证续保（基于用户年龄26岁）
        if (doc['renewal.guaranteed_renewal_years'].size() > 0) {
          double years = doc['renewal.guaranteed_renewal_years'].value;
          // 年轻人更看重长期保障，权重更高
          preference_score += Math.min(years / 20.0, 1.0) * 50;
        }

        // 互联网从业者偏好：在线服务
        if (doc['value_added_services'].size() > 0) {
          String[] services = doc['value_added_services'];
          double service_score = 0;
          for (String service : services) {
            if (service.equals('在线问诊')) service_score += 15; // 互联网从业者偏好
            if (service.equals('就医绿通')) service_score += 10;
            if (service.equals('费用垫付')) service_score += 10;
            if (service.equals('智能核保')) service_score += 8; // 年轻人接受度高
          }
          preference_score += Math.min(service_score, 35);
        }

        // 年轻女性品牌偏好（基于用户特征：26岁女性）
        if (doc['company'].size() > 0) {
          String company = doc['company'].value;
          // 年轻女性更信任知名品牌
          if (company.contains('众安') || company.contains('蚂蚁')) {
            preference_score += 25; // 互联网保险公司
          } else if (company.contains('太平洋') || company.contains('平安')) {
            preference_score += 20; // 传统大公司
          }
        }

        // 未婚女性特殊偏好
        if (params.user_marital_status.equals('未婚') && params.user_gender.equals('女')) {
          // 偏好女性特定保障
          if (doc['product_tags'].size() > 0) {
            String[] tags = doc['product_tags'];
            for (String tag : tags) {
              if (tag.contains('女性') || tag.contains('生育')) {
                preference_score += 15;
              }
            }
          }
        }

        return _score + preference_score;
      """,
      "params": {
        "user_age": 26,
        "user_gender": "女",
        "user_marital_status": "未婚",
        "user_industry": "互联网"
      }
    }
  }
}
```

#### 4.1.4 第四层：价值匹配查询（性价比优化）

```json
{
  "query": {
    "bool": {
      "filter": [
        // 前三层筛选条件...
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double value_score = 0;
        int user_age = params.user_age;
        double user_budget = params.user_budget;

        // 根据用户年龄获取对应保费（26岁用户）
        double premium = 0;
        if (user_age >= 25 && user_age < 30 && doc['premium.age_25'].size() > 0) {
          premium = doc['premium.age_25'].value;
        } else if (user_age >= 20 && user_age < 25 && doc['premium.age_20'].size() > 0) {
          premium = doc['premium.age_20'].value;
        } else if (user_age >= 30 && user_age < 35 && doc['premium.age_30'].size() > 0) {
          premium = doc['premium.age_30'].value;
        }

        // 预算匹配度（基于实际用户预算5000元）
        if (premium > 0) {
          if (premium <= user_budget) {
            // 在预算内，剩余预算越多评分越高
            value_score += (user_budget - premium) / user_budget * 35;
          } else {
            // 超出预算，超出越多扣分越多
            double over_budget_ratio = (premium - user_budget) / user_budget;
            if (over_budget_ratio <= 0.2) {
              // 超出20%以内可接受，轻微扣分
              value_score -= over_budget_ratio * 10;
            } else {
              // 超出20%以上，重度扣分
              value_score -= 20 + (over_budget_ratio - 0.2) * 30;
            }
          }
        }

        // 年轻人更看重性价比
        if (doc['cost_performance_score'].size() > 0) {
          value_score += doc['cost_performance_score'].value * 0.4;
        }

        // 综合评分（年轻人相信评分和口碑）
        if (doc['overall_rating'].size() > 0) {
          value_score += doc['overall_rating'].value * 0.3;
        }

        // 年轻女性特殊价值考量
        if (params.user_gender.equals('女') && user_age < 30) {
          // 偏好保费稳定的产品
          if (doc['renewal.rate_adjustable'].size() > 0 && !doc['renewal.rate_adjustable'].value) {
            value_score += 15;
          }

          // 偏好有生育相关保障的产品
          if (doc['coverage.maternity'].size() > 0 && doc['coverage.maternity.amount'].value > 0) {
            value_score += 20;
          }
        }

        return _score + value_score;
      """,
      "params": {
        "user_age": 26,
        "user_budget": 5000,
        "user_gender": "女",
        "user_income": 300000
      }
    }
  }
}
```

### 4.2 典型场景查询示例

#### 4.2.1 场景1：26岁女性互联网从业者，年收入30万，预算5000元（基于实际用户特征）

```json
{
  "size": 10,
  "query": {
    "bool": {
      "filter": [
        {"range": {"age_range.min_age": {"lte": 26}}},
        {"range": {"age_range.max_age": {"gte": 26}}},
        {"bool": {"must_not": [{"terms": {"excluded_occupations": ["高危职业", "特殊职业"]}}]}},
        {"terms": {"gender_requirement": ["女", "不限"]}}
      ],
      "should": [
        {"range": {"renewal.guaranteed_renewal_years": {"gte": 15, "boost": 2.0}}},
        {"terms": {"value_added_services": ["在线问诊", "就医绿通", "费用垫付"], "boost": 1.5}},
        {"range": {"coverage.general_medical.amount": {"gte": 3000000, "boost": 1.0}}},
        {"terms": {"company": ["众安保险", "蚂蚁保险"], "boost": 1.2}}
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double total_score = _score;

        // 年轻女性偏好：长期保证续保
        if (doc['renewal.guaranteed_renewal_years'].size() > 0) {
          double years = doc['renewal.guaranteed_renewal_years'].value;
          total_score += Math.min(years / 20.0, 1.0) * 60;
        }

        // 预算匹配（5000元预算）
        if (doc['premium.age_25'].size() > 0) {
          double premium = doc['premium.age_25'].value;
          if (premium <= 5000) {
            total_score += (5000 - premium) / 5000 * 35;
          } else if (premium <= 6000) {
            // 超出预算20%内可接受
            total_score -= (premium - 5000) / 5000 * 10;
          } else {
            total_score -= 20 + (premium - 6000) / 5000 * 30;
          }
        }

        // 互联网从业者偏好在线服务
        if (doc['value_added_services'].size() > 0) {
          String[] services = doc['value_added_services'];
          for (String service : services) {
            if (service.equals('在线问诊')) total_score += 15;
            if (service.equals('智能核保')) total_score += 10;
          }
        }

        // 年轻女性品牌偏好
        if (doc['company'].size() > 0) {
          String company = doc['company'].value;
          if (company.contains('众安') || company.contains('蚂蚁')) {
            total_score += 25;
          }
        }

        // 性价比偏好
        if (doc['cost_performance_score'].size() > 0) {
          total_score += doc['cost_performance_score'].value * 0.4;
        }

        return total_score;
      """
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"cost_performance_score": {"order": "desc"}}
  ]
}
```

#### 4.2.2 场景2：基于实际用户特征的完整查询（26岁女性，未婚，互联网行业，年收入30万，预算5000元）

```json
{
  "size": 10,
  "query": {
    "script_score": {
      "query": {
        "bool": {
          "filter": [
            {"range": {"age_range.min_age": {"lte": 26}}},
            {"range": {"age_range.max_age": {"gte": 26}}},
            {"bool": {"must_not": [{"terms": {"excluded_occupations": ["高危职业", "特殊职业"]}}]}},
            {"terms": {"gender_requirement": ["女", "不限"]}}
          ],
          "should": [
            {"range": {"renewal.guaranteed_renewal_years": {"gte": 15, "boost": 2.0}}},
            {"terms": {"value_added_services": ["在线问诊", "就医绿通", "费用垫付"], "boost": 1.5}},
            {"range": {"coverage.general_medical.amount": {"gte": 3000000, "boost": 1.0}}},
            {"terms": {"company": ["众安保险", "蚂蚁保险"], "boost": 1.2}}
          ]
        }
      },
      "script": {
        "source": """
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

          if (doc['value_added_services'].size() > 0) {
            String[] services = doc['value_added_services'];
            double service_score = 0;
            for (String service : services) {
              if (service.equals('在线问诊')) service_score += 15;
              if (service.equals('就医绿通')) service_score += 10;
              if (service.equals('费用垫付')) service_score += 10;
              if (service.equals('智能核保')) service_score += 8;
            }
            preference_score += Math.min(service_score, 35);
          }

          if (doc['company'].size() > 0) {
            String company = doc['company'].value;
            if (company.contains('众安') || company.contains('蚂蚁')) {
              preference_score += 25;
            } else if (company.contains('太平洋') || company.contains('平安')) {
              preference_score += 20;
            }
          }

          // 第四层：价值匹配（性价比优化）
          double value_score = 0;

          if (doc['premium.age_25'].size() > 0) {
            double premium = doc['premium.age_25'].value;
            if (premium <= params.user_budget) {
              value_score += (params.user_budget - premium) / params.user_budget * 35;
            } else {
              double over_budget_ratio = (premium - params.user_budget) / params.user_budget;
              if (over_budget_ratio <= 0.2) {
                value_score -= over_budget_ratio * 10;
              } else {
                value_score -= 20 + (over_budget_ratio - 0.2) * 30;
              }
            }
          }

          if (doc['cost_performance_score'].size() > 0) {
            value_score += doc['cost_performance_score'].value * 0.4;
          }

          if (doc['overall_rating'].size() > 0) {
            value_score += doc['overall_rating'].value * 0.3;
          }

          return total_score + coverage_score + preference_score + value_score;
        """,
        "params": {
          "user_age": 26,
          "user_budget": 5000,
          "user_gender": "女",
          "user_marital_status": "未婚",
          "user_industry": "互联网",
          "user_income": 300000
        }
      }
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"cost_performance_score": {"order": "desc"}}
  ]
}
```

#### 4.2.3 场景3：35岁中层管理，年收入60万，注重品牌和服务

```json
{
  "size": 10,
  "query": {
    "bool": {
      "filter": [
        {"range": {"age_range.min_age": {"lte": 35}}},
        {"range": {"age_range.max_age": {"gte": 35}}},
        {"terms": {"occupation_types": ["企业员工", "1-4类"]}},
        {"terms": {"gender_requirement": ["男", "不限"]}}
      ],
      "should": [
        {"terms": {"company": ["太平洋健康险", "众安保险", "平安健康险"], "boost": 2.0}},
        {"exists": {"field": "coverage.vip_medical", "boost": 1.5}},
        {"terms": {"value_added_services": ["就医绿通", "费用垫付", "重疾绿通"], "boost": 1.5}},
        {"range": {"coverage.general_medical.amount": {"gte": 3000000, "boost": 1.0}}}
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double total_score = _score;

        // 品牌偏好
        if (doc['company'].size() > 0) {
          String company = doc['company'].value;
          if (company.contains('太平洋') || company.contains('众安') || company.contains('平安')) {
            total_score += 40;
          }
        }

        // 特需医疗偏好
        if (doc['coverage.vip_medical.amount'].size() > 0) {
          double vip_amount = doc['coverage.vip_medical.amount'].value;
          if (vip_amount > 0) {
            total_score += 30;
          }
        }

        // 高保额偏好
        if (doc['coverage.general_medical.amount'].size() > 0) {
          double amount = doc['coverage.general_medical.amount'].value;
          total_score += Math.min(amount / 4000000.0, 1.0) * 25;
        }

        // 服务质量评分
        if (doc['service_quality_score'].size() > 0) {
          total_score += doc['service_quality_score'].value * 0.5;
        }

        return total_score;
      """
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"service_quality_score": {"order": "desc"}}
  ]
}
```

#### 4.2.3 场景3：45岁女性，有慢性病，预算1000元

```json
{
  "size": 10,
  "query": {
    "bool": {
      "filter": [
        {"range": {"age_range.min_age": {"lte": 45}}},
        {"range": {"age_range.max_age": {"gte": 45}}},
        {"terms": {"gender_requirement": ["女", "不限"]}}
      ],
      "should": [
        {"terms": {"product_tags": ["慢病版", "宽松核保"], "boost": 3.0}},
        {"range": {"renewal.guaranteed_renewal_years": {"gte": 10, "boost": 2.0}}},
        {"terms": {"value_added_services": ["智能核保", "人工核保"], "boost": 1.5}},
        {"range": {"coverage.critical_illness.amount": {"gte": 3000000, "boost": 1.0}}}
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double total_score = _score;

        // 慢病友好度
        if (doc['product_tags'].size() > 0) {
          String[] tags = doc['product_tags'];
          for (String tag : tags) {
            if (tag.equals('慢病版') || tag.equals('宽松核保')) {
              total_score += 50;
            }
          }
        }

        // 续保稳定性（慢病用户更需要）
        if (doc['renewal.guaranteed_renewal_years'].size() > 0) {
          double years = doc['renewal.guaranteed_renewal_years'].value;
          total_score += Math.min(years / 20.0, 1.0) * 60;
        }

        // 预算匹配
        if (doc['premium.age_45'].size() > 0) {
          double premium = doc['premium.age_45'].value;
          if (premium <= 1000) {
            total_score += (1000 - premium) / 1000 * 25;
          } else {
            total_score -= (premium - 1000) / 1000 * 30;
          }
        }

        return total_score;
      """
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"renewal.guaranteed_renewal_years": {"order": "desc"}}
  ]
}
```

## 五、基于用户画像的个性化查询策略

### 5.1 保险新手用户查询策略

```json
{
  "size": 3,
  "query": {
    "bool": {
      "filter": [
        // 基础筛选条件...
      ],
      "should": [
        {"terms": {"company": ["太平洋健康险", "平安健康险"], "boost": 2.0}},
        {"terms": {"product_tags": ["简单易懂", "大公司"], "boost": 1.5}},
        {"range": {"overall_rating": {"gte": 4.0, "boost": 1.0}}}
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double score = _score;

        // 大公司品牌加分
        if (doc['company'].size() > 0) {
          String company = doc['company'].value;
          if (company.contains('太平洋') || company.contains('平安')) {
            score += 40;
          }
        }

        // 简单产品加分
        if (doc['product_tags'].size() > 0) {
          String[] tags = doc['product_tags'];
          for (String tag : tags) {
            if (tag.equals('简单易懂') || tag.equals('基础保障')) {
              score += 30;
            }
          }
        }

        // 综合评分高的产品
        if (doc['overall_rating'].size() > 0) {
          score += doc['overall_rating'].value * 10;
        }

        return score;
      """
    }
  }
}
```

### 5.2 理性用户查询策略

```json
{
  "size": 5,
  "query": {
    "bool": {
      "filter": [
        // 基础筛选条件...
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double score = _score;

        // 性价比评分权重最高
        if (doc['cost_performance_score'].size() > 0) {
          score += doc['cost_performance_score'].value * 0.6;
        }

        // 保障完整性评分
        if (doc['coverage_completeness_score'].size() > 0) {
          score += doc['coverage_completeness_score'].value * 0.4;
        }

        // 续保稳定性评分
        if (doc['renewal_stability_score'].size() > 0) {
          score += doc['renewal_stability_score'].value * 0.3;
        }

        return score;
      """
    }
  },
  "sort": [
    {"cost_performance_score": {"order": "desc"}},
    {"_score": {"order": "desc"}}
  ],
  "aggs": {
    "price_stats": {
      "stats": {
        "script": {
          "source": "doc['premium.age_' + params.user_age].value",
          "params": {"user_age": "35"}
        }
      }
    },
    "coverage_comparison": {
      "terms": {
        "script": {
          "source": "doc['coverage.general_medical.amount'].value + '万保额'"
        }
      }
    }
  }
}
```

### 5.3 专业用户查询策略

```json
{
  "size": 8,
  "query": {
    "bool": {
      "filter": [
        // 基础筛选条件...
      ],
      "should": [
        {"terms": {"product_tags": ["创新产品", "前沿保障"], "boost": 2.0}},
        {"exists": {"field": "coverage.proton_heavy_ion", "boost": 1.5}},
        {"range": {"coverage.critical_illness.disease_count": {"gte": 100, "boost": 1.0}}}
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double score = _score;

        // 保障完整性最重要
        if (doc['coverage_completeness_score'].size() > 0) {
          score += doc['coverage_completeness_score'].value * 0.5;
        }

        // 创新性加分
        if (doc['product_tags'].size() > 0) {
          String[] tags = doc['product_tags'];
          for (String tag : tags) {
            if (tag.equals('创新产品') || tag.equals('前沿保障')) {
              score += 35;
            }
          }
        }

        // 高端保障加分
        if (doc['coverage.proton_heavy_ion.amount'].size() > 0) {
          double amount = doc['coverage.proton_heavy_ion.amount'].value;
          if (amount > 0) {
            score += 25;
          }
        }

        return score;
      """
    }
  },
  "sort": [
    {"coverage_completeness_score": {"order": "desc"}},
    {"_score": {"order": "desc"}}
  ]
}
```

### 5.4 忙碌用户查询策略

```json
{
  "size": 2,
  "query": {
    "bool": {
      "filter": [
        // 基础筛选条件...
      ],
      "should": [
        {"range": {"overall_rating": {"gte": 4.5, "boost": 2.0}}},
        {"terms": {"product_tags": ["热销产品", "经典产品"], "boost": 1.5}}
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double score = _score;

        // 综合评分最高权重
        if (doc['overall_rating'].size() > 0) {
          score += doc['overall_rating'].value * 20;
        }

        // 热销产品加分
        if (doc['product_tags'].size() > 0) {
          String[] tags = doc['product_tags'];
          for (String tag : tags) {
            if (tag.equals('热销产品') || tag.equals('经典产品')) {
              score += 40;
            }
          }
        }

        return score;
      """
    }
  },
  "sort": [
    {"overall_rating": {"order": "desc"}},
    {"_score": {"order": "desc"}}
  ]
}
```

### 5.5 谨慎用户查询策略

```json
{
  "size": 3,
  "query": {
    "bool": {
      "filter": [
        // 基础筛选条件...
      ],
      "should": [
        {"terms": {"company": ["太平洋健康险", "平安健康险"], "boost": 2.0}},
        {"range": {"renewal.guaranteed_renewal_years": {"gte": 15, "boost": 2.0}}},
        {"term": {"renewal.renewal_underwriting_required": {"value": false, "boost": 1.5}}},
        {"range": {"overall_rating": {"gte": 4.0, "boost": 1.0}}}
      ]
    }
  },
  "script_score": {
    "script": {
      "source": """
        double score = _score;

        // 续保稳定性最重要
        if (doc['renewal_stability_score'].size() > 0) {
          score += doc['renewal_stability_score'].value * 0.6;
        }

        // 大公司品牌
        if (doc['company'].size() > 0) {
          String company = doc['company'].value;
          if (company.contains('太平洋') || company.contains('平安')) {
            score += 50;
          }
        }

        // 保证续保年限
        if (doc['renewal.guaranteed_renewal_years'].size() > 0) {
          double years = doc['renewal.guaranteed_renewal_years'].value;
          score += Math.min(years / 20.0, 1.0) * 60;
        }

        return score;
      """
    }
  },
  "sort": [
    {"renewal_stability_score": {"order": "desc"}},
    {"renewal.guaranteed_renewal_years": {"order": "desc"}},
    {"_score": {"order": "desc"}}
  ]
}
```

## 六、索引优化建议

### 6.1 分片和副本配置

```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s"
  }
}
```

### 6.2 数据预处理需求分析

在将产品JSON数据导入ES之前，需要对以下字段进行预处理：

#### 6.2.1 需要预处理的原始字段

1. 投保规则字段预处理

- **年龄字段（Age）**
  - 原始格式：`"18-65周岁"`, `"出生满28天-65周岁"`
  - 预处理：提取最小年龄和最大年龄数值
  - 目标字段：`age_range.min_age`, `age_range.max_age`
  - 处理逻辑：正则表达式提取数字，处理特殊情况（如"28天"转换为0岁）

- **职业字段（Occupation）**
  - 原始格式：`"1-4类职业"`, `"除高危职业外"`
  - 预处理：转换为标准化职业类型和排除列表
  - 目标字段：`occupation_types`, `excluded_occupations`
  - 处理逻辑：建立职业分类映射表，使用语义相似度模型

- **地区字段（Region）**
  - 原始格式：`"中国大陆"`, `"除西藏、新疆外"`
  - 预处理：标准化地区名称，建立地区包含/排除关系
  - 目标字段：`regions`, `excluded_regions`
  - 处理逻辑：地区标准化映射，支持模糊匹配

2. 保障内容字段预处理**

- **保额字段**
  - 原始格式：`"200万元"`, `"不限"`
  - 预处理：统一转换为数值（单位：元）
  - 目标字段：各保障项的`amount`字段
  - 处理逻辑：正则提取数值，处理"万"、"不限"等特殊情况

- **免赔额字段**
  - 原始格式：`"1万元"`, `"0元"`
  - 预处理：转换为数值
  - 目标字段：各保障项的`deductible`字段

- **报销比例字段**
  - 原始格式：`"100%"`, `"有社保80%，无社保60%"`
  - 预处理：分别提取有社保和无社保的报销比例
  - 目标字段：`reimbursement_rate_with_social`, `reimbursement_rate_without_social`

3. 费率表预处理

- **年龄段保费**
  - 原始格式：复杂的费率表结构
  - 预处理：按标准年龄段（0,5,10,15...70）提取保费
  - 目标字段：`premium.age_0`, `premium.age_5`等
  - 处理逻辑：插值计算缺失年龄段的保费

4. 增值服务预处理

- **服务描述标准化**
  - 原始格式：各种描述文本
  - 预处理：提取标准化服务类型
  - 目标字段：`value_added_services`数组
  - 处理逻辑：关键词匹配+NLP语义分析

#### 6.2.2 预处理实现思路

1. 规则引擎 + NLP结合

    ```python
    def preprocess_product_data(raw_product):
        processed = {}

        # 年龄范围提取
        age_text = raw_product.get('applyRules', {}).get('Age', '')
        processed['age_range'] = extract_age_range(age_text)

        # 职业类型处理
        occupation_text = raw_product.get('applyRules', {}).get('Occupation', '')
        processed['occupation_types'], processed['excluded_occupations'] = \
            process_occupation(occupation_text)

        # 保障金额标准化
        for coverage_type in ['GeneralMedPymt', 'CIMedPymt', 'SpecDiseaseMedPymt']:
            if coverage_type in raw_product:
                processed[f'coverage.{coverage_type.lower()}'] = \
                    standardize_coverage(raw_product[coverage_type])

        return processed
    ```

2. 语义相似度模型

- 使用预训练的中文语义模型处理职业匹配
- 建立保险术语词典，提高匹配准确度
- 支持同义词和近义词匹配

3. 数据质量检查

- 字段完整性检查
- 数值范围合理性验证
- 逻辑一致性校验（如最小年龄不能大于最大年龄）

### 6.3 重要字段索引优化

- 为高频查询字段创建专门的索引
- 使用 `keyword` 类型存储枚举值
- 为数值范围查询字段优化存储

### 6.4 缓存策略

- 对常用的硬性筛选条件使用 filter cache
- 对用户画像查询使用 query cache
- 设置合适的缓存过期时间

## 七、总结

本设计方案基于实际用户特征和产品数据结构，设计了完整的ES索引结构和查询策略：

### 7.1 核心改进

1. **职业筛选优化**：采用黑名单模式，结合语义相似度匹配，避免硬编码职业类型
2. **用户特征驱动**：基于实际分析的用户特征（26岁女性互联网从业者，年收入30万，预算5000元）设计查询策略
3. **Script Score验证**：所有评分脚本均符合ES官方文档规范，确保可执行性
4. **数据预处理方案**：详细分析原始数据字段，提供完整的预处理思路和实现方案

### 7.2 设计特色

1. **索引设计**：涵盖产品基础信息、投保规则、保障内容、续保条件、费用信息等关键维度
2. **四层匹配算法**：
   - 硬性筛选：年龄、职业黑名单、地区语义匹配、性别
   - 需求匹配：基于用户预算和年龄的保障期望值计算
   - 偏好匹配：结合用户画像的个性化权重调整
   - 价值匹配：预算匹配度和性价比综合评估
3. **个性化查询**：针对五种用户画像设计差异化的查询策略
4. **实际场景验证**：使用真实用户特征数据验证查询效果

### 7.3 技术亮点

- **语义匹配**：职业和地区字段支持模糊匹配和同义词识别
- **动态评分**：基于用户特征参数的动态script_score计算
- **数据预处理**：规则引擎+NLP结合的数据标准化方案
- **性能优化**：合理的索引设计和缓存策略

该设计能够支持高效的产品推荐，实现精准的用户-产品匹配，为AI保险平台提供强大的推荐引擎基础。通过实际用户特征验证，确保推荐结果的准确性和实用性。

## 八、产品推荐系统实现概述

### 8.1 核心数据结构

系统定义了两个核心数据类型：

- **ProductInfo**：包含产品名称、产品简介、产品类型、推荐理由四个字段
- **ProductRecommendResponse**：派生自 BaseResponse，包含产品列表和相关分析信息

### 8.2 用户特征分析

系统从数据库中读取用户特征数据，并进行智能分析：

- **数据获取**：从数据库管理器获取用户画像摘要，转换为标准 UserProfile 格式
- **特征分析**：基于年龄、性别、行业、收入等维度进行用户类型分类
- **需求推断**：分析风险偏好、预算敏感度等推荐策略参数

### 8.3 产品搜索引擎

基于 ElasticSearch 双索引架构实现的产品搜索引擎：

- **双索引设计**：推荐索引用于快速筛选，详细信息索引用于获取完整产品数据
- **四层匹配算法**：硬性筛选、需求匹配、偏好匹配、价值匹配
- **兜底机制**：当无法匹配任何产品时，去除硬性条件返回评分最高的产品

### 8.4 LLM 增强的产品信息生成

使用大语言模型从详细产品信息中生成用户友好的推荐内容：

- **智能提取**：从复杂的产品数据中提取关键信息
- **个性化生成**：结合用户特征生成个性化的产品描述和推荐理由
- **降级处理**：当 LLM 不可用时使用规则引擎作为后备方案

### 8.5 工作流集成

系统通过 LangGraph 工作流实现完整的推荐流程：

1. **用户画像分析**：获取和分析用户特征
2. **产品搜索**：执行双阶段 ES 查询
3. **推荐生成**：使用 LLM 生成最终推荐结果

## 九、实施计划和后续步骤

### 9.1 实施优先级

1. **第一阶段**：基础类型定义和数据库扩展
   - 添加 `ProductInfo` 和 `ProductRecommendResponse` 类型定义
   - 扩展数据库管理器，添加用户特征转换方法
   - 更新 `util/types.py` 和相关导入

2. **第二阶段**：ElasticSearch 双索引架构
   - 创建 `insurance_products` 和 `all_products` 两个索引
   - 实现数据导入脚本，将产品数据分别写入两个索引
   - 配置 ES 客户端和连接

3. **第三阶段**：双阶段查询逻辑实现
   - 实现推荐索引的四层匹配查询
   - 实现详细信息索引的批量查询
   - 实现产品搜索引擎类

4. **第四阶段**：LLM 集成和产品信息生成
   - 集成 LLM 客户端（OpenAI/Claude）
   - 实现基于 LLM 的产品信息生成逻辑
   - 实现降级处理机制

5. **第五阶段**：用户特征分析和推荐逻辑
   - 实现用户特征分析方法
   - 实现完整的推荐流程
   - 集成到现有 LangGraph 工作流

6. **第六阶段**：测试和优化
   - 编写单元测试
   - 性能测试和优化
   - LLM 生成质量评估和优化

### 9.2 技术风险和缓解措施

1. **ElasticSearch 双索引性能风险**
   - 缓解：实现查询缓存和索引优化，合理设置分片数量
   - 监控：添加双阶段查询性能监控
   - 优化：考虑使用 ES 的 multi-search API 优化批量查询

2. **LLM 调用延迟和成本风险**
   - 缓解：实现 LLM 响应缓存，相同产品+用户特征组合复用结果
   - 降级：实现规则引擎降级方案，确保服务可用性
   - 优化：批量调用 LLM，减少单次调用开销

3. **用户特征数据不完整风险**
   - 缓解：实现默认值和推断逻辑
   - 降级：提供通用推荐策略

4. **无匹配产品风险**
   - 缓解：实现兜底逻辑，去除所有硬性筛选条件
   - 保障：确保始终能返回 top 3 产品推荐
   - 监控：记录兜底逻辑触发频率，优化筛选条件

5. **LLM 生成质量风险**
   - 缓解：设计详细的 prompt 模板，包含输出格式约束
   - 验证：实现 LLM 响应格式验证和内容合理性检查
   - 优化：收集用户反馈持续改进 prompt

### 9.3 监控和评估指标

1. **技术指标**
   - 推荐索引查询响应时间
   - 详细信息索引查询响应时间
   - LLM 调用响应时间和成功率
   - 推荐生成成功率
   - 兜底逻辑触发频率
   - 系统错误率

2. **业务指标**
   - 推荐点击率
   - 用户满意度评分
   - 推荐转化率
   - LLM 生成内容质量评分

3. **质量指标**
   - 推荐相关性评分
   - LLM 生成内容准确性
   - 用户反馈质量
   - 推荐多样性指标

4. **成本指标**
   - LLM 调用成本
   - ES 查询资源消耗
   - 缓存命中率

## 十、总结

该设计文档提供了完整的产品推荐系统实现方案，采用双索引架构和 LLM 增强的方式：

1. **双索引架构**：分离推荐筛选和详细信息存储，提高查询效率
2. **四层匹配算法**：在推荐索引中实现精准的产品筛选
3. **LLM 增强生成**：使用大语言模型生成用户友好的产品信息
4. **降级处理机制**：确保在 LLM 不可用时系统仍能正常工作
5. **完整的监控体系**：涵盖技术、业务、质量和成本各个维度

通过分阶段实施，可以确保系统的稳定性和可维护性，同时提供高质量的个性化产品推荐服务。
