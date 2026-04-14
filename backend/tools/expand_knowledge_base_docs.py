from __future__ import annotations

import re
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1] / "data" / "knowledge_base" / "China"
GENERATED_SOURCE = "local_editorial_generated"


@dataclass(frozen=True)
class ScenarioTemplate:
    filename: str
    title_suffix: str
    category: str
    tags: list[str]
    crowd_type: list[str]
    budget_level: str
    season: list[str]
    transportation: list[str]
    scene_text: str
    strategy_lines: list[str]
    risk_lines: list[str]
    copy_text: str


SCENARIOS: list[ScenarioTemplate] = [
    ScenarioTemplate(
        filename="rainy_day_family.md",
        title_suffix="雨天亲子轻松建议",
        category="rain_backup",
        tags=["rainy_day", "family", "indoor", "public_transit"],
        crowd_type=["family"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适用于下雨天气下的家庭出行，优先考虑室内友好、步行负担较低、切换成本较小的组合方式。",
        strategy_lines=[
            "上午优先安排一个室内核心点位，减少来回折返。",
            "午餐选择景点周边一公里内、适合家庭停留的餐饮空间。",
            "下午补充一个轻松型室内或半室内点位，并预留机动时间应对天气变化。",
        ],
        risk_lines=[
            "降雨时段可能导致打车等待时间增加，需要预留缓冲。",
            "如遇热门场馆排队，应及时切换到同片区替代方案。",
        ],
        copy_text="这是一条更稳妥的雨天家庭方案，重点不是塞满景点，而是让亲子出行在天气变化下依然顺畅、轻松、好调整。",
    ),
    ScenarioTemplate(
        filename="senior_slow_travel.md",
        title_suffix="长者慢节奏慢游建议",
        category="slow_travel",
        tags=["senior", "slow_travel", "less_walking", "culture"],
        crowd_type=["family", "senior"],
        budget_level="medium",
        season=["spring", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合长者或低强度出行需求，强调少折返、少爬坡、少排队，并把休息体验放在和景点同等重要的位置。",
        strategy_lines=[
            "每天控制在两到三个低强度点位，不追求高密度打卡。",
            "优先选择有座椅、遮阴、无障碍和室内休息空间的区域。",
            "午后安排节奏更缓的活动，避免连续长时间步行。",
        ],
        risk_lines=[
            "如目的地坡度较大，应优先替换为平缓路线或短驳交通方案。",
            "热门景区节假日可能排队较久，不适合长者长时间站立等待。",
        ],
        copy_text="这类方案更看重舒适度和恢复感，适合把行程做得从容一点，让旅途真正成为休息而不是赶路。",
    ),
    ScenarioTemplate(
        filename="summer_night_friends.md",
        title_suffix="夏夜朋友轻社交方案",
        category="night_relax",
        tags=["summer", "night", "friends", "food"],
        crowd_type=["friends"],
        budget_level="medium",
        season=["summer"],
        transportation=["public_transit", "taxi"],
        scene_text="适合夏季与朋友出行，白天控制暴晒与高强度行走，把更好的体验放到傍晚和夜间时段。",
        strategy_lines=[
            "白天优先室内或树荫较多的区域，避免中午暴晒。",
            "傍晚安排滨水、夜景、步行街或夜市型场景，提升社交氛围。",
            "夜间餐饮与散步结合，减少多点位频繁切换。",
        ],
        risk_lines=[
            "夜间热门区域人流大，需要预留排队与打车时间。",
            "夏季雷阵雨具有突发性，建议保留一个室内替代点。",
        ],
        copy_text="夏夜朋友出行更适合把节奏压到傍晚之后，让风景、聊天和本地夜生活自然地串在一起。",
    ),
    ScenarioTemplate(
        filename="citywalk_food.md",
        title_suffix="城市漫游与风味体验建议",
        category="citywalk_food",
        tags=["citywalk", "food", "local_flavor", "couple"],
        crowd_type=["solo", "couple", "friends"],
        budget_level="medium",
        season=["spring", "autumn", "winter"],
        transportation=["walk", "public_transit"],
        scene_text="适合把轻量步行、街区体验和地方风味结合起来，强调路线顺、停留自由度高、拍照与用餐都方便。",
        strategy_lines=[
            "以一条主街区或核心片区为中心，不做跨城式折返。",
            "把吃饭安排嵌入漫游线路中，而不是单独长距离跳转。",
            "优先选择适合慢逛、停下来拍照和短暂停留的节点。",
        ],
        risk_lines=[
            "热门街区周末拥挤，可能影响步行体验和餐饮排队时间。",
            "如天气过热或降雨，应及时把外摆型路线切换为室内商圈或展馆周边。",
        ],
        copy_text="这条方案更像一场自然发生的城市散步，把风景、街区和食物串成一条顺路且不费力的体验线。",
    ),
    ScenarioTemplate(
        filename="weekend_relaxed_couple.md",
        title_suffix="周末情侣轻松两日建议",
        category="weekend_couple",
        tags=["weekend", "couple", "relaxed", "photo_friendly"],
        crowd_type=["couple"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合周末情侣短途出行，重点在于节奏柔和、氛围舒适、适合停留与拍照，而不是高密度跑点。",
        strategy_lines=[
            "上午安排一个代表性地标或主景区，下午转入更适合漫游的片区。",
            "优先搭配咖啡馆、夜景、滨水或老街等更具氛围感的内容。",
            "保留至少一个可以灵活替换的轻量备选点位。",
        ],
        risk_lines=[
            "周末热门点位排队时间可能高于工作日，需要留出机动时间。",
            "如遇天气波动，优先保留氛围体验而不是勉强赶完所有点位。",
        ],
        copy_text="周末情侣行程更适合留白，不必追求面面俱到，只要把风景、节奏和相处体验组合到舒服即可。",
    ),
    ScenarioTemplate(
        filename="public_transit_budget.md",
        title_suffix="地铁优先低预算方案",
        category="budget_transit",
        tags=["budget", "public_transit", "less_walking", "practical"],
        crowd_type=["solo", "friends", "family"],
        budget_level="low",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit"],
        scene_text="适用于预算更敏感的出行场景，强调公共交通可达、门票友好、餐饮成本可控和路线组织效率。",
        strategy_lines=[
            "优先串联同一条地铁线或同一片公共交通便利区域。",
            "景点数量控制在够玩但不增加额外打车成本的范围内。",
            "餐饮以本地高性价比和顺路补给为主，避免跨区觅食。",
        ],
        risk_lines=[
            "高峰期公共交通拥挤，可能影响中转体验。",
            "低预算路线更依赖顺路性，一旦跨区折返，整体成本会明显上升。",
        ],
        copy_text="这类方案的重点不是一味压缩花费，而是在有限预算内把交通、吃饭和游玩安排得更顺、更值。",
    ),
    ScenarioTemplate(
        filename="museum_indoor_backup.md",
        title_suffix="博物馆室内备选方案",
        category="indoor_backup",
        tags=["museum", "indoor", "rainy_day", "culture"],
        crowd_type=["solo", "family", "couple"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合在天气不稳定、希望内容密度不下降的情况下，把行程重心转向室内文化空间与展馆片区。",
        strategy_lines=[
            "优先选择同片区的博物馆、纪念馆或展览空间，减少移动成本。",
            "把午餐安排在馆区周边，避免雨天或高温下长距离步行。",
            "下午可补一个室内商业或文化休息点，增强行程弹性。",
        ],
        risk_lines=[
            "部分展馆存在预约规则，需要提前确认开放时间。",
            "如果临时客流较大，建议用同片区二级场馆替换主场馆。",
        ],
        copy_text="当外部天气不稳定时，室内文化路线往往能兼顾内容密度、舒适度和解释性，是非常稳的备选思路。",
    ),
    ScenarioTemplate(
        filename="local_flavor_night.md",
        title_suffix="本地风味夜间体验建议",
        category="night_food",
        tags=["food", "night", "local_flavor", "friends"],
        crowd_type=["solo", "friends", "couple"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["walk", "public_transit", "taxi"],
        scene_text="适合把白天景点和夜间风味体验结合起来，重点放在地方食物、夜景氛围和短距离移动上。",
        strategy_lines=[
            "白天只安排一到两个核心游览点，给晚间留出精力和时间。",
            "晚餐后可接一个夜景、夜市或老街型场景，形成完整体验链。",
            "尽量把夜间活动压缩在同一片区，提高安全感和便利性。",
        ],
        risk_lines=[
            "夜市与老街类场景节假日人流集中，需预留等位时间。",
            "部分夜间场景适合短停留，不宜安排过多硬性打卡要求。",
        ],
        copy_text="如果想把一座城市吃得更立体、逛得更有记忆点，夜间风味路线通常是最容易留下印象的一类安排。",
    ),
    ScenarioTemplate(
        filename="family_gentle_2day.md",
        title_suffix="家庭轻量两日方案",
        category="family_gentle",
        tags=["family", "gentle_pace", "public_transit", "low_walking"],
        crowd_type=["family"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合家庭两日游，核心目标是让每一天都可完成、可休息、可根据孩子或长辈状态随时微调。",
        strategy_lines=[
            "第一天以代表性景点为主，第二天安排更轻松的补充体验。",
            "每天控制在两到三个主点位，避免全天候紧绷行程。",
            "把吃饭和休息节点提前嵌入路线，降低临场决策压力。",
        ],
        risk_lines=[
            "家庭出行变量较多，应预留至少一个可随时取消的柔性点位。",
            "如遇天气波动或孩子疲劳，优先保留最核心的一个主景点。",
        ],
        copy_text="家庭两日游最重要的是完成度和舒适度，只要节奏稳、切换少，整体体验通常会比高密度打卡更好。",
    ),
    ScenarioTemplate(
        filename="cultural_leisure_route.md",
        title_suffix="人文休闲串联路线",
        category="culture_leisure",
        tags=["culture", "history", "leisure", "citywalk"],
        crowd_type=["solo", "couple", "friends", "family"],
        budget_level="medium",
        season=["spring", "autumn", "winter"],
        transportation=["walk", "public_transit"],
        scene_text="适合对历史、人文、街区故事感兴趣的用户，强调城市文化线索的连续性，而不是孤立地看几个点。",
        strategy_lines=[
            "围绕一条文化主线安排景点，例如老城、博物馆、纪念空间与街区串联。",
            "每半天只保留一个核心主题，避免体验过散。",
            "把解说、拍照、短暂停留和饮食安排结合在一条连续动线上。",
        ],
        risk_lines=[
            "文化类场景更吃讲解和节奏，若点位过多反而容易疲劳。",
            "部分老城区道路狭窄，节假日应避开最拥挤时段。",
        ],
        copy_text="人文休闲路线的重点不在于跑得快，而在于让城市的故事线被慢慢看见、连起来、记下来。",
    ),
    ScenarioTemplate(
        filename="low_mobility_citybreak.md",
        title_suffix="低步行负担城市小住建议",
        category="low_mobility",
        tags=["low_mobility", "citybreak", "indoor", "public_transit"],
        crowd_type=["senior", "family", "solo"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合不希望高强度暴走的用户，强调步行距离短、打车或地铁切换顺、室内外比例均衡。",
        strategy_lines=[
            "每半天只安排一个核心点位和一个补充点位，减少高频折返。",
            "优先选择靠近交通节点或集中片区的景点组合。",
            "把休息空间、咖啡馆或商场型补给点预留到动线中。",
        ],
        risk_lines=[
            "如果核心点位本身面积很大，实际步行量可能高于预期，需要及时压缩内容。",
            "大客流时段容易放大体力消耗，建议避开最拥堵时段出行。",
        ],
        copy_text="低步行负担并不意味着内容单薄，而是通过更聪明的动线组合，让行程更轻松、更稳、更容易完成。",
    ),
    ScenarioTemplate(
        filename="weekend_history_walk.md",
        title_suffix="周末历史街区慢逛建议",
        category="history_weekend",
        tags=["weekend", "history", "citywalk", "photo_friendly"],
        crowd_type=["solo", "couple", "friends"],
        budget_level="medium",
        season=["spring", "autumn", "winter"],
        transportation=["walk", "public_transit"],
        scene_text="适合周末短时间内体验当地历史街区、老城氛围和代表性建筑，不需要大跨度移动。",
        strategy_lines=[
            "以一片老城或历史街区为核心，减少跨区跳转。",
            "步行段尽量压缩在一至两段，留出拍照和短暂停留时间。",
            "把用餐安排在老街附近，增强整体体验连贯性。",
        ],
        risk_lines=[
            "老街类区域在节假日可能人流密集，需避开最拥挤时间。",
            "如遇天气不佳，应准备同片区室内替代点。",
        ],
        copy_text="周末历史街区路线更适合轻松慢逛，在有限时间里看建筑、吃本地味道、感受城市旧日气息。",
    ),
    ScenarioTemplate(
        filename="spring_flower_citywalk.md",
        title_suffix="春日花景漫游建议",
        category="spring_citywalk",
        tags=["spring", "flower", "citywalk", "photo_friendly"],
        crowd_type=["solo", "couple", "friends"],
        budget_level="medium",
        season=["spring"],
        transportation=["walk", "public_transit"],
        scene_text="适合春季出行，重点放在花景、街区氛围、慢走慢看和轻量拍照体验上。",
        strategy_lines=[
            "优先围绕花景明显、步行体验较好的区域展开。",
            "把咖啡、小吃或短暂停留点嵌在漫游线路中，避免走得太赶。",
            "尽量把拍照、人文街区和休息空间放在一条连续动线上。",
        ],
        risk_lines=[
            "花期具有明显时间窗口，建议出发前确认最佳观赏时段。",
            "热门春游区域周末人流会放大拍照等待和步行压力。",
        ],
        copy_text="春日漫游更适合把节奏放缓，让花景、街区和轻松停留自然连在一起，而不是急着赶完每一个点。",
    ),
    ScenarioTemplate(
        filename="winter_sunshine_relax.md",
        title_suffix="冬日向阳休闲建议",
        category="winter_relax",
        tags=["winter", "sunshine", "relaxed", "slow_travel"],
        crowd_type=["solo", "senior", "couple"],
        budget_level="medium",
        season=["winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合冬季出行，优先考虑向阳、室内外可切换、冷风影响较小的轻松路线。",
        strategy_lines=[
            "上午安排采光更好、风感更弱的区域，减少寒冷体感。",
            "午后优先室内展馆、茶馆或商业空间，提升舒适度。",
            "傍晚尽量缩短户外停留时间，把重点内容放在白天完成。",
        ],
        risk_lines=[
            "冬季日照时间较短，热门点位需避免压到过晚时段。",
            "若遇大风或低温，需主动压缩户外线路长度。",
        ],
        copy_text="冬日行程更适合做得暖一点、短一点、顺一点，让舒适感优先于景点密度。",
    ),
    ScenarioTemplate(
        filename="heritage_weekend.md",
        title_suffix="周末文化遗产串联建议",
        category="heritage_weekend",
        tags=["weekend", "heritage", "history", "culture"],
        crowd_type=["solo", "couple", "friends", "family"],
        budget_level="medium",
        season=["spring", "autumn", "winter"],
        transportation=["public_transit", "walk"],
        scene_text="适合周末围绕古迹、历史建筑、纪念空间等文化遗产类点位进行半天到一天的串联体验。",
        strategy_lines=[
            "以一个核心文化遗产点为主轴，再补一个解释性更强的辅助点位。",
            "如果片区内有老街或展馆，可作为中段缓冲和延伸停留。",
            "尽量用步行或短距离公共交通串联，维持整体完整性。",
        ],
        risk_lines=[
            "遗产类点位往往更依赖讲解与停留，安排过多会压缩体验质量。",
            "部分老建筑开放时间有限，节假日需关注预约与限流规则。",
        ],
        copy_text="周末文化遗产路线更强调‘看懂一条线’，而不是把所有点都匆匆打卡。",
    ),
    ScenarioTemplate(
        filename="waterfront_evening.md",
        title_suffix="滨水傍晚松弛路线",
        category="waterfront_evening",
        tags=["waterfront", "evening", "relaxed", "photo_friendly"],
        crowd_type=["couple", "friends", "solo"],
        budget_level="medium",
        season=["spring", "summer", "autumn"],
        transportation=["walk", "public_transit", "taxi"],
        scene_text="适合有滨江、滨河、滨湖资源的城市，把最佳体验放在傍晚光线与夜色渐起的时段。",
        strategy_lines=[
            "白天只保留一个轻量主点，给傍晚黄金时段留足时间。",
            "把夜景、用餐和短距离散步组合成同一片区内的连续体验。",
            "避免傍晚前后大范围跨城移动，减少错过景色的风险。",
        ],
        risk_lines=[
            "滨水区域风感和温差可能更明显，需结合天气预留保暖或避雨准备。",
            "夜间热门带状区域常有人流集中，需要控制步行距离和返程时间。",
        ],
        copy_text="滨水傍晚路线最适合做减法，把最舒服的光线、风景和停留感留给一天的后半段。",
    ),
    ScenarioTemplate(
        filename="tea_oldtown_relax.md",
        title_suffix="茶馆老街松弛慢游",
        category="tea_oldtown",
        tags=["tea", "oldtown", "relaxed", "culture"],
        crowd_type=["solo", "couple", "friends", "senior"],
        budget_level="medium",
        season=["spring", "autumn", "winter"],
        transportation=["walk", "public_transit"],
        scene_text="适合有茶馆、老街、传统街区或生活氛围空间的城市，强调休闲、停留和地方日常感。",
        strategy_lines=[
            "把老街漫游、茶馆休息和轻量景点安排在一个连续片区内。",
            "不追求密集打卡，重点放在氛围感和在地生活体验。",
            "优先保留能够坐下来休息和观察城市日常的节点。",
        ],
        risk_lines=[
            "老街类区域周末客流较高，商业化强的片区可能削弱慢游体验。",
            "如果街区跨度较大，应提前控制步行量，避免后段疲劳。",
        ],
        copy_text="茶馆和老街更适合慢慢逛，路线设计的重点不在于多，而在于有停顿、有呼吸感。",
    ),
    ScenarioTemplate(
        filename="family_museum_halfday.md",
        title_suffix="家庭半日博物馆建议",
        category="family_halfday",
        tags=["family", "museum", "halfday", "indoor"],
        crowd_type=["family"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合时间有限的家庭半日游，重点是用一个主博物馆或科技馆配合一个轻量补充点完成完整体验。",
        strategy_lines=[
            "优先选一个互动性更强的主场馆作为核心。",
            "午餐或下午茶安排在馆区附近，避免高频移动。",
            "如孩子状态允许，再补一个轻量休闲点位作为收尾。",
        ],
        risk_lines=[
            "半日路线时间紧，主场馆排队会显著影响完成度。",
            "互动类展馆更适合预约和错峰，临时高峰容易造成等待。",
        ],
        copy_text="家庭半日行程关键不在于多，而在于用一个高质量主点把体验做完整、做轻松。",
    ),
    ScenarioTemplate(
        filename="slow_breakfast_city.md",
        title_suffix="早午节奏城市小游建议",
        category="slow_breakfast",
        tags=["slow_travel", "food", "morning", "citybreak"],
        crowd_type=["solo", "couple", "friends"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["walk", "public_transit"],
        scene_text="适合把旅途重心放在早午时段，从早餐、市场、街区和轻量景点慢慢展开的一类城市小游。",
        strategy_lines=[
            "从本地早餐或早市开始，把一天节奏拉慢。",
            "上午安排一个不需要排队太久的轻量主景点。",
            "中午后转入休息、咖啡或室内空间，避免整天过度拉满。",
        ],
        risk_lines=[
            "早餐型路线对时间要求较高，出发过晚会影响完整体验。",
            "部分早市和老店营业窗口较短，需要提前规划顺序。",
        ],
        copy_text="有些城市最迷人的时段不是夜晚，而是从早餐开始慢慢醒来的那几个小时。",
    ),
    ScenarioTemplate(
        filename="micro_holiday_2day.md",
        title_suffix="短假期两日微旅行建议",
        category="micro_holiday",
        tags=["holiday", "2day", "relaxed", "practical"],
        crowd_type=["solo", "couple", "friends", "family"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合小长假或普通双休日的两日微旅行，强调完成度高、切换少、性价比稳。",
        strategy_lines=[
            "第一天安排代表性较强的主线路，第二天安排补充和收尾。",
            "住宿尽量放在两个主片区的中间位置，减少两日之间移动成本。",
            "把返程前最后半天做轻一些，避免形成赶路压力。",
        ],
        risk_lines=[
            "短假期交通和热门点位波动更大，需要控制跨区次数。",
            "如果第一天安排过满，第二天体验通常会明显下降。",
        ],
        copy_text="短假期更适合做‘高完成度微旅行’，顺路、稳定、舒服，往往比密集打卡更有获得感。",
    ),
    ScenarioTemplate(
        filename="classic_landmark_day.md",
        title_suffix="经典地标一日串联建议",
        category="classic_landmark",
        tags=["classic", "landmark", "oneday", "practical"],
        crowd_type=["solo", "couple", "friends", "family"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["public_transit", "taxi"],
        scene_text="适合第一次到访某座城市，希望用一天建立最基础印象的用户，强调经典、顺路、稳妥。",
        strategy_lines=[
            "选择一到两个最具代表性的地标作为核心，不追求广撒网。",
            "把城市风貌、拍照点和基础吃饭安排进同一条主线。",
            "下午后段留一个机动补充点位，便于根据体力与天气调整。",
        ],
        risk_lines=[
            "经典地标通常也是最热门的点，节假日和周末需预留排队时间。",
            "第一次到访容易贪多，路线应刻意控制点位数量。",
        ],
        copy_text="经典地标路线的价值在于稳，它能帮助第一次到访的用户用最少折腾建立起这座城市的第一印象。",
    ),
    ScenarioTemplate(
        filename="park_market_leisure.md",
        title_suffix="公园与市集休闲串联",
        category="park_market",
        tags=["park", "market", "leisure", "local_life"],
        crowd_type=["solo", "family", "friends", "senior"],
        budget_level="medium",
        season=["spring", "summer", "autumn"],
        transportation=["walk", "public_transit"],
        scene_text="适合希望感受城市生活感的用户，把公园、集市、街区和轻松停留组合成一条日常化路线。",
        strategy_lines=[
            "以一个城市公园或公共开放空间作为主轴，连接附近生活型节点。",
            "把市场、街边小吃和休闲步行安排成短距离组合。",
            "优先选择不需要预约、不需要高额门票的开放式内容。",
        ],
        risk_lines=[
            "集市类内容对时间段较敏感，错过营业高峰会影响体验。",
            "如遇天气不稳定，开放式路线需要保留室内替代点。",
        ],
        copy_text="如果你想看见一座城市更接近日常的样子，公园和市集往往比热门景区更容易留下生活感。",
    ),
    ScenarioTemplate(
        filename="oldtown_photo_route.md",
        title_suffix="老城拍照漫步路线",
        category="oldtown_photo",
        tags=["oldtown", "photo_friendly", "citywalk", "couple"],
        crowd_type=["solo", "couple", "friends"],
        budget_level="medium",
        season=["spring", "autumn", "winter"],
        transportation=["walk", "public_transit"],
        scene_text="适合围绕老城肌理、建筑立面、巷道空间和街角光影展开的拍照型漫游路线。",
        strategy_lines=[
            "优先选择街巷密度高、建筑风格集中、步行友好的片区。",
            "把拍照点位和咖啡休息点组合，避免纯赶场式拍摄。",
            "把路线长度控制在轻松范围，保证拍照和慢逛都有余量。",
        ],
        risk_lines=[
            "拍照型路线更受光线和人流影响，时段选择很关键。",
            "老城部分区域道路狭窄，周末高峰会降低停留体验。",
        ],
        copy_text="老城拍照路线不需要很长，但需要光线、节奏和空间感都刚刚好，才能真正拍出城市气质。",
    ),
    ScenarioTemplate(
        filename="rail_hub_weekend.md",
        title_suffix="高铁到达周末快游建议",
        category="rail_weekend",
        tags=["high_speed_rail", "weekend", "practical", "citybreak"],
        crowd_type=["solo", "couple", "friends"],
        budget_level="medium",
        season=["spring", "summer", "autumn", "winter"],
        transportation=["high_speed_rail", "public_transit", "taxi"],
        scene_text="适合高铁到达后的周末快游场景，重点在于从站点出发的接驳效率、路线顺路性和时间利用率。",
        strategy_lines=[
            "优先围绕高铁站可快速接驳的主片区安排行程。",
            "第一天以核心线路为主，第二天偏轻量收尾，便于返程。",
            "住宿建议靠近核心动线中部，降低两天之间转移成本。",
        ],
        risk_lines=[
            "高铁往返时间窗口固定，最后半天不宜安排高不确定性内容。",
            "站点与景区距离较远时，需控制景点数量避免形成赶路感。",
        ],
        copy_text="高铁周末游最怕的是时间碎片化，所以路线越顺、接驳越稳，整体体验就越好。",
    ),
]


TOKEN_TRAITS = {
    "mountain": "山地景观",
    "danxia": "地貌景观",
    "river": "滨水风光",
    "lake": "湖泊休闲",
    "wetland": "湿地生态",
    "forest": "森林氧吧",
    "desert": "荒漠景观",
    "grassland": "草原视野",
    "history": "历史人文",
    "heritage": "历史人文",
    "museum": "博物馆体验",
    "food": "地方风味",
    "tea": "地方风味",
    "wine": "地方风味",
    "night": "夜间氛围",
    "citywalk": "城市漫游",
    "couple": "氛围体验",
    "family": "家庭友好",
    "senior": "轻量休闲",
}


def list_markdown_documents() -> list[Path]:
    docs: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if path.name.lower() == "readme.md" or path.name.startswith("_"):
            continue
        docs.append(path)
    return sorted(docs)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="ignore")


def parse_source(text: str) -> str:
    match = re.search(r"^source:\s*\"?([^\"\n]+)\"?\s*$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def collect_traits(names: Iterable[str]) -> list[str]:
    traits: list[str] = []
    seen: set[str] = set()
    for name in names:
        tokens = re.split(r"[_\-\s]+", Path(name).stem.lower())
        for token in tokens:
            trait = TOKEN_TRAITS.get(token)
            if trait and trait not in seen:
                seen.add(trait)
                traits.append(trait)
    return traits[:3]


def city_label(path: Path) -> str:
    raw = path.parent.name.replace("-", " ").replace("_", " ")
    return " ".join(part.capitalize() for part in raw.split()) or path.parent.name


def build_doc_text(path: Path, scenario: ScenarioTemplate, directory_names: list[str]) -> str:
    label = city_label(path)
    traits = collect_traits(directory_names)
    trait_text = "、".join(traits) if traits else "城市休闲、人文体验与顺路动线"
    place_lines = [
        f"- 可围绕当地更具代表性的 {traits[0] if traits else '核心景区'} 作为主点展开；",
        "- 如时间允许，可补充老街、博物馆、滨水公共空间或本地餐饮片区；",
        "- 需要把主要点位尽量压缩在同一片区或同一条公共交通轴线上。",
    ]

    frontmatter = [
        "---",
        f'title: "{label} {scenario.title_suffix}"',
        f'city: "{path.parent.name}"',
        f'category: "{scenario.category}"',
        f"tags: [{', '.join(scenario.tags)}]",
        f"crowd_type: [{', '.join(scenario.crowd_type)}]",
        f'budget_level: "{scenario.budget_level}"',
        f"season: [{', '.join(scenario.season)}]",
        f"transportation: [{', '.join(scenario.transportation)}]",
        f'summary: "面向 {path.parent.name} 的补充场景知识，强调 {trait_text} 下的可执行旅行组织方式。"',
        f'source: "{GENERATED_SOURCE}"',
        'updated_at: "2026-04-11"',
        "---",
        "",
        "## 场景描述",
        f"{scenario.scene_text} 结合该目的地已有知识，更强调 {trait_text} 的稳定组合。",
        "",
        "## 推荐策略",
        *scenario.strategy_lines,
        "",
        "## 可选地点",
        *place_lines,
        "",
        "## 约束与风险",
        *scenario.risk_lines,
        "",
        "## 推荐文案",
        scenario.copy_text,
        "",
    ]
    return "\n".join(frontmatter)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expand local knowledge base documents with generated scenario files.")
    parser.add_argument(
        "--target-total-multiple",
        type=int,
        default=2,
        help="Target total docs relative to original base docs. 2 means double the original corpus size.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.target_total_multiple < 2:
        raise ValueError("--target-total-multiple must be >= 2")

    all_docs = list_markdown_documents()
    base_docs_by_dir: dict[Path, list[Path]] = {}
    generated_count_by_dir: dict[Path, int] = {}
    existing_names_by_dir: dict[Path, set[str]] = {}

    for path in all_docs:
        text = read_text(path)
        source = parse_source(text)
        existing_names_by_dir.setdefault(path.parent, set()).add(path.name)
        if source == GENERATED_SOURCE:
            generated_count_by_dir[path.parent] = generated_count_by_dir.get(path.parent, 0) + 1
            continue
        base_docs_by_dir.setdefault(path.parent, []).append(path)

    created: list[Path] = []

    for directory, base_docs in sorted(base_docs_by_dir.items()):
        base_count = len(base_docs)
        target_generated_total = base_count * (args.target_total_multiple - 1)
        target_new_docs = max(0, target_generated_total - generated_count_by_dir.get(directory, 0))
        if target_new_docs == 0:
            continue

        existing_names = existing_names_by_dir.setdefault(directory, set())
        directory_names = sorted(existing_names)
        available = [scenario for scenario in SCENARIOS if scenario.filename not in existing_names]

        if len(available) < target_new_docs:
            raise RuntimeError(f"{directory} 可用场景模板不足，无法新增 {target_new_docs} 篇文档。")

        for scenario in available[:target_new_docs]:
            output_path = directory / scenario.filename
            output_path.write_text(build_doc_text(output_path, scenario, directory_names), encoding="utf-8")
            existing_names.add(scenario.filename)
            created.append(output_path)

    print(f"created_docs={len(created)}")
    for path in created[:20]:
        print(path)
    if len(created) > 20:
        print(f"... and {len(created) - 20} more")


if __name__ == "__main__":
    main()
