from loguru import logger
from upgrade_codes.upgrade_core.language import select_language
from upgrade_codes.config_sync import ConfigSynchronizer
from upgrade_codes.upgrade_core.upgrade_utils import UpgradeUtility
import os
from datetime import datetime
import sys
from upgrade_codes.upgrade_core.constants import USER_CONF,TEXTS


# 升级管理器
class UpgradeManager:
    def __init__(self):
        self.lang = select_language()  # 选择语言
        self._configure_logger()  # 配置日志
        self.logger = logger  # 日志
        self.upgrade_utils = UpgradeUtility(self.logger, self.lang)  # 升级工具
        self.config_sync = ConfigSynchronizer(self.lang, self.logger)  # 配置同步
        self.texts = TEXTS  # 文本
   
    #检查用户配置文件是否存在
    def check_user_config_exists(self):
        if not os.path.exists(USER_CONF):
            print(self.texts[self.lang]["no_config_fatal"])
            exit(1)

    #配置日志
    def _configure_logger(self):
        logger.remove()
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(
            log_dir, f"upgrade_{datetime.now().strftime('%Y-%m-%d-%H-%M')}.log"
        )

        logger.add(
            sys.stdout,
            level="DEBUG",
            colorize=True,
            format="<green>[{level}]</green> <level>{message}</level>",
        )
        logger.add(
            log_file,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )

    #同步用户配置
    def sync_user_config(self):
        self.config_sync.sync_user_config()

    #更新用户配置
    def update_user_config(self):
        self.config_sync.update_user_config()

    #记录系统信息
    def log_system_info(self):
        return self.upgrade_utils.log_system_info()

    #检查git是否安装
    def check_git_installed(self):
        return self.upgrade_utils.check_git_installed()

    #运行命令
    def run_command(self, command):
        return self.upgrade_utils.run_command(command)

    #记录操作时间
    def time_operation(self, func, *args, **kwargs):
        return self.upgrade_utils.time_operation(func, *args, **kwargs)

    #获取子模块列表
    def get_submodule_list(self):
        return self.upgrade_utils.get_submodule_list()

    #检查是否存在子模块
    def has_submodules(self):
        return self.upgrade_utils.has_submodules()
