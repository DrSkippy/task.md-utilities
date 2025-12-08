import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

tag_re = re.compile(r'\[tag:(.*?)\]')


@dataclass
class Task:
    title: str
    content: str
    tags: List[str]
    lane: str
    path: Path

    @classmethod
    def from_file(cls, file_path: Path, base_dir: Path) -> 'Task':
        """
        Create a Task instance by reading task details from a file located within a specified base directory.

        :param file_path: Path to the file containing the task details.
        :param base_dir: Path to the base directory containing task files.
        :return: A Task instance populated with the extracted file content, title, tags, lane, and file path attributes.
        """
        content = file_path.read_text()
        title = file_path.stem
        lane = file_path.parent.name
        logging.debug(f"Loading task '{title}' from lane '{lane}'")
        # Extract tags if present
        tags = []
        for line in content.split('\n'):
            matches = tag_re.findall(line)
            if matches:
                tags.extend([tag.strip('[]')[6, -1] for tag in matches])
                break
        logging.debug(f"Found tags: {tags}")
        return cls(
            title=title,
            content=content,
            tags=tags,
            lane=lane,
            path=file_path
        )

    def _create_tag_lines(self) -> Optional[str]:
        """
        Generates tag lines from a list of tags if they exist. Each tag is formatted
        as `[tag:<tag>]` and tag lines are concatenated with newline characters.

        :return: A string of concatenated tag lines if tags are present,
            otherwise None.
        :rtype: Optional[str]
        """
        if not self.tags:
            return None
        tag_strings = [f"[tag:{tag}]" for tag in self.tags]
        logging.debug(f"Creating tag lines: {tag_strings}")
        return '\n'.join(tag_strings)

    def add_tag_lines_to_task_content(self) -> str:
        """
        Adds generated tag lines to the content of a task and updates the content.

        This function generates tag lines using an internal private method
        and prepends them to the current content of the task. If no tag lines
        are generated, the content remains unchanged.

        :return: Updated task content with tag lines prepended.
        :rtype: str
        """
        tag_lines = self._create_tag_lines()
        if tag_lines:
            result = f"{tag_lines}\n\n{self.content}"
            self.content = result
        return self.content

    def _remove_tags_from_content(self) -> str:
        """
        Removes lines matching a specific tag pattern from the content. The method scans
        through each line in the content, filters out lines that match the tag pattern,
        and then reconstructs the remaining lines into a content string without tags.

        :return: A string with lines matching the specified tag pattern removed.
        :rtype: str
        """
        lines = self.content.split('\n')
        filtered_lines = [line for line in lines if not tag_re.match(line)]
        result = '\n'.join(filtered_lines).strip()
        return result

    def to_file(self, base_dir: Path) -> None:
        """
        Writes the task content to a markdown file in the specified directory.

        The method first creates a subdirectory within the given `base_dir`, named
        after the task lane. It then constructs the file path using the task title,
        and writes the task's content into a markdown file at that location. If the
        subdirectory already exists, it does not raise an error.

        :param base_dir: Base directory in which the task will be saved.
        :type base_dir: Path
        :return: None
        """
        task_dir = base_dir / self.lane
        task_dir.mkdir(exist_ok=True)
        file_path = task_dir / f"{self.title}.md"
        file_path.write_text(self.content)
        logging.debug(f"Writing task '{self.title}' to '{file_path}'")

    def split(self) -> List['Task']:
        """
        Splits the content of the current task into multiple tasks based on a specific
        delimiter and creates new task instances for each segment. The delimiter used
        is `[[split]]`. If the delimiter is not present, the original task is returned
        as a single-item list.

        New tasks are created with titles that include a numerical prefix indicating
        their order in the split. Tags, if available, are preserved in the new tasks.

        :return: A list of new tasks created from the split.
        :rtype: List[Task]
        """
        _content = self._remove_tags_from_content()
        if '[[split]]' not in _content:
            return [self]
        parts = _content.split('[[split]]')
        new_tasks = []
        for i, part in enumerate(parts, 1):
            new_title = f"{i}-{self.title}"
            new_content = part.strip()
            # Preserve tags if they exist
            if self.tags:
                new_content = f"{self._create_tag_lines()}\n\n{new_content}"
            new_task = Task(
                title=new_title,
                content=new_content,
                tags=self.tags.copy(),
                lane=self.lane,
                path=self.path.parent / f"{new_title}.md"
            )
            new_tasks.append(new_task)
        return new_tasks
