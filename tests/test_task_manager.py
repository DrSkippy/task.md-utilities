import unittest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
import csv
from unittest.mock import Mock, patch
from task_lib.task_manager import TaskManager
from task_lib.config import Config
from task_lib.task import Task


class TestTaskManager(unittest.TestCase):
    """Test suite for the TaskManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config = Config()
        self.config.base_dir = self.test_dir
        self.task_manager = TaskManager(self.config)

        # Create test lanes
        self.todo_lane = self.test_dir / "todo"
        self.doing_lane = self.test_dir / "doing"
        self.done_lane = self.test_dir / "done"
        self.todo_lane.mkdir(exist_ok=True)
        self.doing_lane.mkdir(exist_ok=True)
        self.done_lane.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_task_manager_initialization(self):
        """Test TaskManager initialization."""
        self.assertEqual(self.task_manager.base_dir, self.test_dir)
        self.assertEqual(self.task_manager.trash_dir, self.test_dir / "Trash")
        self.assertTrue(self.task_manager.trash_dir.exists())


    def test_get_all_tasks_empty(self):
        """Test getting all tasks from empty lanes."""
        tasks = self.task_manager.get_all_tasks()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(len(tasks['todo']), 0)
        self.assertEqual(len(tasks['doing']), 0)
        self.assertEqual(len(tasks['done']), 0)

    def test_get_all_tasks_with_tasks(self):
        """Test getting all tasks with existing tasks."""
        # Create test tasks
        (self.todo_lane / "task1.md").write_text("Task 1 content")
        (self.todo_lane / "task2.md").write_text("Task 2 content")
        (self.doing_lane / "task3.md").write_text("Task 3 content")

        tasks = self.task_manager.get_all_tasks()
        self.assertEqual(len(tasks['todo']), 2)
        self.assertEqual(len(tasks['doing']), 1)
        self.assertEqual(len(tasks['done']), 0)

    def test_get_all_tasks_ignores_trash(self):
        """Test that get_all_tasks ignores the Trash directory."""
        trash_dir = self.test_dir / "Trash"
        trash_dir.mkdir(exist_ok=True)
        (trash_dir / "trashed-task.md").write_text("Trashed content")

        tasks = self.task_manager.get_all_tasks()
        self.assertNotIn('Trash', tasks)

    def test_add_lane(self):
        """Test adding a new lane."""
        new_lane = "backlog"
        self.task_manager.add_lane(new_lane)

        lane_dir = self.test_dir / new_lane
        self.assertTrue(lane_dir.exists())
        self.assertTrue(lane_dir.is_dir())

    def test_add_lane_already_exists(self):
        """Test adding a lane that already exists."""
        self.task_manager.add_lane("todo")
        self.assertTrue(self.todo_lane.exists())

    def test_split_tasks_with_split_marker(self):
        """Test splitting tasks that contain split marker."""
        task_file = self.todo_lane / "multi-task.md"
        content = "First part[[split]]Second part[[split]]Third part"
        task_file.write_text(content)

        self.task_manager.split_tasks()

        # Original should be in trash
        trash_file = self.task_manager.trash_dir / "multi-task.md"
        self.assertTrue(trash_file.exists())

        # New split tasks should exist
        self.assertTrue((self.todo_lane / "1-multi-task.md").exists())
        self.assertTrue((self.todo_lane / "2-multi-task.md").exists())
        self.assertTrue((self.todo_lane / "3-multi-task.md").exists())

    def test_split_tasks_without_split_marker(self):
        """Test that tasks without split marker are unchanged."""
        task_file = self.todo_lane / "normal-task.md"
        content = "Normal task content"
        task_file.write_text(content)

        self.task_manager.split_tasks()

        # Original should still exist
        self.assertTrue(task_file.exists())
        # Should not be in trash
        trash_file = self.task_manager.trash_dir / "normal-task.md"
        self.assertFalse(trash_file.exists())

    def test_create_tasks_from_csv(self):
        """Test creating tasks from CSV file."""
        csv_file = self.test_dir / "tasks.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'task', 'tag_list', 'lane'])
            writer.writeheader()
            writer.writerow({
                'title': 'csv-task-1',
                'task': 'Content for task 1',
                'tag_list': 'urgent, bug',
                'lane': 'todo'
            })
            writer.writerow({
                'title': 'csv-task-2',
                'task': 'Content for task 2',
                'tag_list': 'feature',
                'lane': 'doing'
            })

        self.task_manager.create_tasks_from_csv(str(csv_file))

        # Check that tasks were created
        self.assertTrue((self.todo_lane / "csv-task-1.md").exists())
        self.assertTrue((self.doing_lane / "csv-task-2.md").exists())

        # Verify content
        task1_content = (self.todo_lane / "csv-task-1.md").read_text()
        self.assertIn("Content for task 1", task1_content)

    def test_empty_trash(self):
        """Test emptying the trash directory."""
        trash_dir = self.task_manager.trash_dir
        (trash_dir / "trash1.md").write_text("Trash 1")
        (trash_dir / "trash2.md").write_text("Trash 2")
        (trash_dir / "trash3.md").write_text("Trash 3")

        self.task_manager.empty_trash()

        remaining_files = list(trash_dir.glob("*.md"))
        self.assertEqual(len(remaining_files), 0)

    def test_change_lane_success(self):
        """Test successfully changing a task's lane."""
        task_file = self.todo_lane / "task-to-move.md"
        task_file.write_text("Task content")

        self.task_manager.change_lane("task-to-move", "doing")

        # Original location should not exist
        self.assertFalse(task_file.exists())
        # New location should exist
        new_location = self.doing_lane / "task-to-move.md"
        self.assertTrue(new_location.exists())

    def test_change_lane_to_new_lane(self):
        """Test changing a task to a non-existent lane (creates it)."""
        task_file = self.todo_lane / "task-to-move.md"
        task_file.write_text("Task content")

        new_lane_name = "review"
        self.task_manager.change_lane("task-to-move", new_lane_name)

        # New lane should be created
        new_lane_dir = self.test_dir / new_lane_name
        self.assertTrue(new_lane_dir.exists())

        # Task should be in new lane
        new_location = new_lane_dir / "task-to-move.md"
        self.assertTrue(new_location.exists())

    def test_change_lane_task_not_found(self):
        """Test changing lane for non-existent task."""
        # This should not raise an error, just print a message
        self.task_manager.change_lane("non-existent-task", "doing")
        # No exception should be raised

    def test_calculate_statistics_empty(self):
        """Test statistics calculation with no tasks."""
        stats = self.task_manager.calculate_statistics()

        self.assertEqual(stats['num_lanes'], 3)
        self.assertEqual(stats['tasks_per_lane']['todo'], 0)
        self.assertEqual(stats['tasks_per_lane']['doing'], 0)
        self.assertEqual(stats['tasks_per_lane']['done'], 0)
        self.assertEqual(len(stats['tag_counts']), 0)

    def test_calculate_statistics_with_tasks(self):
        """Test statistics calculation with tasks."""
        # Create tasks with tags
        (self.todo_lane / "task1.md").write_text("[tag:urgent]\n[tag:bug]\n\nTask 1")
        (self.todo_lane / "task2.md").write_text("[tag:urgent]\n\nTask 2")
        (self.doing_lane / "task3.md").write_text("[tag:feature]\n\nTask 3")

        stats = self.task_manager.calculate_statistics()

        self.assertEqual(stats['num_lanes'], 3)
        self.assertEqual(stats['tasks_per_lane']['todo'], 2)
        self.assertEqual(stats['tasks_per_lane']['doing'], 1)
        self.assertEqual(stats['tasks_per_lane']['done'], 0)
        self.assertEqual(stats['tag_counts']['urgent'], 2)
        self.assertEqual(stats['tag_counts']['bug'], 1)
        self.assertEqual(stats['tag_counts']['feature'], 1)

    def test_calculate_statistics_with_due_dates(self):
        """Test statistics calculation with due dates."""
        (self.todo_lane / "task1.md").write_text("[due:2025-12-31]\n\nTask 1")
        (self.todo_lane / "task2.md").write_text("[due:2025-12-31]\n\nTask 2")
        (self.doing_lane / "task3.md").write_text("Task 3 no due date")

        stats = self.task_manager.calculate_statistics()

        self.assertEqual(stats['due_date_counts']['2025-12-31'], 2)
        self.assertEqual(stats['due_date_counts']['No Due Date'], 1)

    def test_get_all_tasks_with_tags(self):
        """Test that tasks are loaded correctly with tags."""
        task_content = "[tag:urgent]\n[tag:bug]\n\nTask content here"
        (self.todo_lane / "tagged-task.md").write_text(task_content)

        tasks = self.task_manager.get_all_tasks()
        task = tasks['todo'][0]

        self.assertEqual(task.tags, ['urgent', 'bug'])
        self.assertNotIn('[tag:', task.content)

    def test_get_all_tasks_with_due_date(self):
        """Test that tasks are loaded correctly with due dates."""
        task_content = "[due:2025-12-31]\n\nTask content here"
        (self.todo_lane / "due-task.md").write_text(task_content)

        tasks = self.task_manager.get_all_tasks()
        task = tasks['todo'][0]

        self.assertIsNotNone(task.due_date)
        self.assertEqual(task.due_date.year, 2025)
        self.assertNotIn('[due:', task.content)

    def test_split_tasks_preserves_tags(self):
        """Test that split tasks preserve tags."""
        task_file = self.todo_lane / "tagged-split.md"
        content = "[tag:urgent]\n[tag:bug]\n\nPart 1[[split]]Part 2"
        task_file.write_text(content)

        self.task_manager.split_tasks()

        # Check that split tasks have tags
        task1_content = (self.todo_lane / "1-tagged-split.md").read_text()
        self.assertIn("[tag:urgent]", task1_content)
        self.assertIn("[tag:bug]", task1_content)


if __name__ == '__main__':
    unittest.main()
