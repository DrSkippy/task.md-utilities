import unittest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
from task_lib.task import Task


class TestTask(unittest.TestCase):
    """Test suite for the Task class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.lane_dir = self.test_dir / "todo"
        self.lane_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_task_creation_basic(self):
        """Test basic task creation."""
        task = Task(
            title="Test Task",
            content="This is test content",
            lane="todo",
            path=Path("test.md")
        )
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.content, "This is test content")
        self.assertEqual(task.lane, "todo")
        self.assertIsNone(task.tags)
        self.assertIsNone(task.due_date)

    def test_task_creation_with_tags(self):
        """Test task creation with tags."""
        task = Task(
            title="Tagged Task",
            content="Content",
            lane="todo",
            path=Path("test.md"),
            tags=["urgent", "bug"]
        )
        self.assertEqual(task.tags, ["urgent", "bug"])

    def test_task_creation_with_due_date(self):
        """Test task creation with due date."""
        due_date = datetime(2025, 12, 31)
        task = Task(
            title="Task",
            content="Content",
            lane="todo",
            path=Path("test.md"),
            due_date=due_date
        )
        self.assertEqual(task.due_date, due_date)

    def test_from_dict_basic(self):
        """Test creating task from dictionary."""
        task_dict = {
            'title': 'Dict Task',
            'content': 'Dict content',
            'lane': 'doing',
            'tags': ['tag1', 'tag2']
        }
        task = Task.from_dict(task_dict)
        self.assertEqual(task.title, 'Dict Task')
        self.assertEqual(task.content, 'Dict content')
        self.assertEqual(task.lane, 'doing')
        self.assertEqual(task.tags, ['tag1', 'tag2'])

    def test_from_dict_with_due_date(self):
        """Test creating task from dictionary with due date."""
        task_dict = {
            'title': 'Task',
            'content': 'Content',
            'lane': 'todo',
            'due_date': '2025-12-31'
        }
        task = Task.from_dict(task_dict)
        self.assertIsNotNone(task.due_date)
        self.assertEqual(task.due_date.year, 2025)
        self.assertEqual(task.due_date.month, 12)
        self.assertEqual(task.due_date.day, 31)

    def test_from_dict_invalid_due_date(self):
        """Test creating task from dictionary with invalid due date."""
        task_dict = {
            'title': 'Task',
            'content': 'Content',
            'lane': 'todo',
            'due_date': 'invalid-date'
        }
        task = Task.from_dict(task_dict)
        self.assertIsNone(task.due_date)

    def test_from_dict_missing_title(self):
        """Test creating task from dictionary without title."""
        task_dict = {
            'content': 'Content',
            'lane': 'todo'
        }
        task = Task.from_dict(task_dict)
        self.assertIsNone(task)

    def test_from_file_basic(self):
        """Test loading task from file."""
        task_file = self.lane_dir / "test-task.md"
        task_file.write_text("This is a test task content")

        task = Task.from_file(task_file, self.test_dir)
        self.assertEqual(task.title, "test-task")
        self.assertEqual(task.content, "This is a test task content")
        self.assertEqual(task.lane, "todo")
        self.assertEqual(task.path, task_file)

    def test_from_file_with_tags(self):
        """Test loading task from file with tags."""
        task_file = self.lane_dir / "tagged-task.md"
        content = "[tag:urgent]\n[tag:bug]\n\nTask content here"
        task_file.write_text(content)

        task = Task.from_file(task_file, self.test_dir)
        self.assertEqual(task.title, "tagged-task")
        self.assertEqual(task.tags, ["urgent", "bug"])
        self.assertNotIn("[tag:", task.content)

    def test_from_file_with_due_date(self):
        """Test loading task from file with due date."""
        task_file = self.lane_dir / "due-task.md"
        content = "[due:2025-12-31]\n\nTask content"
        task_file.write_text(content)

        task = Task.from_file(task_file, self.test_dir)
        self.assertIsNotNone(task.due_date)
        self.assertEqual(task.due_date.year, 2025)
        self.assertEqual(task.due_date.month, 12)
        self.assertEqual(task.due_date.day, 31)
        self.assertNotIn("[due:", task.content)

    def test_from_file_with_invalid_due_date(self):
        """Test loading task from file with invalid due date format."""
        task_file = self.lane_dir / "invalid-due-task.md"
        content = "[due:invalid-date]\n\nTask content"
        task_file.write_text(content)

        task = Task.from_file(task_file, self.test_dir)
        self.assertIsNone(task.due_date)

    def test_create_tag_lines_str(self):
        """Test creating tag lines string."""
        task = Task(
            title="Task",
            content="Content",
            lane="todo",
            path=Path("test.md"),
            tags=["urgent", "bug", "feature"]
        )
        tag_lines = task._create_tag_lines_str()
        self.assertIn("[tag:urgent]", tag_lines)
        self.assertIn("[tag:bug]", tag_lines)
        self.assertIn("[tag:feature]", tag_lines)

    def test_create_tag_lines_str_no_tags(self):
        """Test creating tag lines when no tags exist."""
        task = Task(
            title="Task",
            content="Content",
            lane="todo",
            path=Path("test.md")
        )
        tag_lines = task._create_tag_lines_str()
        self.assertIsNone(tag_lines)

    def test_create_date_line_str(self):
        """Test creating date line string."""
        task = Task(
            title="Task",
            content="Content",
            lane="todo",
            path=Path("test.md"),
            due_date=datetime(2025, 12, 31)
        )
        date_line = task._create_date_line_str()
        self.assertEqual(date_line, "[due:2025-12-31]")

    def test_create_date_line_str_no_due_date(self):
        """Test creating date line when no due date exists."""
        task = Task(
            title="Task",
            content="Content",
            lane="todo",
            path=Path("test.md")
        )
        date_line = task._create_date_line_str()
        self.assertIsNone(date_line)

    def test_add_tag_lines_to_task_content(self):
        """Test adding tag lines to task content."""
        task = Task(
            title="Task",
            content="Original content",
            lane="todo",
            path=Path("test.md"),
            tags=["urgent"]
        )
        result = task.add_tag_lines_to_task_content()
        self.assertIn("[tag:urgent]", result)
        self.assertIn("Original content", result)

    def test_add_date_line_to_task_content(self):
        """Test adding date line to task content."""
        task = Task(
            title="Task",
            content="Original content",
            lane="todo",
            path=Path("test.md"),
            due_date=datetime(2025, 12, 31)
        )
        result = task.add_date_line_to_task_content()
        self.assertIn("[due:2025-12-31]", result)
        self.assertIn("Original content", result)

    def test_to_file(self):
        """Test writing task to file."""
        task = Task(
            title="new-task",
            content="Task content",
            lane="todo",
            path=Path("new-task.md"),
            tags=["test"],
            due_date=datetime(2025, 12, 31)
        )
        task.to_file(self.test_dir)

        saved_file = self.test_dir / "todo" / "new-task.md"
        self.assertTrue(saved_file.exists())

        content = saved_file.read_text()
        self.assertIn("[tag:test]", content)
        self.assertIn("[due:2025-12-31]", content)
        self.assertIn("Task content", content)

    def test_split_task_with_split_marker(self):
        """Test splitting task with split marker."""
        task = Task(
            title="multi-task",
            content="First part[[split]]Second part[[split]]Third part",
            lane="todo",
            path=self.lane_dir / "multi-task.md",
            tags=["split-test"]
        )

        new_tasks = task.split()
        self.assertEqual(len(new_tasks), 3)
        self.assertEqual(new_tasks[0].title, "1-multi-task")
        self.assertEqual(new_tasks[1].title, "2-multi-task")
        self.assertEqual(new_tasks[2].title, "3-multi-task")
        self.assertIn("First part", new_tasks[0].content)
        self.assertIn("Second part", new_tasks[1].content)
        self.assertIn("Third part", new_tasks[2].content)

    def test_split_task_without_split_marker(self):
        """Test splitting task without split marker returns original."""
        task = Task(
            title="single-task",
            content="Just one task",
            lane="todo",
            path=self.lane_dir / "single-task.md"
        )

        new_tasks = task.split()
        self.assertEqual(len(new_tasks), 1)
        self.assertEqual(new_tasks[0], task)

    def test_split_task_preserves_tags(self):
        """Test that split tasks preserve original tags."""
        task = Task(
            title="tagged-split",
            content="Part 1[[split]]Part 2",
            lane="todo",
            path=self.lane_dir / "tagged-split.md",
            tags=["urgent", "bug"]
        )

        new_tasks = task.split()
        for new_task in new_tasks:
            self.assertEqual(new_task.tags, ["urgent", "bug", "multi-story feature"])

    def test_split_task_preserves_due_date(self):
        """Test that split tasks preserve original due date."""
        due_date = datetime(2025, 12, 31)
        task = Task(
            title="due-split",
            content="Part 1[[split]]Part 2",
            lane="todo",
            path=self.lane_dir / "due-split.md",
            due_date=due_date
        )

        new_tasks = task.split()
        for new_task in new_tasks:
            self.assertEqual(new_task.due_date, due_date)


if __name__ == '__main__':
    unittest.main()
