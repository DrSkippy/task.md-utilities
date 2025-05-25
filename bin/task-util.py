#!/usr/bin/env -S poetry run python

import argparse
from pathlib import Path
import sys
import os

from task_lib.task_manager import TaskManager
from task_lib.config import Config

def main():
    parser = argparse.ArgumentParser(description='Task Manager Utility')
    parser.add_argument('--config', type=str,
                      help='Path to configuration file')
    parser.add_argument('--base-dir', type=str, default='.',
                      help='Base directory for tasks (default: current directory)')
    parser.add_argument('--show-tasks', action='store_true',
                      help='Show all tasks in all lanes')
    parser.add_argument('--split-tasks', action='store_true',
                      help='Split tasks containing [[split]] marker')
    parser.add_argument('--add-lane', type=str,
                      help='Add a new lane')
    parser.add_argument('--csv-create-tasks', type=str,
                      help='Create tasks from CSV file')
    parser.add_argument('--empty-trash', action='store_true',
                      help='Empty the trash directory')
    parser.add_argument('--change-lane', nargs=2, metavar=('task', 'new-lane'),
                      help='Change the lane of a task')

    args = parser.parse_args()
    
    # Load configuration
    config = Config()
    if args.config:
        try:
            config = Config(Path(args.config))
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    # Override base_dir from command line if specified
    if args.base_dir != '.':
        config.base_dir = Path(args.base_dir).resolve()
    
    # Ensure base directory exists
    if not config.base_dir.exists():
        print(f"Error: Base directory '{config.base_dir}' does not exist")
        sys.exit(1)

    task_manager = TaskManager(config)

    if args.show_tasks:
        tasks_by_lane = task_manager.get_all_tasks()
        for lane, tasks in tasks_by_lane.items():
            print(f"\nLane: {lane}")
            print("-" * (len(lane) + 6))
            for task in tasks:
                print(f"Title: {task.title}")
                if task.tags:
                    print(f"Tags: {', '.join(task.tags)}")
                print("-" * 40)

    if args.split_tasks:
        task_manager.split_tasks()
        print("Tasks have been split and originals moved to Trash")

    if args.add_lane:
        task_manager.add_lane(args.add_lane)
        print(f"Added new lane: {args.add_lane}")

    if args.csv_create_tasks:
        if not os.path.exists(args.csv_create_tasks):
            print(f"Error: CSV file '{args.csv_create_tasks}' does not exist")
            sys.exit(1)
        task_manager.create_tasks_from_csv(args.csv_create_tasks)
        print(f"Created tasks from CSV file: {args.csv_create_tasks}")

    if args.empty_trash:
        task_manager.empty_trash()

    if args.change_lane:
        task_title, new_lane = args.change_lane
        task_manager.change_lane(task_title, new_lane)

if __name__ == '__main__':
    main() 