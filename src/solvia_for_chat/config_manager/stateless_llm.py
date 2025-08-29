# config_manager/stateless_llm.py
from typing import ClassVar, Literal
from pydantic import BaseModel, Field
from .i18n import I18nMixin, Description

# ==========  Base configuration for stateless LLM ==========
class StatelessLLMBaseConfig(I18nMixin):
    """Base configuration for StatelessLLM."""

    # interrupt_method. If the provider supports inserting system prompt anywhere in the chat memory, use "system". Otherwise, use "user".
    interrupt_method: Literal["system", "user"] = Field(
        "user", alias="interrupt_method"
    )
    DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        "interrupt_method": Description(
            en="""The method to use for prompting the interruption signal.
            If the provider supports inserting system prompt anywhere in the chat memory, use "system". 
            Otherwise, use "user". You don't need to change this setting.""",
            zh="""用于表示中断信号的方法(提示词模式)。如果LLM支持在聊天记忆中的任何位置插入系统提示词，请使用“system”。
            否则，请使用“user”。""",
        ),
    }

# 无状态LLM配置，模板
class StatelessLLMWithTemplate(StatelessLLMBaseConfig):
    """Configuration for OpenAI-compatible LLM providers."""

    base_url: str = Field(..., alias="base_url") # 基础URL
    llm_api_key: str = Field(..., alias="llm_api_key") # LLM API密钥
    model: str = Field(..., alias="model") # 模型名称  例如 gpt-4, claude-3-sonnet 等
    organization_id: str | None = Field(..., alias="organization_id") # 组织ID 某些API提供商需要此字段
    project_id: str | None = Field(..., alias="project_id") # 项目ID 某些API提供商需要此字段
    template: str | None = Field(None, alias="template") # 模板 用于自定义提示词模板
    temperature: float = Field(1.0, alias="temperature") # 温度 (默认值: 1.0) 采样温度，控制输出的随机性 范围：0-2，值越高越随机

    _OPENAI_COMPATIBLE_DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        "base_url": Description(en="The base URL of the LLM provider.", zh="LLM提供者的基础URL。"),
        "llm_api_key": Description(en="The API key of the LLM provider.", zh="LLM提供者的API密钥。"),
        "model": Description(en="The model name of the LLM provider.", zh="LLM提供者的模型名称。"),
        "organization_id": Description(en="The organization ID of the LLM provider.", zh="LLM提供者的组织ID(可选，一些API提供商需要此字段)。"),
        "project_id": Description(en="The project ID of the LLM provider.", zh="LLM提供者的项目ID（可选，一些API提供商需要此字段。"),
        "template": Description(en="The template of the LLM provider.", zh="LLM提供者的模板。"),
        "temperature": Description(en="The temperature of the LLM provider.", zh="使用的采样温度，介于 0 和 2 之间"),
    }
    
    # 合并描述
    DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        **StatelessLLMBaseConfig.DESCRIPTIONS,
        **_OPENAI_COMPATIBLE_DESCRIPTIONS,
    }

    

# 标准OpenAI兼容
class OpenAICompatibleConfig(StatelessLLMBaseConfig):
    """Configuration for OpenAI-compatible LLM providers."""

    base_url: str = Field(..., alias="base_url")
    llm_api_key: str = Field(..., alias="llm_api_key")
    model: str = Field(..., alias="model")
    organization_id: str | None = Field(None, alias="organization_id")
    project_id: str | None = Field(None, alias="project_id")
    temperature: float = Field(1.0, alias="temperature")

    _OPENAI_COMPATIBLE_DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        "base_url": Description(en="The base URL of the LLM provider.", zh="LLM提供者的基础URL。"),
        "llm_api_key": Description(en="The API key of the LLM provider.", zh="LLM提供者的API密钥。"),
        "model": Description(en="The model name of the LLM provider.", zh="LLM提供者的模型名称。"),
        "organization_id": Description(en="The organization ID of the LLM provider.", zh="LLM提供者的组织ID(可选，一些API提供商需要此字段)。"),
        "project_id": Description(en="The project ID of the LLM provider.", zh="LLM提供者的项目ID（可选，一些API提供商需要此字段。"),
        "temperature": Description(en="What sampling temperature to use, between 0 and 2.", zh="使用的采样温度，介于 0 和 2 之间"),
    }

    DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        **StatelessLLMBaseConfig.DESCRIPTIONS,
        **_OPENAI_COMPATIBLE_DESCRIPTIONS,
    }
 
# ollama 配置方式 (本地部署)
class OllamaConfig(OpenAICompatibleConfig):
    """Configuration for Ollama API."""

    llm_api_key: str = Field(..., alias="llm_api_key")
    keep_alive: float = Field(-1, alias="keep_alive")
    upload_at_exit: bool = Field(False, alias="upload_at_exit")
    interrupt_method: Literal["system", "user"] = Field(
        "system", alias="interrupt_method"
    )

    # Ollama-specific descriptions
    _OLLAMA_DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        "llm_api_key": Description(
            en="API key for authentication (defaults to 'default_api_key' for Ollama)", 
            zh="API 认证密钥 (Ollama 默认为 'default_api_key')"
        ),
        "keep_alive": Description(
            en="The keep alive time of the LLM provider.", 
            zh="LLM提供者的保持连接时间。"
        ),
        "upload_at_exit": Description(
            en="Unload the model when the program exits.", 
            zh="是否在程序退出时卸载模型。"
        ),
        
    }

    # 合并描述
    DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        **OpenAICompatibleConfig.DESCRIPTIONS,
        **_OLLAMA_DESCRIPTIONS,
    }

# OpenAI 的配置方式  （ 云端部署）
class OpenAIConfig(OpenAICompatibleConfig):
    """Configuration for Official OpenAI API."""

    base_url: str = Field("https://api.openai.com/v1", alias="base_url")
    interrupt_method: Literal["system", "user"] = Field(
        "system", alias="interrupt_method"
    )

# LM Studio 配置方式 （本地部署）
class LmStudioConfig(OpenAICompatibleConfig):
    """Configuration for LM Studio API."""

    # LM Studio-specific fields
    llm_api_key: str = Field("default_api_key", alias="llm_api_key") # 默认API密钥
    base_url: str = Field("http://localhost:11434", alias="base_url") 
    interrupt_method: Literal["system", "user"] = Field(
        "system", alias="interrupt_method"
        )
    
# LlamaCppConfig 配置方式 （本地部署）
class LlamaCppConfig(StatelessLLMBaseConfig):
    """Configuration for LlamaCpp."""

    model_path: str = Field(..., alias="model_path")
    interrupt_method: Literal["system", "user"] = Field(
        "system", alias="interrupt_method"
    )

    _LLAMACPP_DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        "model_path": Description(en="The path to the model file.", zh="模型文件的路径。"),
    }
    
    DESCRIPTIONS: ClassVar[dict[str, Description]] = {
        **StatelessLLMBaseConfig.DESCRIPTIONS,
        **_LLAMACPP_DESCRIPTIONS,
    }


# 无状态LLM配置池
class StatelessLLMConfigs(I18nMixin):
    """Pool of LLM provider configurations.
    This class contains configurations for different LLM providers."""
    
    # 无状态LLM配置模板
    stateless_llm_with_template: StatelessLLMWithTemplate | None = Field(
        None, alias="stateless_llm_with_template"
    )
    # openai 兼容配置方式
    openai_compatible_llm: OpenAICompatibleConfig | None = Field(
        None, alias="openai_compatible_llm"
    )
    # llamaCpp配置方式
    llama_cpp_llm: LlamaCppConfig | None = Field(
        None, alias="llama_cpp_llm"
    )
    # ollama配置方式
    ollama_llm: OllamaConfig | None = Field(
        None, alias="ollama_llm"
    )
    # lm studio配置方式
    lmstudio_llm: LmStudioConfig | None = Field(None, alias="lmstudio_llm")
    # openai 配置方式
    openai_llm: OpenAIConfig | None = Field(None, alias="openai_llm")
    

    # 配置池描述
    DESCRIPTIONS: ClassVar[dict[str, Description]] = {
       "stateless_llm_with_template": Description(en="The configuration for the stateless LLM with template.", zh="无状态LLM配置模板。"),
       "openai_compatible_llm": Description(en="The configuration for the OpenAI compatible LLM.", zh="OpenAI兼容LLM配置。"),
       "llama_cpp_llm": Description(en="The configuration for the LlamaCpp LLM.", zh="LlamaCpp LLM配置。"),
       "ollama_llm": Description(en="The configuration for the Ollama LLM.", zh="Ollama LLM配置。"),
       "lmstudio_llm": Description(en="The configuration for the LM Studio LLM.", zh="LM Studio LLM配置。"),
       "openai_llm": Description(en="The configuration for the OpenAI LLM.", zh="OpenAI LLM配置。"),
    }