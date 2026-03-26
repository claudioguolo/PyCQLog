# Contributing to PyCQLog

Thanks for your interest in contributing to `PyCQLog`.

`PyCQLog` exists because there is real demand for a Linux amateur radio logging application built in a more modern language and with a codebase that welcomes more volunteers into shared development. Contributions are part of the project's core purpose, not an afterthought.

The project is open to everyone who wants to participate by developing features, improving documentation, testing workflows, using the application in real operation, reporting bugs, suggesting ideas, reviewing code, or helping maintain the project over time.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Run the application locally:

```bash
./pycqlog
```

Run checks:

```bash
python3 -m compileall src tests
pytest
```

## Contribution Guidelines

- Keep changes focused and easy to review.
- Prefer small pull requests over large mixed changes.
- Update documentation when behavior changes.
- Avoid committing local databases, configuration files, or credentials.
- Preserve the existing layered architecture: `domain`, `application`, `infrastructure`, `interfaces`.

## Reporting Issues

Bug reports, usability feedback, and operational notes from real use are all valuable contributions.

When opening an issue, include:

- what you expected to happen
- what actually happened
- steps to reproduce
- OS and desktop environment
- Python version
- whether the issue involves PyQt, ADIF import/export, or integration with external software
