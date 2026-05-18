# Logging Configuration with Colored Output
# 带彩色输出的日志配置

import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels.
    自定义格式化器，为日志级别添加颜色。
    """

    # ANSI color codes
    # ANSI 颜色代码
    COLORS = {
        "DEBUG": "\033[90m",      # Light gray / 浅灰色
        "INFO": "\033[32m",       # Green / 绿色
        "WARNING": "\033[33m",    # Yellow / 黄色
        "ERROR": "\033[31m",      # Red / 红色
        "CRITICAL": "\033[35m",   # Magenta / 品红色
    }
    RESET = "\033[0m"

    def format(self, record):
        """Format the log record with colors.
        格式化带颜色的日志记录。

        Args:
            record: Log record.
                日志记录。

        Returns:
            Formatted log message with colors.
            带颜色的格式化日志消息。
        """
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            record.msg = f"{self.COLORS[levelname]}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "mini-agent",
    level: int = logging.DEBUG,
    use_colors: bool = True
) -> logging.Logger:
    """Setup logger with colored output.
    设置带彩色输出的日志记录器。

    Args:
        name: Logger name.
            日志记录器名称。
        level: Logging level.
            日志级别。
        use_colors: Whether to use colored output.
            是否使用彩色输出。

    Returns:
        Configured logger instance.
            配置好的日志记录器实例。
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if use_colors:
        formatter = ColoredFormatter(
            # "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Default logger instance
# 默认日志记录器实例
logger = setup_logger()
