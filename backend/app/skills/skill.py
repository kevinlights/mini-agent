# Skill Base Class and Registry with Progressive Disclosure
# 技能基础类和注册表，支持渐进式披露

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import re
from app.log import logger



@dataclass
class SkillMetadata:
    """Metadata for a skill loaded from markdown.
    从 markdown 加载的技能元数据。
    """

    name: str
    description: str
    summary: str  # Short summary for progressive disclosure
    category: str = "general"
    tags: List[str] = field(default_factory=list)


@dataclass
class SkillContent:
    """Full content of a skill.
    技能的完整内容。
    """

    name: str
    metadata: SkillMetadata
    full_content: str  # Full markdown content
    sections: Dict[str, str] = field(default_factory=dict)  # Parsed sections


class BaseSkill(ABC):
    """Base class for all skills.
    所有技能的基础类。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the skill.
        技能的唯一名称。
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the skill does.
        技能功能的描述。
        """
        pass

    @property
    def summary(self) -> str:
        """Short summary for progressive disclosure.
        用于渐进式披露的简短摘要。
        """
        return self.description[:100]

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the skill with given parameters.
        使用给定参数执行技能。

        Args:
            **kwargs: Parameter values.
                参数值。

        Returns:
            Execution result.
                执行结果。
        """
        pass


class MarkdownSkill(BaseSkill):
    """Skill loaded from markdown file.
    从 markdown 文件加载的技能。
    """

    def __init__(
        self,
        name: str,
        description: str,
        summary: str,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
    ):
        self._name = name
        self._description = description
        self._summary = summary
        self._content = content
        self._category = category
        self._tags = tags or []
        self._sections = self._parse_sections(content)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def summary(self) -> str:
        return self._summary

    @property
    def category(self) -> str:
        return self._category

    @property
    def tags(self) -> List[str]:
        return self._tags

    @property
    def sections(self) -> Dict[str, str]:
        return self._sections

    @property
    def full_content(self) -> str:
        return self._content

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown content into sections by headings.
        将 markdown 内容按标题解析为多个部分。

        Args:
            content: Markdown content string.
                Markdown 内容字符串。

        Returns:
            Dictionary mapping section name to content.
                映射部分名称到内容的字典。
        """
        sections = {}
        # Split by ## headings
        pattern = r'^##\s+(.+)$'
        parts = re.split(pattern, content, flags=re.MULTILINE)

        if len(parts) > 1:
            # First part before any heading
            if parts[0].strip():
                sections["introduction"] = parts[0].strip()

            # Process heading/content pairs
            for i in range(1, len(parts), 2):
                heading = parts[i].strip().lower().replace(" ", "_")
                body = parts[i + 1].strip() if i + 1 < len(parts) else ""
                if body:
                    sections[heading] = body
        else:
            # No headings, treat entire content as one section
            sections["content"] = content.strip()

        return sections

    async def execute(self, **kwargs) -> str:
        """Execute the skill - returns the skill content as context.
        执行技能 - 返回技能内容作为上下文。

        Args:
            **kwargs: Parameters like 'section' to get specific part.
                参数如 'section' 用于获取特定部分。

        Returns:
            Skill content or specific section.
                技能内容或特定部分。
        """
        section = kwargs.get("section")
        if section and section in self._sections:
            return self._sections[section]
        return self._content


class SkillRegistry:
    """Registry for managing skills with progressive disclosure.
    管理技能的注册表，支持渐进式披露。
    """

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill):
        """Register a skill.
        注册一个技能。

        Args:
            skill: Skill instance to register.
                要注册的技能实例。
        """
        self._skills[skill.name] = skill

    def unregister(self, name: str):
        """Unregister a skill by name.
        按名称注销一个技能。

        Args:
            name: Name of the skill to remove.
                要移除的技能名称。
        """
        self._skills.pop(name, None)

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name (case-insensitive).
        按名称获取技能（不区分大小写）。

        Args:
            name: Name of the skill.
                技能名称。

        Returns:
            Skill instance or None.
                技能实例或 None。
        """
        name_lower = name.lower()
        for skill_name, skill in self._skills.items():
            if skill_name.lower() == name_lower:
                return skill
        return None

    def list_skills(self) -> List[Dict[str, str]]:
        """List all registered skills with summary only (progressive disclosure).
        列出所有已注册的技能，仅显示摘要（渐进式披露）。

        Returns:
            List of skill summaries.
                技能摘要列表。
        """
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "summary": skill.summary,
            }
            for skill in self._skills.values()
        ]

    def get_skill_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed summary of a specific skill.
        获取特定技能的详细摘要。

        Args:
            name: Name of the skill.
                技能名称。

        Returns:
            Skill summary with sections list.
                包含部分列表的技能摘要。
        """
        skill = self._skills.get(name)
        if not skill:
            return None

        if isinstance(skill, MarkdownSkill):
            return {
                "name": skill.name,
                "description": skill.description,
                "summary": skill.summary,
                "category": skill.category,
                "tags": skill.tags,
                "sections": list(skill.sections.keys()),
            }

        return {
            "name": skill.name,
            "description": skill.description,
            "summary": skill.summary,
        }

    def get_skill_content(self, name: str, section: Optional[str] = None) -> Optional[str]:
        """Get full content of a skill, optionally a specific section.
        获取技能的完整内容，可选择特定部分。

        Args:
            name: Name of the skill.
                技能名称。
            section: Specific section name (optional).
                特定部分名称（可选）。

        Returns:
            Skill content or None.
                技能内容或 None。
        """
        skill = self._skills.get(name)
        if not skill:
            return None

        if isinstance(skill, MarkdownSkill):
            return skill.full_content if not section else skill.sections.get(section, "")

        return skill.summary

    @classmethod
    def load_from_markdown(cls, file_path: str) -> "SkillRegistry":
        """Load skills from a markdown file.
        从 markdown 文件加载技能。

        Args:
            file_path: Path to markdown file or directory.
                Markdown 文件或目录的路径。

        Returns:
            SkillRegistry with loaded skills.
                包含已加载技能的 SkillRegistry。
        """
        registry = cls()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File or directory not found: {file_path}")

        if path.is_file():
            registry._load_single_markdown(path)
        elif path.is_dir():
            for md_file in path.glob("**/*.md"):
                if not md_file.name.startswith("_"):
                    registry._load_single_markdown(md_file)

        return registry

    def _load_single_markdown(self, file_path: Path):
        """Load a single markdown file as a skill.
        将单个 markdown 文件加载为技能。

        Args:
            file_path: Path to the markdown file.
                Markdown 文件的路径。
        """
        content = file_path.read_text(encoding="utf-8")

        # Parse YAML front matter if exists
        metadata = self._parse_front_matter(content)

        name = metadata.get("name", file_path.stem.replace("_", " ").title())
        description = metadata.get("description", f"Skill loaded from {file_path.name}")
        summary = metadata.get("summary", description[:100])
        category = metadata.get("category", "general")
        tags = metadata.get("tags", [])

        # Remove front matter from content
        clean_content = self._remove_front_matter(content)

        skill = MarkdownSkill(
            name=name,
            description=description,
            summary=summary,
            content=clean_content,
            category=category,
            tags=tags,
        )

        self.register(skill)
        logger.debug(f"Loaded skill: {name}")

    def _parse_front_matter(self, content: str) -> Dict[str, Any]:
        """Parse YAML front matter from markdown.
        从 markdown 解析 YAML front matter。

        Args:
            content: Markdown content.
                Markdown 内容。

        Returns:
            Dictionary of front matter values.
                front matter 值的字典。
        """
        metadata = {}
        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, content, re.DOTALL)

        if match:
            front_matter = match.group(1)
            for line in front_matter.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Parse lists like [tag1, tag2]
                    if value.startswith("[") and value.endswith("]"):
                        value = [v.strip() for v in value[1:-1].split(",") if v.strip()]

                    metadata[key] = value

        return metadata

    def _remove_front_matter(self, content: str) -> str:
        """Remove YAML front matter from markdown content.
        从 markdown 内容中移除 YAML front matter。

        Args:
            content: Markdown content.
                Markdown 内容。

        Returns:
            Content without front matter.
                移除了 front matter 的内容。
        """
        pattern = r"^---\s*\n.*?\n---\s*\n"
        return re.sub(pattern, "", content, count=1, flags=re.DOTALL).strip()

    def get_progressive_context(self, skill_names: List[str]) -> str:
        """Get progressive disclosure context for multiple skills.
        获取多个技能的渐进式披露上下文。

        This returns only summaries first, keeping context short.
        这首先只返回摘要，保持上下文简短。

        Args:
            skill_names: List of skill names to include.
                要包含的技能名称列表。

        Returns:
            Formatted context string with skill summaries.
                包含技能摘要的格式化上下文字符串。
        """
        parts = []
        parts.append("Available skills (use skill name to get full content when needed):")

        for name in skill_names:
            skill = self._skills.get(name)
            if skill:
                parts.append(f"- {skill.name}: {skill.summary}")

        return "\n".join(parts)
