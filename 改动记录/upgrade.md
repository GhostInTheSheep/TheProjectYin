# i18n
             ┌─────────────────────────────┐
             │      MultiLingualString     │
             │   en: str                   │
             │   zh: str                   │
             │ ┌───────────────────────┐   │
             │ │ get(lang_code: str)   │   │→ 返回指定语言内容
             │ └───────────────────────┘   │
             └───────────▲─────────────────┘
                         │
             ┌───────────┴───────────────┐
             │        Description        │
             │ ┌───────────────────────┐ │
             │ │ notes: MultiLingual...│ │← 备注（可选）
             │ └───────────────────────┘ │
             │ + get_text(lang)          │→ 获取主描述
             │ + get_notes(lang)         │→ 获取备注
             │ + from_str(...)           │→ 快速构造实例
             └───────────▲───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │         I18nMixin (mixin)     │
         │  model_config = ConfigDict... │
         │  DESCRIPTIONS: Dict[str, ...] │← 字段说明注册表
         │                               │
         │ + get_field_description()     │← 获取字段说明
         │ + get_field_notes()           │← 获取字段备注
         │ + get_field_options()         │← 获取字段选项（预留）
         └───────────────────────────────┘



