import csv
import openai
import shutil
from pathlib import Path
from typing import List, Dict

from .config import Config
from .task import Task


class TaskManager:
    def __init__(self, config: Config):
        """
        Initializes an instance of the class with configuration settings.

        This constructor sets up necessary directories and configures the OpenAI API
        if an API key is provided in the given configuration.

        :param config: The configuration object that contains required settings
            for the class initialization, such as base directory and OpenAI API key.
        :type config: Config
        """
        self.config = config
        self.base_dir = config.base_dir
        self.trash_dir = self.base_dir / "Trash"
        self.trash_dir.mkdir(exist_ok=True)
        # Configure OpenAI if API key is available
        if config.openai_api_key:
            openai.api_key = config.openai_api_key

    def get_all_tasks(self) -> Dict[str, List[Task]]:
        """
        Retrieves and organizes all tasks by their respective lanes.

        This method reads all task files from directories within the base directory.
        Each directory other than "Trash" is considered a lane. Task files found
        in each lane directory are processed and grouped by the lane name. The
        resulting data is organized into a dictionary where the keys represent
        lane names and the values are lists of Task objects corresponding to that
        lane.

        :return: A dictionary where the keys are lane names (str) and the values are
            lists of Task objects corresponding to the tasks found in those lanes.
        :rtype: Dict[str, List[Task]]
        """
        tasks_by_lane = {}

        for lane_dir in self.base_dir.iterdir():
            if not lane_dir.is_dir() or lane_dir.name == "Trash":
                continue
            tasks = []
            for task_file in lane_dir.glob("*.md"):
                task = Task.from_file(task_file, self.base_dir)
                tasks.append(task)
            tasks_by_lane[lane_dir.name] = tasks
        return tasks_by_lane

    def add_lane(self, lane_name: str) -> None:
        """
        Creates a new lane directory with the specified name inside the base directory.

        The method ensures that the directory is created. If the directory already exists, it does not raise an error.

        :param lane_name: Name of the lane directory to be created.
        :type lane_name: str
        :return: None
        """
        lane_dir = self.base_dir / lane_name
        lane_dir.mkdir(exist_ok=True)

    def split_tasks(self) -> None:
        """
        Splits tasks containing the marker '[[split]]' into multiple tasks, saves the
        newly created tasks to files, and moves the original tasks to the trash
        directory.

        This function retrieves all tasks grouped by their respective lanes. For each
        task that includes the '[[split]]' marker in its content, it performs the
        following actions:
        1. Splits the task into smaller tasks.
        2. Saves each new task to its corresponding file in the base directory.
        3. Moves the original task file to the trash directory.

        :raises FileNotFoundError: If any original task file to be moved to the trash
            does not exist.
        :raises shutil.Error: If there is an issue moving a file to the trash
            directory such as insufficient permissions or disk space.

        :return: None
        """
        tasks_by_lane = self.get_all_tasks()

        for lane, tasks in tasks_by_lane.items():
            for task in tasks:
                if '[[split]]' in task.content:
                    # Create new split tasks
                    new_tasks = task.split()
                    for new_task in new_tasks:
                        new_task.to_file(self.base_dir)

                    # Move original to trash
                    trash_path = self.trash_dir / task.path.name
                    shutil.move(str(task.path), str(trash_path))

    def create_tasks_from_csv(self, csv_path: str) -> None:
        """
        Creates tasks based on the data from a given CSV file.

        This function reads the provided CSV file, extracts task details such as title, tags,
        content, and lane, and creates tasks accordingly. For each task, optional tags are
        added to the content if present, and the task is then saved as a Markdown file
        (.md) in the specified directory structure.

        :param csv_path: The path to the CSV file containing task data.
        :type csv_path: str
        :return: This function does not return a value.
        :rtype: None
        """
        with (open(csv_path, 'r') as f):
            reader = csv.DictReader(f)
            for row in reader:
                title = row['title']
                tags = [tag.strip() for tag in row['tag_list'].split(',')]
                content = row['task']
                lane = row['lane']
                task = Task(
                    title=title,
                    content=content,
                    tags=tags,
                    lane=lane,  # Default lane
                    path=self.base_dir / lane / f"{title}.md"
                )
                # Add tags to content if present
                if tags:
                    task.add_tag_lines_to_task_content()
                task.to_file(self.base_dir)

    def empty_trash(self) -> None:
        """
        Removes all markdown files from the trash directory. This method iterates
        through all markdown files in the specified trash directory, deletes each
        file, and then prints the number of deleted files.

        :raises FileNotFoundError: An error is not raised explicitly by this function,
            but it may occur if trash_dir is not a valid directory.
        :raises PermissionError: May occur if the function lacks the necessary
            permissions to delete files in the specified trash directory.

        :return: None
        """
        for file in self.trash_dir.glob("*.md"):
            file.unlink()
        print(f"Removed {len(list(self.trash_dir.glob('*.md')))} files from trash")

    def change_lane(self, task_title: str, new_lane: str) -> None:
        """
        Changes the lane of a specified task by moving its corresponding file to a new
        location. If the new lane does not exist, it creates a new directory for it
        before performing the move operation.

        :param task_title: The title of the task to be relocated.
        :type task_title: str
        :param new_lane: The name of the new lane where the task should be moved.
        :type new_lane: str
        :return: None
        """
        # Search for the task in all lanes
        task_found = False
        for lane_dir in self.base_dir.iterdir():
            if not lane_dir.is_dir() or lane_dir.name == "Trash":
                continue
            task_file = lane_dir / f"{task_title}.md"
            if task_file.exists():
                task_found = True
                # Create new lane if it doesn't exist
                new_lane_dir = self.base_dir / new_lane
                new_lane_dir.mkdir(exist_ok=True)

                # Move the file to the new lane
                new_path = new_lane_dir / task_file.name
                shutil.move(str(task_file), str(new_path))
                print(f"Moved task '{task_title}' from '{lane_dir.name}' to '{new_lane}'")
                break
        if not task_found:
            print(f"Error: Task '{task_title}' not found in any lane")

    def calculate_statistics(self) -> Dict:
        """
        Calculates and returns a statistical summary of tasks organized by lanes and tags.

        This method processes all the tasks grouped by lanes, counts the total number
        of lanes, determines the number of tasks per lane, and calculates how often
        each tag appears across all tasks. The returned dictionary provides a structured
        overview of these computed statistics.

        :return: A dictionary containing the following keys and corresponding values:
            - 'num_lanes': Total number of lanes.
            - 'tasks_per_lane': A dictionary where keys are lane names and values are the
              count of tasks in each lane.
            - 'tag_counts': A dictionary where keys are tags and values represent the
              count of occurrences of each tag.
        :rtype: dict
        """
        tasks_by_lane = self.get_all_tasks()
        # Count lanes
        num_lanes = len(tasks_by_lane)
        # Count tasks per lane
        tasks_per_lane = {lane: len(tasks) for lane, tasks in tasks_by_lane.items()}
        # Count tag occurrences
        tag_counts = {}
        for lane, tasks in tasks_by_lane.items():
            for task in tasks:
                for tag in task.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return {
            'num_lanes': num_lanes,
            'tasks_per_lane': tasks_per_lane,
            'tag_counts': tag_counts
        }
