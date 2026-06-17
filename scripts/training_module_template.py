"""Shared module step template for training task generation."""

# step_key -> (title, phase, days, assignee or None for user input, depends_on step_keys)
MODULE_STEPS = [
    ("1.1", "Assign the training", "content", 0, "Priscilla", []),
    ("1.2", "Populate the word document", "content", 5, "Priscilla", ["1.1"]),
    ("1.3", "Review and comment", "content", 1, "Priscilla", ["1.2"]),
    ("1.4", "Update to word", "content", 1, "Priscilla", ["1.2"]),
    ("1.5", "Approval of word document", "content", 3, None, ["1.3", "1.4"]),
    ("2.1", "Design slides", "development", 1, "Priscilla", ["1.5"]),
    ("2.2", "Input slide content", "development", 0.5, "Priscilla", ["2.1"]),
    ("2.3", "Incorporate voice-over", "development", 0.5, "Priscilla", ["2.2"]),
    ("2.4", "Functional review", "development", 1, "Priscilla", ["2.3"]),
    ("2.5", "Design review", "development", 1, "Priscilla", ["2.3"]),
    ("2.6", "Update", "development", 1, "Priscilla", ["2.3"]),
    ("2.7", "Submit for approval", "development", 1, "Priscilla", ["2.4", "2.5", "2.6"]),
    ("2.8", "Approval", "development", 5, None, ["2.7"]),
    ("3.1", "Save final files to dropbox", "upload", 1, "Priscilla", ["2.8"]),
    ("3.2", "Upload to platform", "upload", 1, "Priscilla", ["2.8"]),
    ("3.3", "Go live on platform", "upload", 1, "Priscilla", ["2.8"]),
]

PARALLEL_GROUPS = {
    "1.3": "content-review",
    "1.4": "content-review",
    "2.4": "dev-qa",
    "2.5": "dev-qa",
    "2.6": "dev-qa",
    "3.1": "upload",
    "3.2": "upload",
    "3.3": "upload",
}

STEP_OFFSET = {
    "1.1": 1,
    "1.2": 2,
    "1.3": 3,
    "1.4": 4,
    "1.5": 5,
    "2.1": 11,
    "2.2": 12,
    "2.3": 13,
    "2.4": 14,
    "2.5": 15,
    "2.6": 16,
    "2.7": 17,
    "2.8": 18,
    "3.1": 21,
    "3.2": 22,
    "3.3": 23,
}


def task_id(module_index: int, step_key: str) -> int:
    return module_index * 100 + STEP_OFFSET[step_key]


def step_sort_key(step_id: str) -> tuple:
    parts = step_id.split(".")
    return (int(parts[0]), int(parts[1]))
