import os
import sys
import ctypes
import locale
import platform
import subprocess

# 获取系统语言
def get_system_language():
    """Get system language using a combination of methods."""

    os_name = platform.system()

    if os_name == 'Windows':
        try:
            # 使用windows api获取系统语言
            windll = ctypes.windll.kernel32 # type: ignore
            ui_lang = windll.GetUserDefaultUILanguage() 
            lang_code = locale.windows_locale[ui_lang] 
            if lang_code:
                lang = lang_code.split('_')[0]
                if lang.startswith('zh'):
                    return 'zh'
        except Exception:
            pass

    elif os_name == "Darwin":  # macOS
        try:
            # 使用macos api获取系统语言
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleLocale"],
                capture_output=True,
                text=True,
            )
            lang = result.stdout.strip().split("_")[0]
            if lang.startswith("zh"):
                return "zh"
        except Exception:
            pass
    
    elif os_name == 'Linux':
            # 检查Lang的环境变量
            lang = os.environ.get('LANG')
            if lang:
                lang = lang.split('.')[0]
                if lang.startswith('zh'):
                    return 'zh'
    
    # Fallback to using locale.getpreferredencoding()
    # 如果以上方法都失败，则使用locale.getpreferredencoding()获取系统语言
    encoding = locale.getpreferredencoding()
    if encoding.lower() in ("cp936", "gbk", "big5"):
        return "zh"
    
    return "en"

# 选取语言
def select_language():
    """Select language based on command line arguments or system language."""
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("zh", "en"):
        return sys.argv[1].lower()
    return get_system_language()