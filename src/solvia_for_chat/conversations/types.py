from typing import List, Dict, Callable, Optional, TypedDict, Awaitable, ClassVar
from dataclasses import dataclass, field
from pydantic import BaseModel

from ..agent.output_types import Actions, DisplayText


# Type definitions
# 发送消息
WebSocketSend = Callable[[str], Awaitable[None]]
# 广播消息
BroadcastFunc = Callable[[List[str], dict, Optional[str]], Awaitable[None]]
# 音频负载
class AudioPayload(TypedDict):
    """Type definition for audio payload"""

    type: str # 类型
    audio: Optional[str] # 音频
    volumes: Optional[List[float]] # 音量
    slice_length: Optional[int] # 切片长度
    display_text: Optional[DisplayText]
    actions: Optional[Actions]
    forwarded: Optional[bool]

# 广播上下文
@dataclass
class BroadcastContext:
    """Context for broadcasting messages in group chat"""

    broadcast_func: Optional[BroadcastFunc] = None
    group_members: Optional[List[str]] = None
    current_client_uid: Optional[str] = None

# 对话配置
class ConversationConfig(BaseModel):
    """Configuration for conversation chain"""

    conf_uid: str = ""
    history_uid: str = ""
    client_uid: str = ""
    character_name: str = "AI"

# 群组对话状态
@dataclass
class GroupConversationState:
    """State for group conversation"""

    # Class variable to track current states
    _states: ClassVar[Dict[str, "GroupConversationState"]] = {}

    group_id: str
    conversation_history: List[str] = field(default_factory=list)
    memory_index: Dict[str, int] = field(default_factory=dict)
    group_queue: List[str] = field(default_factory=list)
    session_emoji: str = ""
    current_speaker_uid: Optional[str] = None

    def __post_init__(self):
        """Register state instance after initialization"""
        GroupConversationState._states[self.group_id] = self

    @classmethod
    def get_state(cls, group_id: str) -> Optional["GroupConversationState"]:
        """Get conversation state by group_id"""
        return cls._states.get(group_id)

    @classmethod
    def remove_state(cls, group_id: str) -> None:
        """Remove conversation state when done"""
        cls._states.pop(group_id, None)

