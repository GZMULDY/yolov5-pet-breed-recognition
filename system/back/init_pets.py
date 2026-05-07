"""
宠物品种数据初始化模块

【模块职责】
在系统首次启动时，将预定义的宠物分类和品种数据初始化到数据库中。

【数据结构】
采用嵌套字典结构定义层级分类和品种信息：

PET_BREEDS_DATA = {
    "猫类": {
        "icon": "🐱",
        "children": {
            "短毛猫": {
                "children": {
                    "英国短毛猫": {
                        "name_en": "british_shorthair",
                        "description": "...",
                        ...
                    }
                }
            }
        }
    }
}

【初始化流程】
┌─────────────────────────────────────────────────────────────────┐
│  检查数据库是否已有数据                                          │
│       ↓ (无数据)                                                │
│  递归遍历数据字典                                                │
│       ↓                                                         │
│  创建分类记录 (PetCategory)                                      │
│       ↓                                                         │
│  如果是最底层分类，创建品种记录 (PetBreed)                        │
│       ↓                                                         │
│  提交事务                                                        │
└─────────────────────────────────────────────────────────────────┘

【幂等性】
脚本可重复执行，不会产生重复数据：
- 检查是否存在分类记录，存在则跳过初始化

【调用时机】
在 FastAPI 应用启动事件 (startup_event) 中自动调用

【数据来源】
宠物品种数据来自公开资料整理，包括：
- 品种名称（中英文）
- 原产地
- 性格特点
- 饲养建议
- 饮食需求
- 常见健康问题
- 体型大小
- 寿命范围
"""

import sys
import os
from pathlib import Path

# =============================================================================
# 路径配置
# =============================================================================
# 将当前目录添加到 Python 路径
# 确保后续导入语句能正确解析当前包内的模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import database
import models

# =============================================================================
# 宠物品种数据定义
# =============================================================================
# 【数据结构说明】
# 顶层键为一级分类名称
# 每个分类包含:
#   - icon: 图标（emoji 或图标类名）
#   - children: 子分类字典
#   - 或品种信息（如果是最终品种）
#
# 品种信息字段：
#   - name_en: 英文名称
#   - description: 品种描述
#   - origin: 原产地
#   - personality: 性格特点
#   - care_tips: 饲养建议
#   - diet_needs: 饮食需求
#   - health_issues: 常见健康问题
#   - size: 体型大小
#   - lifespan: 寿命范围
PET_BREEDS_DATA = {
    "猫类": {
        "icon": "🐱",
        "children": {
            "短毛猫": {
                "icon": "🐈",
                "children": {
                    "东方短毛猫": {"name_en": "abyssinian", "description": "阿比西尼亚猫是一种古老的猫品种，体型优雅，毛色独特。", "origin": "埃塞俄比亚/埃及", "personality": "活泼好动、聪明好奇、亲人", "care_tips": "毛发短易打理，每周梳理1-2次即可，注意清洁耳朵和眼睛。", "diet_needs": "优质猫粮为主，适量补充蛋白质。", "health_issues": "常见牙齿问题，定期检查口腔。", "size": "中小型", "lifespan": "12-15年"},
                    "孟加拉猫": {"name_en": "bengal", "description": "孟加拉猫具有野性美的外观，身上的豹纹非常独特。", "origin": "美国", "personality": "精力充沛、聪明活泼、喜欢玩水", "care_tips": "需要大量运动和玩耍时间，定期梳理毛发。", "diet_needs": "高蛋白饮食，可适量喂食生肉。", "health_issues": "需注意心脏健康，定期体检。", "size": "中大型", "lifespan": "12-16年"},
                    "孟买猫": {"name_en": "bombay", "description": "孟买猫全身乌黑光亮，像一只小型黑豹。", "origin": "美国", "personality": "亲人友好、活泼好动、喜欢与人互动", "care_tips": "毛发短，每周梳理即可，注意泪痕清洁。", "diet_needs": "均衡营养的猫粮。", "health_issues": "注意呼吸系统健康。", "size": "中型", "lifespan": "12-16年"},
                    "英国短毛猫": {"name_en": "british_shorthair", "description": "英国短毛猫体型圆润，毛色多样，是最受欢迎的猫品种之一。", "origin": "英国", "personality": "温顺安静、稳重独立、耐心", "care_tips": "定期梳理防止掉毛，控制饮食避免肥胖。", "diet_needs": "需控制食量，避免过度肥胖。", "health_issues": "容易肥胖，需注意体重管理。", "size": "中型到大型", "lifespan": "12-17年"},
                    "埃及猫": {"name_en": "egyptian_mau", "description": "埃及猫是自然形成的斑点猫品种，非常古老。", "origin": "埃及", "personality": "聪明活泼、忠诚亲人、喜欢运动", "care_tips": "短毛易打理，需要足够的活动空间。", "diet_needs": "高蛋白饮食。", "health_issues": "注意心脏健康。", "size": "中型", "lifespan": "12-15年"},
                    "日本短尾猫": {"name_en": "japanese_chin", "description": "日本短尾猫体型小巧，尾巴短小卷曲。", "origin": "日本", "personality": "聪明活泼、亲人友好、喜欢玩耍", "care_tips": "毛发短易护理，需要陪伴和互动。", "diet_needs": "均衡营养。", "health_issues": "一般健康状况良好。", "size": "小型", "lifespan": "12-15年"},
                    "俄罗斯蓝猫": {"name_en": "russian_blue", "description": "俄罗斯蓝猫拥有独特的蓝灰色毛发和绿色的眼睛。", "origin": "俄罗斯", "personality": "温柔安静、聪明敏感、认主", "care_tips": "毛发短，每周梳理，注意口腔卫生。", "diet_needs": "优质猫粮。", "health_issues": "注意泌尿系统健康。", "size": "中型", "lifespan": "15-20年"},
                    "暹罗猫": {"name_en": "siamese", "description": "暹罗猫以其独特的重点色和蓝色眼睛闻名。", "origin": "泰国", "personality": "聪明好奇、话多亲人、粘人", "care_tips": "短毛易打理，需要大量陪伴和互动。", "diet_needs": "注意控制体重。", "health_issues": "注意牙齿和呼吸系统。", "size": "中型", "lifespan": "12-15年"},
                    "斯芬克斯猫": {"name_en": "sphynx", "description": "斯芬克斯猫是无毛猫品种，皮肤有绒毛触感。", "origin": "加拿大", "personality": "活泼亲人、聪明粘人、怕冷", "care_tips": "需要定期洗澡清洁皮肤，注意保暖。", "diet_needs": "代谢快，需要更多热量摄入。", "health_issues": "注意皮肤护理和心脏健康。", "size": "中型", "lifespan": "12-14年"},
                    "美国短毛猫": {"name_en": "american_bulldog", "description": "美国短毛猫体型健壮，毛色多样。", "origin": "美国", "personality": "健康活泼、适应性强、亲人", "care_tips": "短毛易护理，定期体检。", "diet_needs": "均衡营养。", "health_issues": "一般健康状况良好。", "size": "中型到大型", "lifespan": "15-20年"},
                }
            },
            "长毛猫": {
                "icon": "🐅",
                "children": {
                    "波斯猫": {"name_en": "persian", "description": "波斯猫是最著名的长毛猫品种，拥有华丽的长毛和扁平的脸。", "origin": "伊朗", "personality": "温顺安静、亲人友好、慵懒", "care_tips": "需要每天梳理毛发，定期洗澡，注意泪痕。", "diet_needs": "控制饮食避免肥胖，选择易消化的食物。", "health_issues": "注意呼吸道和眼睛问题。", "size": "中型到大型", "lifespan": "12-17年"},
                    "缅因猫": {"name_en": "maine_coon", "description": "缅因猫是体型最大的猫品种之一，被称为温柔的巨人。", "origin": "美国", "personality": "温顺友好、聪明活泼、亲人", "care_tips": "毛发浓密需定期梳理，注意耳朵清洁。", "diet_needs": "需要高质量蛋白质饮食。", "health_issues": "注意心脏和关节健康。", "size": "大型", "lifespan": "12-15年"},
                    "布偶猫": {"name_en": "ragdoll", "description": "布偶猫体型大，毛色美丽，性格温顺。", "origin": "美国", "personality": "温顺粘人、安静友好、喜欢被抱", "care_tips": "长毛需定期梳理，注意室内安全。", "diet_needs": "均衡营养。", "health_issues": "注意心脏健康。", "size": "大型", "lifespan": "12-17年"},
                    "伯曼猫": {"name_en": "birman", "description": "伯曼猫又称缅甸圣猫，拥有蓝色眼睛和重点色毛色。", "origin": "缅甸", "personality": "温柔友好、安静亲人、忠诚", "care_tips": "长毛需定期梳理，注意爪子护理。", "diet_needs": "均衡营养。", "health_issues": "一般健康状况良好。", "size": "中型到大型", "lifespan": "12-16年"},
                }
            }
        }
    },
    "狗类": {
        "icon": "🐕",
        "children": {
            "大型犬": {
                "icon": "🦮",
                "children": {
                    "大白熊犬": {"name_en": "great_pyrenees", "description": "大白熊犬体型巨大，毛色雪白，是优秀的守护犬。", "origin": "法国/西班牙", "personality": "忠诚勇敢、温顺友好、保护欲强", "care_tips": "厚毛需定期梳理，需要足够运动空间。", "diet_needs": "高蛋白饮食，食量较大。", "health_issues": "注意关节和心脏健康。", "size": "大型", "lifespan": "10-12年"},
                    "圣伯纳犬": {"name_en": "saint_bernard", "description": "圣伯纳犬是著名的救援犬，体型巨大，性格温顺。", "origin": "瑞士", "personality": "温顺友好、忠诚亲人、耐心", "care_tips": "厚毛需定期梳理，注意控制体重。", "diet_needs": "食量较大，需控制饮食。", "health_issues": "注意关节和心脏问题。", "size": "超大型", "lifespan": "8-10年"},
                    "纽芬兰犬": {"name_en": "newfoundland", "description": "纽芬兰犬体型巨大，擅长水中救援。", "origin": "加拿大", "personality": "温顺友好、聪明勇敢、喜欢水", "care_tips": "厚毛需定期梳理，需要足够运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意关节和心脏健康。", "size": "超大型", "lifespan": "8-10年"},
                    "大丹犬": {"name_en": "great_dane", "description": "大丹犬是世界上最高的犬种，被称为太阳神。", "origin": "德国", "personality": "友好温和、忠诚亲人、勇敢", "care_tips": "短毛易护理，需要足够空间活动。", "diet_needs": "幼犬期需注意骨骼发育。", "health_issues": "注意心脏和骨骼问题。", "size": "超大型", "lifespan": "7-10年"},
                    "藏獒": {"name_en": "Tibetan_mastiff", "description": "藏獒是古老的护卫犬，体型巨大，勇猛忠诚。", "origin": "中国西藏", "personality": "勇敢忠诚、独立性强、领地意识强", "care_tips": "厚毛需定期梳理，需要早期社会化训练。", "diet_needs": "高蛋白饮食。", "health_issues": "注意关节健康。", "size": "大型到超大型", "lifespan": "10-14年"},
                    "斗牛獒": {"name_en": "bull_mastiff", "description": "斗牛獒是优秀的护卫犬，体型健壮。", "origin": "英国", "personality": "忠诚勇敢、温和友好、保护欲强", "care_tips": "短毛易护理，需要适度运动。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意呼吸和关节问题。", "size": "大型", "lifespan": "8-10年"},
                    "德国牧羊犬": {"name_en": "german_shepherd", "description": "德国牧羊犬是最优秀的工作犬之一，智商高。", "origin": "德国", "personality": "聪明忠诚、勇敢服从、工作热情高", "care_tips": "需要大量运动和训练，定期梳理毛发。", "diet_needs": "高蛋白饮食，注意营养均衡。", "health_issues": "注意髋关节和皮肤问题。", "size": "大型", "lifespan": "9-13年"},
                    "杜宾犬": {"name_en": "Doberman", "description": "杜宾犬体型优美，智商高，是优秀的护卫犬。", "origin": "德国", "personality": "聪明勇敢、忠诚服从、警惕性高", "care_tips": "短毛易护理，需要大量运动和训练。", "diet_needs": "高蛋白饮食。", "health_issues": "注意心脏和骨骼健康。", "size": "大型", "lifespan": "10-13年"},
                    "拳师犬": {"name_en": "boxer", "description": "拳师犬体型健壮，性格活泼，是优秀的家庭犬。", "origin": "德国", "personality": "活泼友好、忠诚亲人、喜欢玩耍", "care_tips": "短毛易护理，需要足够运动。", "diet_needs": "幼犬期注意营养。", "health_issues": "注意心脏和癌症问题。", "size": "大型", "lifespan": "10-12年"},
                    "伯恩山犬": {"name_en": "bernese_mountain_dog", "description": "伯恩山犬体型巨大，毛色美丽，性格温顺。", "origin": "瑞士", "personality": "温顺友好、忠诚亲人、耐心", "care_tips": "厚毛需定期梳理，需要足够运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意癌症和关节问题。", "size": "大型", "lifespan": "6-8年"},
                    "大瑞士山地犬": {"name_en": "Greater_Swiss_Mountain_dog", "description": "大瑞士山地犬是古老的工作犬，体型健壮。", "origin": "瑞士", "personality": "温顺友好、忠诚勇敢、工作努力", "care_tips": "短毛易护理，需要足够运动。", "diet_needs": "均衡营养。", "health_issues": "注意关节健康。", "size": "大型", "lifespan": "10-11年"},
                    "狼狗": {"name_en": "German_shorthaired", "description": "德国短毛指示犬是多功能的运动犬。", "origin": "德国", "personality": "聪明活泼、精力充沛、友好", "care_tips": "需要大量运动和训练，定期梳理毛发。", "diet_needs": "高能量饮食。", "health_issues": "注意髋关节健康。", "size": "大型", "lifespan": "12-14年"},
                }
            },
            "中型犬": {
                "icon": "🐕‍🦺",
                "children": {
                    "英国可卡犬": {"name_en": "english_cocker_spaniel", "description": "英国可卡犬是优秀的猎犬，也是可爱的家庭犬。", "origin": "英国", "personality": "活泼友好、聪明亲人、服从性好", "care_tips": "长毛需定期梳理，需要足够运动。", "diet_needs": "注意控制体重。", "health_issues": "注意耳朵和眼睛问题。", "size": "中型", "lifespan": "12-15年"},
                    "英国雪达犬": {"name_en": "english_setter", "description": "英国雪达犬外观优雅，是优秀的猎犬。", "origin": "英国", "personality": "友好活泼、温柔亲人、聪明", "care_tips": "长毛需定期梳理，需要大量运动。", "diet_needs": "均衡营养。", "health_issues": "注意癌症和耳部问题。", "size": "中型到大型", "lifespan": "11-15年"},
                    "斑点狗": {"name_en": "german_shorthaired", "description": "斑点狗以独特的斑点图案闻名。", "origin": "克罗地亚", "personality": "聪明活泼、友好亲人、精力充沛", "care_tips": "短毛易护理，需要大量运动。", "diet_needs": "高能量饮食。", "health_issues": "注意耳部和肾脏问题。", "size": "中型", "lifespan": "10-13年"},
                    "松狮犬": {"name_en": "chow", "description": "松狮犬拥有独特的蓝色舌头和浓密的毛发。", "origin": "中国", "personality": "独立忠诚、安静稳重、领地意识强", "care_tips": "厚毛需定期梳理，注意控制体重。", "diet_needs": "注意饮食均衡。", "health_issues": "注意髋关节和眼睛问题。", "size": "中型", "lifespan": "12-15年"},
                    "柴犬": {"name_en": "shiba_inu", "description": "柴犬是日本的本土犬种，表情丰富。", "origin": "日本", "personality": "独立聪明、活泼好动、忠诚", "care_tips": "双层毛需定期梳理，掉毛季增加梳理频率。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意关节和皮肤问题。", "size": "中型", "lifespan": "12-15年"},
                    "萨摩耶": {"name_en": "samoyed", "description": "萨摩耶拥有美丽的白色毛发和微笑的表情。", "origin": "西伯利亚", "personality": "友好活泼、聪明亲人、精力充沛", "care_tips": "厚毛需定期梳理，需要足够运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意糖尿病和皮肤问题。", "size": "中型", "lifespan": "12-14年"},
                    "哈士奇": {"name_en": "Siberian_husky", "description": "哈士奇是雪橇犬，拥有漂亮的蓝眼睛。", "origin": "西伯利亚", "personality": "友好活泼、精力充沛、调皮", "care_tips": "厚毛需定期梳理，需要大量运动。", "diet_needs": "高能量饮食。", "health_issues": "注意眼睛和关节问题。", "size": "中型", "lifespan": "12-14年"},
                    "阿拉斯加": {"name_en": "malamute", "description": "阿拉斯加雪橇犬是大型雪橇犬，毛发浓密。", "origin": "阿拉斯加", "personality": "友好忠诚、精力充沛、调皮", "care_tips": "厚毛需定期梳理，需要大量运动。", "diet_needs": "高能量饮食。", "health_issues": "注意关节和皮肤问题。", "size": "大型", "lifespan": "10-12年"},
                    "威尔士柯基": {"name_en": "Pembroke", "description": "威尔士柯基犬体型小巧，腿短屁股圆。", "origin": "英国", "personality": "聪明活泼、友好亲人、勇敢", "care_tips": "短毛易护理，注意控制体重。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意椎间盘问题。", "size": "小型", "lifespan": "12-15年"},
                    "柯基": {"name_en": "Cardigan", "description": "卡迪根柯基犬比彭布罗克柯基稍大。", "origin": "英国", "personality": "聪明活泼、忠诚友好、调皮", "care_tips": "短毛易护理，注意体重管理。", "diet_needs": "控制饮食。", "health_issues": "注意关节问题。", "size": "小型", "lifespan": "12-15年"},
                    "腊肠犬": {"name_en": "dachshund", "description": "腊肠犬身体长腿短，是著名的猎獾犬。", "origin": "德国", "personality": "聪明勇敢、活泼好动、忠诚", "care_tips": "短毛易护理，注意脊椎保护。", "diet_needs": "控制体重避免脊椎负担。", "health_issues": "注意椎间盘疾病。", "size": "小型", "lifespan": "12-16年"},
                    "沙皮犬": {"name_en": "Chinese_Shar_Pei", "description": "沙皮犬拥有独特的褶皱皮肤。", "origin": "中国", "personality": "独立忠诚、安静友好、领地意识强", "care_tips": "褶皱处需注意清洁护理。", "diet_needs": "注意皮肤过敏。", "health_issues": "注意皮肤和眼睛问题。", "size": "中型", "lifespan": "8-12年"},
                }
            },
            "小型犬": {
                "icon": "🐶",
                "children": {
                    "吉娃娃": {"name_en": "chihuahua", "description": "吉娃娃是世界上最小的犬种，体型娇小。", "origin": "墨西哥", "personality": "活泼勇敢、忠诚粘人、警惕性高", "care_tips": "短毛易护理，注意保暖。", "diet_needs": "少量多餐，避免低血糖。", "health_issues": "注意牙齿和膝盖问题。", "size": "超小型", "lifespan": "12-20年"},
                    "博美犬": {"name_en": "pomeranian", "description": "博美犬体型小巧，毛发蓬松，非常可爱。", "origin": "德国/波兰", "personality": "活泼好奇、聪明亲人、喜欢叫", "care_tips": "厚毛需定期梳理，需要陪伴。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意牙齿和气管问题。", "size": "小型", "lifespan": "12-16年"},
                    "巴哥犬": {"name_en": "pug", "description": "巴哥犬面部扁平，表情忧郁，非常可爱。", "origin": "中国", "personality": "友好亲人、活泼可爱、粘人", "care_tips": "面部褶皱需注意清洁，避免剧烈运动。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意呼吸和眼睛问题。", "size": "小型", "lifespan": "12-15年"},
                    "约克夏梗": {"name_en": "yorkshire_terrier", "description": "约克夏梗体型小巧，毛发如丝般光滑。", "origin": "英国", "personality": "勇敢自信、聪明活泼、亲人", "care_tips": "长毛需每天梳理，定期美容。", "diet_needs": "注意牙齿健康。", "health_issues": "注意气管和牙齿问题。", "size": "超小型", "lifespan": "13-16年"},
                    "马尔济斯": {"name_en": "Maltese_dog", "description": "马尔济斯犬拥有纯白色的长毛，非常优雅。", "origin": "马耳他", "personality": "友好亲人、活泼可爱、粘人", "care_tips": "长毛需每天梳理，定期洗澡。", "diet_needs": "注意牙齿健康。", "health_issues": "注意牙齿和皮肤问题。", "size": "小型", "lifespan": "12-15年"},
                    "西施犬": {"name_en": "Shih-Tzu", "description": "西施犬是中国古老的观赏犬，毛发华丽。", "origin": "中国", "personality": "友好亲人、活泼可爱、调皮", "care_tips": "长毛需每天梳理，定期美容。", "diet_needs": "控制饮食。", "health_issues": "注意呼吸道和眼睛问题。", "size": "小型", "lifespan": "10-18年"},
                    "北京犬": {"name_en": "Pekinese", "description": "北京犬是中国古老的宫廷犬，姿态优雅。", "origin": "中国", "personality": "独立自信、忠诚亲人、勇敢", "care_tips": "长毛需定期梳理，注意面部清洁。", "diet_needs": "控制饮食。", "health_issues": "注意呼吸道和眼睛问题。", "size": "小型", "lifespan": "12-15年"},
                    "蝴蝶犬": {"name_en": "papillon", "description": "蝴蝶犬因耳朵像蝴蝶而得名，体型小巧。", "origin": "法国", "personality": "聪明活泼、友好亲人、喜欢玩耍", "care_tips": "长毛需定期梳理，需要训练。", "diet_needs": "均衡营养。", "health_issues": "注意牙齿和膝盖问题。", "size": "小型", "lifespan": "12-16年"},
                    "迷你杜宾": {"name_en": "miniature_pinscher", "description": "迷你杜宾体型小但气质勇敢。", "origin": "德国", "personality": "聪明勇敢、活泼好动、忠诚", "care_tips": "短毛易护理，需要适度运动。", "diet_needs": "控制饮食。", "health_issues": "注意膝盖和牙齿问题。", "size": "小型", "lifespan": "12-16年"},
                    "法斗": {"name_en": "French_bulldog", "description": "法国斗牛犬体型紧凑，是受欢迎的宠物犬。", "origin": "法国", "personality": "友好亲人、活泼可爱、粘人", "care_tips": "注意呼吸道问题，避免剧烈运动。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意呼吸和脊椎问题。", "size": "小型", "lifespan": "10-12年"},
                    "巴吉度": {"name_en": "basset_hound", "description": "巴吉度犬腿短身长，耳朵很大。", "origin": "法国", "personality": "温顺友好、耐心亲人、嗅觉灵敏", "care_tips": "长毛需定期梳理，注意耳朵清洁。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意耳朵和脊椎问题。", "size": "中型", "lifespan": "10-12年"},
                    "比格犬": {"name_en": "beagle", "description": "比格犬是著名的猎兔犬，嗅觉灵敏。", "origin": "英国", "personality": "友好活泼、好奇贪吃、亲人", "care_tips": "短毛易护理，需要大量运动。", "diet_needs": "注意控制食量。", "health_issues": "注意耳朵和脊椎问题。", "size": "小型", "lifespan": "12-15年"},
                }
            },
            "梗犬类": {
                "icon": "🦔",
                "children": {
                    "苏格兰梗": {"name_en": "scottish_terrier", "description": "苏格兰梗体型小但性格勇敢。", "origin": "英国", "personality": "独立勇敢、聪明活泼、忠诚", "care_tips": "硬毛需定期美容，注意背部护理。", "diet_needs": "控制饮食。", "health_issues": "注意癌症和膀胱问题。", "size": "小型", "lifespan": "11-13年"},
                    "雪纳瑞": {"name_en": "standard_schnauzer", "description": "雪纳瑞有独特的胡须造型。", "origin": "德国", "personality": "聪明勇敢、活泼友好、忠诚", "care_tips": "硬毛需定期美容，需要训练。", "diet_needs": "均衡营养。", "health_issues": "注意胰腺和皮肤问题。", "size": "中型", "lifespan": "13-16年"},
                    "迷你雪纳瑞": {"name_en": "miniature_schnauzer", "description": "迷你雪纳瑞是受欢迎的家庭犬。", "origin": "德国", "personality": "聪明友好、活泼亲人、警惕", "care_tips": "硬毛需定期美容。", "diet_needs": "控制饮食。", "health_issues": "注意胰腺和结石问题。", "size": "小型", "lifespan": "12-15年"},
                    "凯恩梗": {"name_en": "cairn", "description": "凯恩梗是活泼的小型梗犬。", "origin": "英国", "personality": "活泼勇敢、聪明友好、好奇", "care_tips": "硬毛需定期梳理。", "diet_needs": "均衡营养。", "health_issues": "注意体重和牙齿问题。", "size": "小型", "lifespan": "12-15年"},
                    "牛头梗": {"name_en": "staffordshire_bull_terrier", "description": "牛头梗肌肉发达，性格勇敢。", "origin": "英国", "personality": "勇敢忠诚、友好亲人、活泼", "care_tips": "短毛易护理，需要适度运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意皮肤和关节问题。", "size": "中型", "lifespan": "12-14年"},
                    "美国斯塔福梗": {"name_en": "American_Staffordshire_terrier", "description": "美国斯塔福梗强壮有力。", "origin": "美国", "personality": "勇敢忠诚、友好亲人、聪明", "care_tips": "短毛易护理，需要训练和社会化。", "diet_needs": "高蛋白饮食。", "health_issues": "注意关节和心脏问题。", "size": "中型", "lifespan": "12-16年"},
                    "比特犬": {"name_en": "american_pit_bull_terrier", "description": "比特犬肌肉发达，勇敢忠诚。", "origin": "美国", "personality": "勇敢忠诚、聪明活泼、亲人", "care_tips": "需要早期社会化训练和适度运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意关节和皮肤问题。", "size": "中型", "lifespan": "12-14年"},
                    "西高地白梗": {"name_en": "West_Highland_white_terrier", "description": "西高地白梗全身雪白，非常可爱。", "origin": "英国", "personality": "活泼友好、聪明勇敢、调皮", "care_tips": "硬毛需定期美容。", "diet_needs": "控制饮食。", "health_issues": "注意皮肤和牙齿问题。", "size": "小型", "lifespan": "12-16年"},
                    "万能梗": {"name_en": "Airedale", "description": "万能梗是梗犬中体型最大的。", "origin": "英国", "personality": "聪明勇敢、友好活泼、忠诚", "care_tips": "硬毛需定期美容，需要大量运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意癌症和皮肤问题。", "size": "中型", "lifespan": "10-13年"},
                    "贝灵顿梗": {"name_en": "Bedlington_terrier", "description": "贝灵顿梗外形像小羊。", "origin": "英国", "personality": "温柔友好、活泼亲人、聪明", "care_tips": "硬毛需定期美容。", "diet_needs": "控制饮食。", "health_issues": "注意肝脏和眼睛问题。", "size": "小型", "lifespan": "14-16年"},
                    "边境梗": {"name_en": "Border_terrier", "description": "边境梗体型小但勇敢。", "origin": "英国", "personality": "友好活泼、聪明勇敢、亲人", "care_tips": "硬毛需定期梳理。", "diet_needs": "均衡营养。", "health_issues": "注意癫痫和心脏问题。", "size": "小型", "lifespan": "12-15年"},
                    "拉萨犬": {"name_en": "Lhasa", "description": "拉萨犬是古老的西藏犬种。", "origin": "中国西藏", "personality": "忠诚独立、聪明活泼、警惕", "care_tips": "长毛需定期梳理。", "diet_needs": "均衡营养。", "health_issues": "注意皮肤和关节问题。", "size": "小型", "lifespan": "12-15年"},
                }
            },
            "牧羊犬类": {
                "icon": "🐑",
                "children": {
                    "边境牧羊犬": {"name_en": "Border_collie", "description": "边境牧羊犬是智商最高的犬种。", "origin": "英国", "personality": "聪明活泼、精力充沛、工作热情高", "care_tips": "需要大量运动和智力刺激，定期梳理毛发。", "diet_needs": "高能量饮食。", "health_issues": "注意髋关节和癫痫。", "size": "中型", "lifespan": "12-15年"},
                    "苏格兰牧羊犬": {"name_en": "collie", "description": "苏格兰牧羊犬外观优雅，性格温顺。", "origin": "英国", "personality": "温柔友好、聪明忠诚、亲人", "care_tips": "长毛需定期梳理，需要足够运动。", "diet_needs": "均衡营养。", "health_issues": "注意眼睛和髋关节问题。", "size": "中型到大型", "lifespan": "12-14年"},
                    "喜乐蒂牧羊犬": {"name_en": "Shetland_sheepdog", "description": "喜乐蒂牧羊犬是小型牧羊犬。", "origin": "英国", "personality": "聪明友好、活泼亲人、忠诚", "care_tips": "长毛需定期梳理，需要运动和训练。", "diet_needs": "均衡营养。", "health_issues": "注意眼睛和皮肤问题。", "size": "小型", "lifespan": "12-14年"},
                    "古代牧羊犬": {"name_en": "Old_English_sheepdog", "description": "古代牧羊犬毛发蓬松，非常可爱。", "origin": "英国", "personality": "友好亲人、聪明活泼、调皮", "care_tips": "厚毛需每天梳理，需要足够运动。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意髋关节和耳朵问题。", "size": "大型", "lifespan": "10-12年"},
                    "德国牧羊犬": {"name_en": "German_shepherd", "description": "德国牧羊犬是最优秀的工作犬。", "origin": "德国", "personality": "聪明忠诚、勇敢服从、工作热情高", "care_tips": "需要大量运动和训练，定期梳理毛发。", "diet_needs": "高蛋白饮食。", "health_issues": "注意髋关节和皮肤问题。", "size": "大型", "lifespan": "9-13年"},
                    "比利时牧羊犬": {"name_en": "malinois", "description": "比利时牧羊犬是优秀的工作犬。", "origin": "比利时", "personality": "聪明勇敢、精力充沛、忠诚", "care_tips": "需要大量运动和训练。", "diet_needs": "高能量饮食。", "health_issues": "注意髋关节和癫痫。", "size": "中型", "lifespan": "12-14年"},
                    "澳大利亚牧羊犬": {"name_en": "kelpie", "description": "澳大利亚牧羊犬精力充沛。", "origin": "澳大利亚", "personality": "聪明活泼、精力充沛、工作努力", "care_tips": "需要大量运动和智力刺激。", "diet_needs": "高能量饮食。", "health_issues": "注意髋关节健康。", "size": "中型", "lifespan": "12-15年"},
                    "波利犬": {"name_en": "komondor", "description": "波利犬拥有独特的绳状毛发。", "origin": "匈牙利", "personality": "忠诚勇敢、独立性强、保护欲强", "care_tips": "特殊毛发需专业护理。", "diet_needs": "均衡营养。", "health_issues": "注意关节健康。", "size": "大型", "lifespan": "10-12年"},
                    "匈牙利牧羊犬": {"name_en": "kuvasz", "description": "匈牙利牧羊犬是大型护卫犬。", "origin": "匈牙利", "personality": "忠诚勇敢、独立性强、领地意识强", "care_tips": "厚毛需定期梳理，需要足够运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意关节健康。", "size": "大型", "lifespan": "10-12年"},
                }
            },
            "猎犬类": {
                "icon": "🏹",
                "children": {
                    "金毛寻回犬": {"name_en": "golden_retriever", "description": "金毛寻回犬是最受欢迎的家庭犬之一。", "origin": "英国", "personality": "友好亲人、聪明活泼、耐心", "care_tips": "长毛需定期梳理，需要足够运动。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意癌症和关节问题。", "size": "大型", "lifespan": "10-12年"},
                    "拉布拉多": {"name_en": "Labrador_retriever", "description": "拉布拉多是世界最受欢迎的犬种。", "origin": "加拿大", "personality": "友好亲人、聪明活泼、服从性好", "care_tips": "短毛易护理，需要大量运动。", "diet_needs": "控制饮食避免肥胖。", "health_issues": "注意肥胖和关节问题。", "size": "大型", "lifespan": "10-12年"},
                    "哈士奇": {"name_en": "Siberian_husky", "description": "哈士奇是雪橇犬，精力充沛。", "origin": "西伯利亚", "personality": "友好活泼、精力充沛、调皮", "care_tips": "厚毛需定期梳理，需要大量运动。", "diet_needs": "高能量饮食。", "health_issues": "注意眼睛和关节问题。", "size": "中型", "lifespan": "12-14年"},
                    "萨摩耶": {"name_en": "samoyed", "description": "萨摩耶是雪橇犬，毛发雪白。", "origin": "西伯利亚", "personality": "友好活泼、聪明亲人、精力充沛", "care_tips": "厚毛需定期梳理，需要足够运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意糖尿病和皮肤问题。", "size": "中型", "lifespan": "12-14年"},
                    "阿富汗猎犬": {"name_en": "Afghan_hound", "description": "阿富汗猎犬拥有美丽的长毛。", "origin": "阿富汗", "personality": "独立优雅、活泼友好、亲人", "care_tips": "长毛需每天梳理，定期美容。", "diet_needs": "均衡营养。", "health_issues": "注意皮肤和癌症问题。", "size": "大型", "lifespan": "12-14年"},
                    "灰狗": {"name_en": "greyhound", "description": "灰狗是世界上跑得最快的犬种。", "origin": "中东", "personality": "温柔安静、亲人友好、聪明", "care_tips": "短毛易护理，需要适度运动。", "diet_needs": "注意营养均衡。", "health_issues": "注意骨骼和癌症问题。", "size": "大型", "lifespan": "10-14年"},
                    "惠比特": {"name_en": "whippet", "description": "惠比特是小型赛跑犬。", "origin": "英国", "personality": "温柔安静、亲人友好、活泼", "care_tips": "短毛易护理，需要适度运动。", "diet_needs": "均衡营养。", "health_issues": "注意心脏和皮肤问题。", "size": "中型", "lifespan": "12-15年"},
                    "爱尔兰雪达犬": {"name_en": "Irish_setter", "description": "爱尔兰雪达犬拥有美丽的红毛。", "origin": "爱尔兰", "personality": "活泼友好、亲人友好、聪明", "care_tips": "长毛需定期梳理，需要大量运动。", "diet_needs": "均衡营养。", "health_issues": "注意癌症和眼睛问题。", "size": "大型", "lifespan": "11-15年"},
                    "魏玛猎犬": {"name_en": "Weimaraner", "description": "魏玛猎犬拥有独特的灰色毛发。", "origin": "德国", "personality": "聪明活泼、精力充沛、亲人", "care_tips": "短毛易护理，需要大量运动。", "diet_needs": "高能量饮食。", "health_issues": "注意胃扭转和癌症问题。", "size": "大型", "lifespan": "11-13年"},
                    "指示犬": {"name_en": "German_short-haired_pointer", "description": "德国短毛指示犬是多功能猎犬。", "origin": "德国", "personality": "聪明活泼、精力充沛、友好", "care_tips": "短毛易护理，需要大量运动。", "diet_needs": "高能量饮食。", "health_issues": "注意髋关节和癌症问题。", "size": "大型", "lifespan": "12-14年"},
                }
            },
            "玩具犬类": {
                "icon": "🧸",
                "children": {
                    "玩具贵宾": {"name_en": "toy_poodle", "description": "玩具贵宾体型小巧，聪明优雅。", "origin": "法国", "personality": "聪明活泼、亲人友好、服从性好", "care_tips": "卷毛需定期美容，注意耳朵清洁。", "diet_needs": "控制饮食。", "health_issues": "注意牙齿和关节问题。", "size": "超小型", "lifespan": "12-15年"},
                    "迷你贵宾": {"name_en": "miniature_poodle", "description": "迷你贵宾是受欢迎的家庭犬。", "origin": "法国", "personality": "聪明活泼、亲人友好、调皮", "care_tips": "卷毛需定期美容。", "diet_needs": "控制饮食。", "health_issues": "注意髋关节和眼睛问题。", "size": "小型", "lifespan": "12-15年"},
                    "标准贵宾": {"name_en": "standard_poodle", "description": "标准贵宾聪明优雅，是优秀的表演犬。", "origin": "法国", "personality": "聪明友好、活泼亲人、忠诚", "care_tips": "卷毛需定期美容，需要足够运动。", "diet_needs": "均衡营养。", "health_issues": "注意髋关节和皮肤问题。", "size": "大型", "lifespan": "12-15年"},
                    "吉娃娃": {"name_en": "chihuahua", "description": "吉娃娃是世界上最小的犬种。", "origin": "墨西哥", "personality": "活泼勇敢、忠诚粘人、警惕", "care_tips": "短毛易护理，注意保暖。", "diet_needs": "少量多餐。", "health_issues": "注意牙齿和膝盖问题。", "size": "超小型", "lifespan": "12-20年"},
                    "约克夏梗": {"name_en": "yorkshire_terrier", "description": "约克夏梗毛发如丝。", "origin": "英国", "personality": "勇敢自信、聪明活泼、亲人", "care_tips": "长毛需每天梳理。", "diet_needs": "注意牙齿健康。", "health_issues": "注意气管和牙齿问题。", "size": "超小型", "lifespan": "13-16年"},
                    "马尔济斯": {"name_en": "Maltese_dog", "description": "马尔济斯犬纯白优雅。", "origin": "马耳他", "personality": "友好亲人、活泼可爱、粘人", "care_tips": "长毛需每天梳理。", "diet_needs": "注意牙齿健康。", "health_issues": "注意牙齿和皮肤问题。", "size": "小型", "lifespan": "12-15年"},
                    "哈巴狗": {"name_en": "pug", "description": "巴哥犬表情可爱。", "origin": "中国", "personality": "友好亲人、活泼可爱、粘人", "care_tips": "注意面部清洁。", "diet_needs": "控制饮食。", "health_issues": "注意呼吸和眼睛问题。", "size": "小型", "lifespan": "12-15年"},
                    "北京犬": {"name_en": "Pekinese", "description": "北京犬是中国古老的宫廷犬。", "origin": "中国", "personality": "独立自信、忠诚亲人、勇敢", "care_tips": "长毛需定期梳理。", "diet_needs": "控制饮食。", "health_issues": "注意呼吸道和眼睛问题。", "size": "小型", "lifespan": "12-15年"},
                    "西施犬": {"name_en": "Shih-Tzu", "description": "西施犬毛发华丽。", "origin": "中国", "personality": "友好亲人、活泼可爱、调皮", "care_tips": "长毛需每天梳理。", "diet_needs": "控制饮食。", "health_issues": "注意呼吸道和眼睛问题。", "size": "小型", "lifespan": "10-18年"},
                    "蝴蝶犬": {"name_en": "papillon", "description": "蝴蝶犬耳朵像蝴蝶。", "origin": "法国", "personality": "聪明活泼、友好亲人、喜欢玩耍", "care_tips": "长毛需定期梳理。", "diet_needs": "均衡营养。", "health_issues": "注意牙齿和膝盖问题。", "size": "小型", "lifespan": "12-16年"},
                }
            },
            "护卫犬类": {
                "icon": "🛡️",
                "children": {
                    "罗威纳": {"name_en": "Rottweiler", "description": "罗威纳是著名的护卫犬。", "origin": "德国", "personality": "忠诚勇敢、聪明服从、保护欲强", "care_tips": "需要早期社会化训练和适度运动。", "diet_needs": "高蛋白饮食。", "health_issues": "注意髋关节和心脏问题。", "size": "大型", "lifespan": "8-10年"},
                    "杜宾犬": {"name_en": "Doberman", "description": "杜宾犬优雅勇敢。", "origin": "德国", "personality": "聪明勇敢、忠诚服从、警惕", "care_tips": "需要大量运动和训练。", "diet_needs": "高蛋白饮食。", "health_issues": "注意心脏和骨骼问题。", "size": "大型", "lifespan": "10-13年"},
                    "德国牧羊犬": {"name_en": "german_shepherd", "description": "德国牧羊犬是最优秀的工作犬。", "origin": "德国", "personality": "聪明忠诚、勇敢服从、工作热情高", "care_tips": "需要大量运动和训练。", "diet_needs": "高蛋白饮食。", "health_issues": "注意髋关节和皮肤问题。", "size": "大型", "lifespan": "9-13年"},
                    "藏獒": {"name_en": "Tibetan_mastiff", "description": "藏獒是古老的护卫犬。", "origin": "中国西藏", "personality": "勇敢忠诚、独立性强、保护欲强", "care_tips": "需要早期社会化训练。", "diet_needs": "高蛋白饮食。", "health_issues": "注意关节健康。", "size": "大型到超大型", "lifespan": "10-14年"},
                    "南非獒": {"name_en": "African_hunting_dog", "description": "南非獒是大型护卫犬。", "origin": "南非", "personality": "勇敢忠诚、保护欲强、领地意识强", "care_tips": "需要早期训练和社交。", "diet_needs": "高蛋白饮食。", "health_issues": "注意关节健康。", "size": "大型", "lifespan": "9-11年"},
                }
            },
            "其他犬类": {
                "icon": "🐕",
                "children": {
                    "斑点狗": {"name_en": "dalmatian", "description": "斑点狗以独特的斑点闻名。", "origin": "克罗地亚", "personality": "聪明活泼、友好亲人、精力充沛", "care_tips": "短毛易护理，需要大量运动。", "diet_needs": "高能量饮食。", "health_issues": "注意耳部和肾脏问题。", "size": "中型", "lifespan": "10-13年"},
                    "比格犬": {"name_en": "beagle", "description": "比格犬是著名的猎兔犬。", "origin": "英国", "personality": "友好活泼、好奇贪吃、亲人", "care_tips": "短毛易护理，需要大量运动。", "diet_needs": "注意控制食量。", "health_issues": "注意耳朵和脊椎问题。", "size": "小型", "lifespan": "12-15年"},
                    "巴吉度": {"name_en": "basset_hound", "description": "巴吉度犬腿短身长。", "origin": "法国", "personality": "温顺友好、耐心亲人、嗅觉灵敏", "care_tips": "注意耳朵清洁。", "diet_needs": "控制饮食。", "health_issues": "注意耳朵和脊椎问题。", "size": "中型", "lifespan": "10-12年"},
                    "腊肠犬": {"name_en": "dachshund", "description": "腊肠犬身体长腿短。", "origin": "德国", "personality": "聪明勇敢、活泼好动、忠诚", "care_tips": "注意脊椎保护。", "diet_needs": "控制体重。", "health_issues": "注意椎间盘疾病。", "size": "小型", "lifespan": "12-16年"},
                    "沙皮犬": {"name_en": "Chinese_Shar_Pei", "description": "沙皮犬有独特的褶皱。", "origin": "中国", "personality": "独立忠诚、安静友好、领地意识强", "care_tips": "褶皱处需注意清洁。", "diet_needs": "注意皮肤过敏。", "health_issues": "注意皮肤和眼睛问题。", "size": "中型", "lifespan": "8-12年"},
                    "松狮犬": {"name_en": "chow", "description": "松狮犬有蓝色舌头。", "origin": "中国", "personality": "独立忠诚、安静稳重、领地意识强", "care_tips": "厚毛需定期梳理。", "diet_needs": "注意饮食均衡。", "health_issues": "注意髋关节和眼睛问题。", "size": "中型", "lifespan": "12-15年"},
                    "哈士奇": {"name_en": "Siberian_husky", "description": "哈士奇是雪橇犬。", "origin": "西伯利亚", "personality": "友好活泼、精力充沛、调皮", "care_tips": "厚毛需定期梳理。", "diet_needs": "高能量饮食。", "health_issues": "注意眼睛和关节问题。", "size": "中型", "lifespan": "12-14年"},
                    "萨摩耶": {"name_en": "samoyed", "description": "萨摩耶笑容甜美。", "origin": "西伯利亚", "personality": "友好活泼、聪明亲人、精力充沛", "care_tips": "厚毛需定期梳理。", "diet_needs": "高蛋白饮食。", "health_issues": "注意糖尿病和皮肤问题。", "size": "中型", "lifespan": "12-14年"},
                    "柴犬": {"name_en": "shiba_inu", "description": "柴犬是日本犬。", "origin": "日本", "personality": "独立聪明、活泼好动、忠诚", "care_tips": "双层毛需定期梳理。", "diet_needs": "控制饮食。", "health_issues": "注意关节和皮肤问题。", "size": "中型", "lifespan": "12-15年"},
                    "秋田犬": {"name_en": "akita", "description": "秋田犬是日本国犬。", "origin": "日本", "personality": "忠诚勇敢、独立性强、亲人", "care_tips": "厚毛需定期梳理。", "diet_needs": "高蛋白饮食。", "health_issues": "注意关节和皮肤问题。", "size": "大型", "lifespan": "10-12年"},
                }
            }
        }
    }
}


def init_pet_data():
    """
    初始化宠物品种数据

    【功能】将预定义的宠物分类和品种数据写入数据库

    【执行时机】FastAPI 应用启动时自动调用

    【幂等性】如果数据库已有宠物分类数据，则跳过初始化

    【算法流程】
    1. 检查数据库是否已有分类数据
    2. 如果已有数据，输出提示并返回
    3. 递归遍历数据字典
    4. 为每个分类创建 PetCategory 记录
    5. 为最终品种创建 PetBreed 记录
    6. 提交事务

    【递归处理】
    create_categories 函数递归处理嵌套的数据结构：
    - 有 children 键：这是分类节点，创建分类并递归处理子节点
    - 无 children 键但有 name_en：这是品种节点，创建品种记录

    【事务管理】
    - 所有操作在一个事务中完成
    - 如果出错，回滚事务，不产生部分数据

    【数据完整性】
    - 分类使用 db.flush() 获取 ID，用于建立父子关系
    - 品种的外键指向所属分类的 ID
    """
    with database.SessionLocal() as db:
        try:
            # -------------------------------------------------------------------------
            # 检查是否已有数据
            # -------------------------------------------------------------------------
            existing_categories = db.query(models.PetCategory).first()
            if existing_categories:
                print("Pet data already exists, skipping initialization.")
                return

            # -------------------------------------------------------------------------
            # 分类 ID 映射
            # -------------------------------------------------------------------------
            # 用于存储名称到 ID 的映射，建立父子关系时使用
            # 格式: {分类名称: 分类ID}
            category_map = {}

            # -------------------------------------------------------------------------
            # 递归创建分类和品种
            # -------------------------------------------------------------------------
            def create_categories(data, parent_id=None, level=0):
                """
                递归创建分类和品种记录

                【参数】
                - data: 当前层级的分类/品种数据字典
                - parent_id: 父分类ID，顶级分类为 None
                - level: 当前层级深度，用于排序

                【算法】
                遍历当前层级的所有节点：
                - 创建分类记录
                - 如果有 children，递归处理子分类
                - 如果是品种（有 name_en），创建品种记录
                """
                for name, info in data.items():
                    # 获取图标（可选）
                    icon = info.get("icon")

                    # 创建分类记录
                    category = models.PetCategory(
                        name=name,
                        name_en=info.get("name_en"),
                        parent_id=parent_id,
                        icon=icon,
                        sort_order=level
                    )
                    db.add(category)
                    db.flush()  # 刷新以获取自增 ID

                    # 记录名称到 ID 的映射
                    category_map[name] = category.id
                    print(f"Created category: {name} (id: {category.id})")

                    # -----------------------------------------------------------------
                    # 判断节点类型并继续处理
                    # -----------------------------------------------------------------
                    if "children" in info:
                        # 有 children 键，这是分类节点
                        # 递归处理子分类
                        create_categories(info["children"], category.id, level + 1)
                    else:
                        # 无 children 键，检查是否为品种
                        if "name_en" in info:
                            # 有 name_en，这是品种节点
                            breed = models.PetBreed(
                                name=name,
                                name_en=info.get("name_en"),
                                category_id=category.id,
                                description=info.get("description"),
                                origin=info.get("origin"),
                                personality=info.get("personality"),
                                care_tips=info.get("care_tips"),
                                diet_needs=info.get("diet_needs"),
                                health_issues=info.get("health_issues"),
                                exercise_needs=info.get("exercise_needs"),
                                size=info.get("size"),
                                lifespan=info.get("lifespan")
                            )
                            db.add(breed)
                            print(f"  Created breed: {name}")

            # 开始递归创建
            create_categories(PET_BREEDS_DATA)

            # -------------------------------------------------------------------------
            # 提交事务
            # -------------------------------------------------------------------------
            db.commit()
            print("Pet data initialized successfully!")

        except Exception as e:
            # -------------------------------------------------------------------------
            # 错误处理：回滚事务
            # -------------------------------------------------------------------------
            db.rollback()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


# =============================================================================
# 模块入口
# =============================================================================
if __name__ == "__main__":
    # 支持直接运行此脚本初始化数据
    init_pet_data()
