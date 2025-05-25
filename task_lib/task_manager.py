from pathlib import Path
from typing import List, Dict
import csv
import shutil

from .task import Task

class TaskManager:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.trash_dir = self.base_dir / "Trash"
        self.trash_dir.mkdir(exist_ok=True)

    def get_all_tasks(self) -> Dict[str, List[Task]]:
        """Get all tasks organized by lane."""
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
        """Add a new lane (directory)."""
        lane_dir = self.base_dir / lane_name
        lane_dir.mkdir(exist_ok=True)

    def split_tasks(self) -> None:
        """Split tasks containing [[split]] marker and move originals to trash."""
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
        """Create tasks from a CSV file with columns: title, tag_list, task."""
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row['title']
                tags = [tag.strip() for tag in row['tag_list'].split(',')]
                content = row['task']
                lane = row['lane']
                
                # Add tags to content if present
                if tags:
                    content = f"tags: {', '.join(tags)}\n\n{content}"
                
                task = Task(
                    title=title,
                    content=content,
                    tags=tags,
                    lane=lane,  # Default lane
                    path=self.base_dir / lane / f"{title}.md"
                )
                task.to_file(self.base_dir) 

    def empty_trash(self) -> None:
        """Empty the trash directory by removing all files."""
        for file in self.trash_dir.glob("*.md"):
            file.unlink()
        print(f"Removed {len(list(self.trash_dir.glob('*.md')))} files from trash") 

    def change_lane(self, task_title: str, new_lane: str) -> None:
        """Change the lane of a task by moving its file to the new lane directory."""
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
                