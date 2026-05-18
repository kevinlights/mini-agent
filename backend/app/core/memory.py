# Memory System with JSONL Storage
# 记忆系统，使用 JSONL 存储

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import re
from datetime import datetime, timedelta


@dataclass
class MemoryEntry:
    """A single memory entry.
    单个记忆条目。
    """

    timestamp: float
    task_type: str
    importance: int  # 1-10 scale
    summary: str
    keywords: List[str]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        转换为字典表示。
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary representation.
        从字典表示创建。
        """
        return cls(**data)


class MemorySystem:
    """Memory system using JSONL storage with hybrid retrieval algorithms.
    使用 JSONL 存储的记忆系统，支持混合检索算法。
    """

    def __init__(self, storage_path: str = "memories.jsonl"):
        """Initialize memory system.
        初始化记忆系统。

        Args:
            storage_path: Path to JSONL file for storing memories.
                用于存储记忆的 JSONL 文件路径。
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save_memory(self, entry: MemoryEntry):
        """Save a memory entry to storage.
        保存记忆条目到存储。

        Args:
            entry: Memory entry to save.
                要保存的记忆条目。
        """
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def load_all_memories(self) -> List[MemoryEntry]:
        """Load all memories from storage.
        从存储加载所有记忆。

        Returns:
            List of all memory entries.
                所有记忆条目的列表。
        """
        if not self.storage_path.exists():
            return []

        memories = []
        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        memories.append(MemoryEntry.from_dict(data))
                    except json.JSONDecodeError:
                        continue  # Skip invalid lines

        return memories

    def get_recent_memories(
        self, minutes: int = 60, limit: int = 10
    ) -> List[MemoryEntry]:
        """Get recent memories within a time window.
        获取指定时间窗口内的近期记忆。

        Args:
            minutes: Time window in minutes.
                时间窗口（分钟）。
            limit: Maximum number of memories to return.
                返回的最大记忆数。

        Returns:
            List of recent memory entries.
                近期记忆条目列表。
        """
        cutoff_time = time.time() - (minutes * 60)
        all_memories = self.load_all_memories()
        recent = [
            mem for mem in all_memories if mem.timestamp >= cutoff_time
        ]
        # Sort by timestamp descending (most recent first)
        recent.sort(key=lambda x: x.timestamp, reverse=True)
        return recent[:limit]

    def search_by_keywords(
        self, keywords: List[str], limit: int = 10
    ) -> List[MemoryEntry]:
        """Search memories by keywords.
        按关键字搜索记忆。

        Args:
            keywords: Keywords to search for.
                要搜索的关键字。
            limit: Maximum number of memories to return.
                返回的最大记忆数。

        Returns:
            List of matching memory entries.
                匹配的记忆条目列表。
        """
        all_memories = self.load_all_memories()
        matches = []

        for memory in all_memories:
            # Score based on keyword matches in summary and keywords
            score = 0
            summary_lower = memory.summary.lower()
            keywords_lower = [kw.lower() for kw in memory.keywords]

            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Count matches in summary
                score += summary_lower.count(keyword_lower) * 2
                # Count matches in keywords
                score += sum(1 for kw in keywords_lower if keyword_lower in kw)

            if score > 0:
                matches.append((memory, score))

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches[:limit]]

    def search_by_task_type(
        self, task_type: str, limit: int = 10
    ) -> List[MemoryEntry]:
        """Search memories by task type.
        按任务类型搜索记忆。

        Args:
            task_type: Task type to search for.
                要搜索的任务类型。
            limit: Maximum number of memories to return.
                返回的最大记忆数。

        Returns:
            List of matching memory entries.
                匹配的记忆条目列表。
        """
        all_memories = self.load_all_memories()
        matches = [
            mem for mem in all_memories
            if task_type.lower() in mem.task_type.lower()
        ]
        # Sort by importance and timestamp
        matches.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        return matches[:limit]

    def search_by_importance(
        self, min_importance: int = 1, max_importance: int = 10, limit: int = 10
    ) -> List[MemoryEntry]:
        """Search memories by importance range.
        按重要性范围搜索记忆。

        Args:
            min_importance: Minimum importance level.
                最低重要性等级。
            max_importance: Maximum importance level.
                最高重要性等级。
            limit: Maximum number of memories to return.
                返回的最大记忆数。

        Returns:
            List of matching memory entries.
                匹配的记忆条目列表。
        """
        all_memories = self.load_all_memories()
        matches = [
            mem for mem in all_memories
            if min_importance <= mem.importance <= max_importance
        ]
        # Sort by importance and timestamp
        matches.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        return matches[:limit]

    def hybrid_search(
        self,
        query: str,
        task_types: Optional[List[str]] = None,
        importance_range: Tuple[int, int] = (1, 10),
        time_window_minutes: Optional[int] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Hybrid search combining multiple algorithms.
        混合搜索，结合多种算法。

        Args:
            query: Query string to search for.
                要搜索的查询字符串。
            task_types: Task types to filter by.
                要过滤的任务类型。
            importance_range: Range of importance levels to include.
                要包含的重要性等级范围。
            time_window_minutes: Time window in minutes (None for all time).
                时间窗口（分钟），None 表示所有时间。
            limit: Maximum number of memories to return.
                返回的最大记忆数。

        Returns:
            List of matching memory entries.
                匹配的记忆条目列表。
        """
        all_memories = self.load_all_memories()

        # Apply filters first
        filtered = []
        for memory in all_memories:
            # Check time window
            if time_window_minutes:
                cutoff = time.time() - (time_window_minutes * 60)
                if memory.timestamp < cutoff:
                    continue

            # Check task types
            if task_types:
                if memory.task_type.lower() not in [t.lower() for t in task_types]:
                    continue

            # Check importance range
            min_imp, max_imp = importance_range
            if not (min_imp <= memory.importance <= max_imp):
                continue

            filtered.append(memory)

        # Calculate scores for remaining memories
        scored_memories = []
        query_lower = query.lower()
        query_words = re.findall(r'\b\w+\b', query_lower)

        for memory in filtered:
            score = 0

            # Keyword matching in summary
            summary_lower = memory.summary.lower()
            for word in query_words:
                score += summary_lower.count(word) * 2

            # Keyword matching in memory keywords
            for kw in memory.keywords:
                kw_lower = kw.lower()
                for word in query_words:
                    if word in kw_lower:
                        score += 1

            # Boost by importance
            score *= memory.importance

            # Boost by recency (if within 24 hours)
            age_hours = (time.time() - memory.timestamp) / 3600
            if age_hours < 24:
                score *= (1 + (24 - age_hours) / 24)  # Up to 2x boost

            if score > 0:
                scored_memories.append((memory, score))

        # Sort by score descending
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [mem[0] for mem in scored_memories[:limit]]

    def summarize_and_save(
        self,
        task_type: str,
        importance: int,
        summary: str,
        keywords: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Summarize and save a task memory.
        总结并保存任务记忆。

        Args:
            task_type: Type of task.
                任务类型。
            importance: Importance level (1-10).
                重要性等级（1-10）。
            summary: Task summary.
                任务摘要。
            keywords: Keywords for the task.
                任务的关键字。
            metadata: Additional metadata.
                附加元数据。
        """
        entry = MemoryEntry(
            timestamp=time.time(),
            task_type=task_type,
            importance=importance,
            summary=summary,
            keywords=keywords,
            metadata=metadata
        )
        self.save_memory(entry)

    def get_memory_context(
        self,
        current_query: str,
        max_memories: int = 5
    ) -> str:
        """Get memory context for a query.
        获取查询的记忆上下文。

        Args:
            current_query: Current query to get context for.
                当前查询。
            max_memories: Maximum number of memories to include.
                包含的最大记忆数。

        Returns:
            Formatted context string with relevant memories.
                包含相关记忆的格式化上下文字符串。
        """
        # Get relevant memories using hybrid search
        relevant_memories = self.hybrid_search(
            query=current_query,
            limit=max_memories
        )

        if not relevant_memories:
            return "No relevant memories found."

        context_parts = ["Relevant Memories:"]
        for i, memory in enumerate(relevant_memories, 1):
            timestamp = datetime.fromtimestamp(memory.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            context_parts.append(
                f"{i}. [{timestamp}] {memory.task_type} (Importance: {memory.importance}/10)\n"
                f"   Summary: {memory.summary}\n"
                f"   Keywords: {', '.join(memory.keywords)}"
            )

        return "\n".join(context_parts)
