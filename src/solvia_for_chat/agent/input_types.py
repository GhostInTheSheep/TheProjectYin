from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any


# 图片来源
class ImageSource(Enum):
    """Enum for different image sources"""

    CAMERA = "camera"
    SCREEN = "screen"
    CLIPBOARD = "clipboard"
    UPLOAD = "upload"

# 文本来源
class TextSource(Enum):
    """Enum for different text sources"""

    INPUT = "input"  # Main user input/transcription
    CLIPBOARD = "clipboard"  # Text from clipboard
    
# 图片数据
@dataclass
class ImageData:
    """
    Represents an image from various sources

    Attributes:
        source: Source of the image
        data: Base64 encoded image data or URL
        mime_type: MIME type of the image (e.g., 'image/jpeg', 'image/png')
    """

    source: ImageSource
    data: str  # Base64 encoded or URL
    mime_type: str

# 文件数据
@dataclass
class FileData:
    """
    Represents a file uploaded by the user

    Attributes:
        name: Original filename
        data: Base64 encoded file data
        mime_type: MIME type of the file
    """

    name: str
    data: str  # Base64 encoded
    mime_type: str


# 文本数据
@dataclass
class TextData:
    """
    Represents text data from various sources

    Attributes:
        source: Source of the text
        content: str - The text content
        from_name: Optional[str] - Name of the sender/character
    """

    source: TextSource
    content: str
    from_name: Optional[str] = None


class BaseInput:
    """Base class for all input types"""

    pass

# 批量输入
@dataclass
class BatchInput(BaseInput):
    """
    Input type for batch processing, containing complete transcription and optional media

    Attributes:
        texts: List of text data from different sources
        images: Optional list of images
        files: Optional list of files
        metadata: Optional dictionary of metadata flags for special inputs
            - 'proactive_speak': Boolean flag indicating if this is a proactive speak input
            - 'skip_memory': Boolean flag indicating if this input should be skipped in AI's internal memory
            - 'skip_history': Boolean flag indicating if this input should be skipped in local history storage
    """

    texts: List[TextData]
    images: Optional[List[ImageData]] = None
    files: Optional[List[FileData]] = None
    metadata: Optional[Dict[str, Any]] = None
