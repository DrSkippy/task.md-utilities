from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class Task:
    title: str
    content: str
    tags: List[str]
    lane: str
    path: Path

    @classmethod
    def from_file(cls, file_path: Path, base_dir: Path) -> 'Task':
        """Create a Task instance from a markdown file."""
        content = file_path.read_text()
        title = file_path.stem
        lane = file_path.parent.name
        
        # Extract tags if present
        tags = []
        for line in content.split('\n'):
            if line.startswith('tags:'):
                tags = [tag.strip() for tag in line[5:].split(',')]
                break
        
        return cls(
            title=title,
            content=content,
            tags=tags,
            lane=lane,
            path=file_path
        )

    def to_file(self, base_dir: Path) -> None:
        """Write task to a markdown file."""
        task_dir = base_dir / self.lane
        task_dir.mkdir(exist_ok=True)
        
        file_path = task_dir / f"{self.title}.md"
        file_path.write_text(self.content)

    def split(self) -> List['Task']:
        """Split task into multiple tasks based on [[split]] marker."""
        if '[[split]]' not in self.content:
            return [self]
            
        parts = self.content.split('[[split]]')
        # remove the tags from part1[0] so it doen't appear twice
        parts[0] = parts[0].replace(f"tags: {', '.join(self.tags)}\n", "")
        
        new_tasks = []
        
        for i, part in enumerate(parts, 1):
            new_title = f"{i}-{self.title}"
            new_content = part.strip()
            
            # Preserve tags if they exist
            if self.tags:
                new_content = f"tags: {', '.join(self.tags)}\n\n{new_content}"
                
            new_task = Task(
                title=new_title,
                content=new_content,
                tags=self.tags.copy(),
                lane=self.lane,
                path=self.path.parent / f"{new_title}.md"
            )
            new_tasks.append(new_task)
            
        return new_tasks 