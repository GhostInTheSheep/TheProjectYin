from pydantic import BaseModel, model_validator
from src.solvia_for_chat.config_manager.i18n import I18nMixin

class 角色(BaseModel):
    名字: str
    等级: int
    血量: int
    武器: str
    
    @model_validator(mode="before")  # 进入战斗前的准备阶段
    @classmethod
    def 战斗准备(cls, 角色数据):
        print("🛡️ 战斗准备阶段：", 角色数据)
        # 检查并准备装备
        if isinstance(角色数据, dict):
            if '武器' in 角色数据 and 角色数据['武器'] == '木剑':
                角色数据['武器'] = '铁剑'  # 升级武器
                print("⚔️ 武器升级：木剑 → 铁剑")
        return 角色数据
    
    @model_validator(mode="after")   # 战斗结束后的检查阶段
    def 战斗检查(self):
        print("🎯 战斗检查阶段：", self)
        # 检查角色状态是否合理
        if self.等级 < 10 and self.血量 > 1000:
            raise ValueError("❌ 等级太低，血量不可能这么高！")
        if self.武器 == '木剑' and self.等级 > 50:
            raise ValueError("❌ 等级这么高还用木剑？该换武器了！")
        return self

# 创建角色
print("=== 创建新手角色 ===")
新手 = 角色(名字="褪色者", 等级=5, 血量=500, 武器="木剑")

print("\n=== 创建高级角色 ===")
高级 = 角色(名字="艾尔登之王", 等级=60, 血量=2000, 武器="月光大剑")


