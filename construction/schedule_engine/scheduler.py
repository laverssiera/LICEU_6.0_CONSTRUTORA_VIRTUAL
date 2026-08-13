from .task import Task

class Scheduler:
    def __init__(self, tasks):
        self.tasks = {t.id: t for t in tasks}

    def calculate(self):
        for task in self.tasks.values():
            if not task.dependencies:
                task.start_day = 0
            else:
                task.start_day = max(
                    self.tasks[dep].end_day for dep in task.dependencies
                )
            task.end_day = task.start_day + task.duration_days
        return list(self.tasks.values())
