"""
工具函数模块 - 包含多个边界条件复杂的函数，用于 prog_05 单元测试生成任务
"""
from typing import List, Optional


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将数值限制在 [min_val, max_val] 范围内"""
    if min_val > max_val:
        raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val})")
    return max(min_val, min(value, max_val))


def chunk_list(lst: list, size: int) -> List[list]:
    """将列表按 size 分块，最后一块可能不足 size"""
    if size <= 0:
        raise ValueError("size must be positive")
    if not lst:
        return []
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def safe_divide(a: float, b: float, default: Optional[float] = None) -> Optional[float]:
    """除法，除数为零时返回 default（默认 None）"""
    if b == 0:
        return default
    return a / b


def flatten(nested: list) -> list:
    """展平一层嵌套列表（只展平一层，不递归）"""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def truncate_string(s: str, max_len: int, ellipsis: str = "...") -> str:
    """截断字符串，超长时末尾附加 ellipsis"""
    if max_len < len(ellipsis):
        raise ValueError("max_len must be >= len(ellipsis)")
    if len(s) <= max_len:
        return s
    return s[:max_len - len(ellipsis)] + ellipsis


def count_words(text: str) -> dict:
    """统计文本中每个词出现次数（忽略大小写，忽略空字符串）"""
    if not text or not text.strip():
        return {}
    words = text.lower().split()
    result = {}
    for w in words:
        result[w] = result.get(w, 0) + 1
    return result
