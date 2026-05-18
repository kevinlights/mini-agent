# Memory System Tests
# 记忆系统测试

import pytest
import time
import json
import os
from pathlib import Path
import tempfile

from app.core.memory import MemorySystem, MemoryEntry


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass.
    MemoryEntry 数据类的测试。
    """

    def test_create_entry(self):
        """Test creating a memory entry.
        测试创建记忆条目。
        """
        entry = MemoryEntry(
            timestamp=time.time(),
            task_type="test",
            importance=8,
            summary="Test summary",
            keywords=["test", "example"]
        )
        assert entry.task_type == "test"
        assert entry.importance == 8
        assert entry.summary == "Test summary"
        assert entry.keywords == ["test", "example"]

    def test_to_dict(self):
        """Test converting entry to dictionary.
        测试将条目转换为字典。
        """
        entry = MemoryEntry(
            timestamp=1234567890.0,
            task_type="test",
            importance=5,
            summary="Test",
            keywords=["test"]
        )
        d = entry.to_dict()
        assert d["timestamp"] == 1234567890.0
        assert d["task_type"] == "test"
        assert d["summary"] == "Test"

    def test_from_dict(self):
        """Test creating entry from dictionary.
        测试从字典创建条目。
        """
        data = {
            "timestamp": 1234567890.0,
            "task_type": "test",
            "importance": 5,
            "summary": "Test",
            "keywords": ["test"]
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.timestamp == 1234567890.0
        assert entry.task_type == "test"


class TestMemorySystem:
    """Tests for MemorySystem class.
    MemorySystem 类的测试。
    """

    def setup_method(self):
        """Setup test environment.
        设置测试环境。
        """
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        self.temp_file.close()
        self.memory_system = MemorySystem(storage_path=self.temp_file.name)

    def teardown_method(self):
        """Clean up test environment.
        清理测试环境。
        """
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_save_memory(self):
        """Test saving a memory entry.
        测试保存记忆条目。
        """
        entry = MemoryEntry(
            timestamp=time.time(),
            task_type="test",
            importance=8,
            summary="Test summary",
            keywords=["test"]
        )
        self.memory_system.save_memory(entry)

        # Check file exists and has content
        assert os.path.exists(self.temp_file.name)
        with open(self.temp_file.name, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["summary"] == "Test summary"

    def test_load_all_memories(self):
        """Test loading all memories.
        测试加载所有记忆。
        """
        # Save multiple entries
        for i in range(3):
            entry = MemoryEntry(
                timestamp=time.time() - i * 3600,
                task_type="test",
                importance=8 - i,
                summary=f"Test {i}",
                keywords=[f"test{i}"]
            )
            self.memory_system.save_memory(entry)

        memories = self.memory_system.load_all_memories()
        assert len(memories) == 3

    def test_load_all_memories_empty(self):
        """Test loading from non-existent file.
        测试从不存在文件加载。
        """
        empty_system = MemorySystem(storage_path="/tmp/nonexistent.jsonl")
        assert empty_system.load_all_memories() == []

    def test_get_recent_memories(self):
        """Test getting recent memories.
        测试获取近期记忆。
        """
        # Save recent and old entries
        recent_entry = MemoryEntry(
            timestamp=time.time() - 1800,  # 30 minutes ago
            task_type="test",
            importance=8,
            summary="Recent",
            keywords=["recent"]
        )
        old_entry = MemoryEntry(
            timestamp=time.time() - 7200,  # 2 hours ago
            task_type="test",
            importance=8,
            summary="Old",
            keywords=["old"]
        )
        self.memory_system.save_memory(recent_entry)
        self.memory_system.save_memory(old_entry)

        recent = self.memory_system.get_recent_memories(minutes=60)
        assert len(recent) == 1
        assert recent[0].summary == "Recent"

    def test_search_by_keywords(self):
        """Test searching by keywords.
        测试按关键字搜索。
        """
        entry1 = MemoryEntry(
            timestamp=time.time(),
            task_type="coding",
            importance=8,
            summary="Implemented tool calling feature",
            keywords=["tool", "calling", "feature"]
        )
        entry2 = MemoryEntry(
            timestamp=time.time(),
            task_type="coding",
            importance=5,
            summary="Fixed bug in agent",
            keywords=["bug", "agent"]
        )
        self.memory_system.save_memory(entry1)
        self.memory_system.save_memory(entry2)

        results = self.memory_system.search_by_keywords(["tool", "calling"])
        assert len(results) == 1
        assert results[0].summary == "Implemented tool calling feature"

    def test_search_by_task_type(self):
        """Test searching by task type.
        测试按任务类型搜索。
        """
        entry1 = MemoryEntry(
            timestamp=time.time(),
            task_type="coding",
            importance=8,
            summary="Code task",
            keywords=["code"]
        )
        entry2 = MemoryEntry(
            timestamp=time.time(),
            task_type="debugging",
            importance=5,
            summary="Debug task",
            keywords=["debug"]
        )
        self.memory_system.save_memory(entry1)
        self.memory_system.save_memory(entry2)

        results = self.memory_system.search_by_task_type("coding")
        assert len(results) == 1
        assert results[0].task_type == "coding"

    def test_search_by_importance(self):
        """Test searching by importance range.
        测试按重要性范围搜索。
        """
        entry1 = MemoryEntry(
            timestamp=time.time(),
            task_type="test",
            importance=9,
            summary="High importance",
            keywords=["high"]
        )
        entry2 = MemoryEntry(
            timestamp=time.time(),
            task_type="test",
            importance=3,
            summary="Low importance",
            keywords=["low"]
        )
        self.memory_system.save_memory(entry1)
        self.memory_system.save_memory(entry2)

        results = self.memory_system.search_by_importance(min_importance=7, max_importance=10)
        assert len(results) == 1
        assert results[0].importance == 9

    def test_summarize_and_save(self):
        """Test summarizing and saving.
        测试总结并保存。
        """
        self.memory_system.summarize_and_save(
            task_type="test",
            importance=8,
            summary="Test summary",
            keywords=["test", "summary"]
        )

        memories = self.memory_system.load_all_memories()
        assert len(memories) == 1
        assert memories[0].summary == "Test summary"

    def test_get_memory_context(self):
        """Test getting memory context.
        测试获取记忆上下文。
        """
        entry = MemoryEntry(
            timestamp=time.time(),
            task_type="coding",
            importance=8,
            summary="Implemented tool calling",
            keywords=["tool", "calling"]
        )
        self.memory_system.save_memory(entry)

        context = self.memory_system.get_memory_context("tool calling implementation")
        assert "Relevant Memories:" in context
        assert "Implemented tool calling" in context

    def test_get_memory_context_no_memories(self):
        """Test getting context with no memories.
        测试无记忆时获取上下文。
        """
        context = self.memory_system.get_memory_context("anything")
        assert context == "No relevant memories found."


class TestHybridSearch:
    """Tests for hybrid search functionality.
    混合搜索功能的测试。
    """

    def setup_method(self):
        """Setup test environment.
        设置测试环境。
        """
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        self.temp_file.close()
        self.memory_system = MemorySystem(storage_path=self.temp_file.name)

        # Add test memories
        self.memory_system.summarize_and_save(
            task_type="coding",
            importance=8,
            summary="Implemented tool calling with error handling",
            keywords=["tool", "calling", "error", "handling"]
        )
        self.memory_system.summarize_and_save(
            task_type="debugging",
            importance=5,
            summary="Fixed agent memory leak",
            keywords=["agent", "memory", "leak"]
        )
        self.memory_system.summarize_and_save(
            task_type="coding",
            importance=9,
            summary="Added skill support to agent framework",
            keywords=["skill", "agent", "framework"]
        )

    def teardown_method(self):
        """Clean up test environment.
        清理测试环境。
        """
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_hybrid_search_basic(self):
        """Test basic hybrid search.
        测试基本混合搜索。
        """
        results = self.memory_system.hybrid_search("tool calling")
        assert len(results) > 0
        assert results[0].summary == "Implemented tool calling with error handling"

    def test_hybrid_search_with_task_type_filter(self):
        """Test hybrid search with task type filter.
        测试带任务类型过滤的混合搜索。
        """
        results = self.memory_system.hybrid_search(
            "agent",
            task_types=["coding"]
        )
        assert len(results) > 0
        assert all(r.task_type == "coding" for r in results)

    def test_hybrid_search_with_importance_filter(self):
        """Test hybrid search with importance filter.
        测试带重要性过滤的混合搜索。
        """
        results = self.memory_system.hybrid_search(
            "agent",
            importance_range=(7, 10)
        )
        assert len(results) > 0
        assert all(r.importance >= 7 for r in results)

    def test_hybrid_search_with_time_window(self):
        """Test hybrid search with time window.
        测试带时间窗口的混合搜索。
        """
        results = self.memory_system.hybrid_search(
            "agent",
            time_window_minutes=120  # 2 hours
        )
        assert len(results) > 0

    def test_hybrid_search_scoring(self):
        """Test that hybrid search scores correctly.
        测试混合搜索评分正确性。
        """
        results = self.memory_system.hybrid_search("tool calling")
        assert len(results) >= 1
        # Most relevant should be first
        assert "tool calling" in results[0].summary.lower()
