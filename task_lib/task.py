import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("mcp-task-service")
tag_re = re.compile(r'\[tag:.*?\]')
date_line_re = re.compile(r'\[due:.*?\]')


@dataclass
class Task:
    title: str
    content: str
    lane: str
    path: Path
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None

    @classmethod
    def from_dict(cls, task_dict) -> 'Task':
        """
        Creates a Task instance from a dictionary representation.

        This class method reconstructs a Task object from a dictionary containing
        task data. It handles optional fields gracefully and performs date parsing
        for the due_date field. If the due_date is present in the dictionary, it
        attempts to parse it from the '%Y-%m-%d' format. Invalid date formats or
        missing required keys are handled with appropriate error handling and
        logger.

        :param task_dict: Dictionary containing task data with keys such as
            'title', 'content', 'lane', 'tags', and 'due_date'
        :type task_dict: dict
        :return: A new Task instance created from the dictionary data, or None if
            required keys are missing
        :rtype: Task or None
        """
        try:
            due_date = datetime.strptime(task_dict['due_date'], '%Y-%m-%d') if 'due_date' in task_dict else None
        except ValueError:
            due_date = None
        try:
            task = cls(
                title=task_dict['title'],
                content=task_dict['content'],
                lane=task_dict['lane'],
                path=None,
                tags=task_dict.get('tags', None),
                due_date=due_date
            )
        except KeyError as e:
            logger.error(f"Missing required key in task dictionary: {e}")
            return None
        # Remove Task: object always holds content string without tags!
        task._remove_tags_from_content()
        task._remove_date_line_from_content()
        return task

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
        logger.debug(f"Loading task '{title}' from lane '{lane}'")
        # Extract tags if present
        tags = []
        due_date = None
        for line in content.split('\n'):
            matches = tag_re.findall(line)
            if matches:
                tags.extend([tag.strip('[]').split(":")[1].strip() for tag in matches])
            due_matches = date_line_re.findall(line)
            if due_matches:
                due_str = due_matches[0].strip('[]').split(":")[1].strip()
                try:
                    # Validate date format
                    due_date = datetime.strptime(due_str, '%Y-%m-%d')
                    logger.debug(f"Found due date: {due_str}")
                except ValueError:
                    logger.warning(f"Invalid due date format found: {due_str}")
                # Task object always holds content string without tags!

        logger.debug(f"Found tags: {tags}")
        task = cls(
            title=title,
            content=content,
            tags=tags,
            due_date=due_date,
            lane=lane,
            path=file_path
        )
        # Remove Task: object always holds content string without tags!
        task._remove_tags_from_content()
        task._remove_date_line_from_content()
        return task

    def _create_date_line_str(self):
        """
        Generates a date line for the task content, formatted as a markdown comment.

        :return: A string representing the date line if a due date is set, otherwise None.
        :rtype: Optional[str]
        """
        if self.due_date:
            return f"[due:{self.due_date.strftime('%Y-%m-%d')}]"
        return None

    def _remove_date_line_from_content(self) -> None:
        """
        Removes date line entries from the content by filtering out lines matching
        a date pattern.

        This method splits the content into individual lines, filters out any lines
        that match the date line regular expression pattern, and rejoins the
        remaining lines back into a single string.

        :return: Content string with date lines removed
        :rtype: str
        """
        lines = self.content.split('\n')
        filtered_lines = [line for line in lines if not date_line_re.match(line)]
        result = '\n'.join(filtered_lines)
        self.content = result

    def add_date_line_to_task_content(self, content=None):
        """
        Adds a formatted date line to the beginning of task content.

        Creates a date line string and prepends it to either the provided content
        parameter or the instance's content attribute. The date line is separated
        from the content by two newline characters. If no date line can be created,
        the original content is returned unchanged.

        :param content: Optional content string to which the date line should be
            prepended. If not provided, uses the instance's content attribute
        :type content: str or None
        :return: The content with the date line prepended, or the original content
            if no date line was created
        :rtype: str
        """
        date_line = self._create_date_line_str()
        result = content if content else self.content
        if date_line:
            if content:
                result = f"{date_line}\n\n{content}"
            else:
                result = f"{date_line}\n\n{self.content}"
        return result

    def _create_tag_lines_str(self) -> Optional[str]:
        """
        Create a formatted string representation of tags with each tag on a
        separate line.

        This method processes the tags collection and formats each tag into a
        bracketed tag line format. Each tag is prefixed with "tag:" and wrapped
        in square brackets. The resulting tag lines are joined with newline
        characters to create a multi-line string. If no tags are present, the
        method returns None. Debug logger is performed to track the tag
        formatting process.

        :return: A multi-line string with formatted tag lines, or None if no
                 tags exist
        :rtype: Optional[str]
        """
        if not self.tags:
            return None
        tag_strings = [f"[tag:{tag}]" for tag in self.tags]
        logger.debug(f"Creating tag lines: {tag_strings}")
        return '\n'.join(tag_strings)

    def _remove_tags_from_content(self) -> None:
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
        self.content = result

    def add_tag_lines_to_task_content(self, content=None) -> str:
        """
        Adds tag lines to the task content by prepending formatted tag
        information to either the provided content or the instance's
        content attribute.

        This method generates a formatted string of tag lines and combines
        it with the specified content or falls back to the instance's
        content. If no tag lines exist, the method returns the content
        unchanged.

        :param content: Optional content string to prepend tag lines to. If
            not provided, uses the instance's content attribute.
        :type content: str, optional
        :return: Content string with tag lines prepended if tags exist,
            separated by double newlines.
        :rtype: str
        """
        tag_lines = self._create_tag_lines_str()
        result = content if content else self.content
        if tag_lines:
            if content:
                result = f"{tag_lines}\n\n{content}"
            else:
                result = f"{tag_lines}\n\n{self.content}"
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
        # Restore tags and due date to text formatted task
        content = self.add_tag_lines_to_task_content(self.add_date_line_to_task_content())
        file_path.write_text(content)
        logger.debug(f"Writing task '{self.title}' to '{file_path}'")

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
        if '[[split]]' not in self.content:
            return [self]
        parts = self.content.split('[[split]]')
        new_tasks = []
        common_tags = self.tags.copy() if self.tags else []
        common_tags.append("multi-story feature")
        for i, part in enumerate(parts, 1):
            new_title = f"{i}-{self.title}"
            new_content = part.strip()
            # Preserve tags if they exist
            new_task = Task(
                title=new_title,
                content=new_content,
                tags=common_tags,
                due_date=self.due_date,
                lane=self.lane,
                path=self.path.parent / f"{new_title}.md"
            )
            new_tasks.append(new_task)
        return new_tasks
