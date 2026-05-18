# Tests for Skill Framework
# 技能框架测试

import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from app.skills.skill import (
    BaseSkill,
    MarkdownSkill,
    SkillRegistry,
    SkillMetadata,
    SkillContent,
)


class TestMarkdownSkill:
    """Tests for MarkdownSkill class.
    MarkdownSkill 类的测试。
    """

    def setup_method(self):
        self.sample_content = """# Introduction
This is a sample skill.

## Usage
How to use this skill.

## Examples
Some examples here.
"""
        self.skill = MarkdownSkill(
            name="Test Skill",
            description="A test skill for unit testing.",
            summary="Short summary",
            content=self.sample_content,
            category="test",
            tags=["test", "example"],
        )

    def test_init(self):
        """Test MarkdownSkill initialization.
        测试 MarkdownSkill 初始化。
        """
        assert self.skill.name == "Test Skill"
        assert self.skill.description == "A test skill for unit testing."
        assert self.skill.summary == "Short summary"
        assert self.skill.category == "test"
        assert self.skill.tags == ["test", "example"]

    def test_parse_sections(self):
        """Test section parsing.
        测试部分解析。
        """
        sections = self.skill.sections
        assert "introduction" in sections
        assert "usage" in sections
        assert "examples" in sections
        assert "This is a sample skill." in sections["introduction"]
        assert "How to use this skill." in sections["usage"]

    def test_parse_sections_no_headings(self):
        """Test parsing content without headings.
        测试解析没有标题的内容。
        """
        skill = MarkdownSkill(
            name="No Headings",
            description="No headings skill",
            summary="Summary",
            content="Just plain text content.",
        )
        assert "content" in skill.sections
        assert skill.sections["content"] == "Just plain text content."

    @pytest.mark.asyncio
    async def test_execute_full_content(self):
        """Test execute returns full content.
        测试执行返回完整内容。
        """
        result = await self.skill.execute()
        assert "# Introduction" in result
        assert "## Usage" in result

    @pytest.mark.asyncio
    async def test_execute_specific_section(self):
        """Test execute returns specific section.
        测试执行返回特定部分。
        """
        result = await self.skill.execute(section="usage")
        assert "How to use this skill." in result

    @pytest.mark.asyncio
    async def test_execute_nonexistent_section(self):
        """Test execute with nonexistent section returns full content.
        测试执行不存在部分时返回完整内容。
        """
        result = await self.skill.execute(section="nonexistent")
        assert result == self.sample_content


class TestSkillRegistry:
    """Tests for SkillRegistry class.
    SkillRegistry 类的测试。
    """

    def setup_method(self):
        self.registry = SkillRegistry()
        self.skill1 = MarkdownSkill(
            name="Skill One",
            description="First skill description.",
            summary="First skill summary",
            content="# Content\nFirst skill content.",
        )
        self.skill2 = MarkdownSkill(
            name="Skill Two",
            description="Second skill description.",
            summary="Second skill summary",
            content="# Content\nSecond skill content.",
        )

    def test_register(self):
        """Test registering a skill.
        测试注册技能。
        """
        self.registry.register(self.skill1)
        assert self.registry.get_skill("Skill One") is self.skill1

    def test_unregister(self):
        """Test unregistering a skill.
        测试注销技能。
        """
        self.registry.register(self.skill1)
        self.registry.unregister("Skill One")
        assert self.registry.get_skill("Skill One") is None

    def test_unregister_nonexistent(self):
        """Test unregistering nonexistent skill.
        测试注销不存在的技能。
        """
        self.registry.unregister("Nonexistent")  # Should not raise

    def test_get_skill(self):
        """Test getting a skill.
        测试获取技能。
        """
        self.registry.register(self.skill1)
        assert self.registry.get_skill("Skill One") is self.skill1
        assert self.registry.get_skill("Nonexistent") is None

    def test_list_skills(self):
        """Test listing skills.
        测试列出技能。
        """
        self.registry.register(self.skill1)
        self.registry.register(self.skill2)
        skills = self.registry.list_skills()
        assert len(skills) == 2
        assert skills[0]["name"] == "Skill One"
        assert "summary" in skills[0]

    def test_get_skill_summary(self):
        """Test getting skill summary.
        测试获取技能摘要。
        """
        self.registry.register(self.skill1)
        summary = self.registry.get_skill_summary("Skill One")
        assert summary is not None
        assert summary["name"] == "Skill One"
        assert "sections" in summary

    def test_get_skill_summary_nonexistent(self):
        """Test getting summary of nonexistent skill.
        测试获取不存在技能的摘要。
        """
        assert self.registry.get_skill_summary("Nonexistent") is None

    def test_get_skill_content(self):
        """Test getting skill content.
        测试获取技能内容。
        """
        self.registry.register(self.skill1)
        content = self.registry.get_skill_content("Skill One")
        assert "# Content" in content

    def test_get_skill_content_section(self):
        """Test getting specific section of skill content.
        测试获取技能内容的特定部分。
        """
        self.registry.register(self.skill1)
        content = self.registry.get_skill_content("Skill One")
        assert "# Content" in content

    def test_get_skill_content_nonexistent(self):
        """Test getting content of nonexistent skill.
        测试获取不存在技能的内容。
        """
        assert self.registry.get_skill_content("Nonexistent") is None


class TestMarkdownLoading:
    """Tests for loading skills from markdown files.
    从 markdown 文件加载技能的测试。
    """

    def test_load_from_markdown_file(self):
        """Test loading skill from a single markdown file.
        测试从单个 markdown 文件加载技能。
        """
        content = """---
name: Test Skill
description: A test skill
summary: Short summary
category: test
tags: [test, example]
---

# Introduction
This is a test skill.

## Usage
How to use it.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            registry = SkillRegistry.load_from_markdown(f.name)
            assert len(registry.list_skills()) == 1

            skill = registry.get_skill("Test Skill")
            assert skill is not None
            assert skill.description == "A test skill"
            assert skill.category == "test"
            assert skill.tags == ["test", "example"]

            os.unlink(f.name)

    def test_load_from_markdown_directory(self):
        """Test loading skills from a directory.
        测试从目录加载技能。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple markdown files
            file1 = Path(tmpdir) / "skill1.md"
            file1.write_text("""---
name: Skill 1
description: First skill
summary: Summary 1
---
Content 1
""")

            file2 = Path(tmpdir) / "skill2.md"
            file2.write_text("""---
name: Skill 2
description: Second skill
summary: Summary 2
---
Content 2
""")

            # Create a file starting with _ (should be ignored)
            file3 = Path(tmpdir) / "_ignore.md"
            file3.write_text("""---
name: Ignored
description: Should be ignored
summary: Ignored
---
Ignored content
""")

            registry = SkillRegistry.load_from_markdown(tmpdir)
            skills = registry.list_skills()

            assert len(skills) == 2
            names = [s["name"] for s in skills]
            assert "Skill 1" in names
            assert "Skill 2" in names
            assert "Ignored" not in names

    def test_load_without_front_matter(self):
        """Test loading markdown without front matter.
        测试加载没有 front matter 的 markdown。
        """
        content = "# Just Content\nNo front matter here."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            registry = SkillRegistry.load_from_markdown(f.name)
            assert len(registry.list_skills()) == 1

            # Name should be derived from filename
            skill = registry.get_skill(Path(f.name).stem.replace("_", " ").title())
            assert skill is not None

            os.unlink(f.name)


class TestProgressiveDisclosure:
    """Tests for progressive disclosure functionality.
    渐进式披露功能的测试。
    """

    def setup_method(self):
        self.registry = SkillRegistry()
        self.registry.register(MarkdownSkill(
            name="Code Review",
            description="Comprehensive code review skill with detailed analysis.",
            summary="Reviews code for quality and best practices",
            content="# Code Review\nFull content here with lots of details...",
        ))
        self.registry.register(MarkdownSkill(
            name="Debugging",
            description="Advanced debugging skill with runtime analysis capabilities.",
            summary="Debugs complex runtime issues",
            content="# Debugging\nFull debugging content...",
        ))

    def test_get_progressive_context(self):
        """Test getting progressive disclosure context.
        测试获取渐进式披露上下文。
        """
        context = self.registry.get_progressive_context(["Code Review", "Debugging"])

        assert "Available skills" in context
        assert "Code Review" in context
        assert "Reviews code for quality and best practices" in context
        assert "Debugging" in context
        assert "Debugs complex runtime issues" in context

    def test_get_progressive_context_partial(self):
        """Test getting context for subset of skills.
        测试获取部分技能的上下文。
        """
        context = self.registry.get_progressive_context(["Code Review"])

        assert "Code Review" in context
        assert "Debugging" not in context

    def test_get_progressive_context_nonexistent(self):
        """Test getting context with nonexistent skill.
        测试获取包含不存在技能的上下文。
        """
        context = self.registry.get_progressive_context(["Code Review", "Nonexistent"])

        assert "Code Review" in context
        assert "Nonexistent" not in context
