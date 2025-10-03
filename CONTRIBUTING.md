# Contributing to DotCanvas

Thank you for your interest in improving DotCanvas! This guide explains how we collaborate through pull requests and walks you through the process of adding new canvas views.

## Table of Contents
- [Pull Request Workflow](#pull-request-workflow)
  - [1. Set up your environment](#1-set-up-your-environment)
  - [2. Create a feature branch](#2-create-a-feature-branch)
  - [3. Make and document your changes](#3-make-and-document-your-changes)
  - [4. Run quality checks](#4-run-quality-checks)
  - [5. Push and open your pull request](#5-push-and-open-your-pull-request)
  - [6. Respond to review feedback](#6-respond-to-review-feedback)
- [Creating a New View](#creating-a-new-view)
  - [1. Copy the template](#1-copy-the-template)
  - [2. Rename the class and type identifier](#2-rename-the-class-and-type-identifier)
  - [3. Define configuration parameters](#3-define-configuration-parameters)
  - [4. Implement the draw method](#4-implement-the-draw-method)
  - [5. Export the view module](#5-export-the-view-module)
  - [6. Add configuration and tests](#6-add-configuration-and-tests)

---

## Pull Request Workflow

### 1. Set up your environment
1. Clone the repository and install the Python dependencies:
   ```bash
   uv sync
   ```
2. Activate the virtual environment created by `uv`:
   ```bash
   source .venv/bin/activate
   ```

### 2. Create a feature branch
1. Ensure your local `main` branch is up to date:
   ```bash
   git checkout main
   git pull origin main
   ```
2. Create a descriptively named feature branch:
   ```bash
   git checkout -b feature/<short-description>
   ```

### 3. Make and document your changes
- Commit early and often with clear messages describing the intent of each change.
- Update or add documentation alongside code changes when it clarifies how to use or extend the project.

### 4. Run quality checks
Before opening a pull request, make sure the project still works.
1. Run automated tests (add them if your change introduces new functionality):
   ```bash
   uv run python -m pytest
   ```
2. For changes that affect rendering logic, manually exercise the canvas server if possible to confirm the updated views behave as expected:
   ```bash
   uv run python server.py
   ```

### 5. Push and open your pull request
1. Push your feature branch:
   ```bash
   git push -u origin feature/<short-description>
   ```
2. Open a pull request that:
   - Summarizes the user-facing impact of the change.
   - Lists the tests you ran.
   - References any related issues.

### 6. Respond to review feedback
- Make any requested changes on the same feature branch.
- Reply to review comments to explain the updates you made.
- Keep your branch up to date with `main` by rebasing or merging as requested by reviewers.

---

## Creating a New View
Views render shapes, text, or other visuals onto a canvas. Each view must subclass `_BaseView` and implement a static `draw` method that accepts a `PIL.ImageDraw` instance plus a configuration dictionary.

### 1. Copy the template
Start from the template in [`canvas/views/_new_view_template.py`](canvas/views/_new_view_template.py). Copy the file to a new module within the same directory. For example, to create a banner view:
```bash
cp canvas/views/_new_view_template.py canvas/views/banner.py
```

### 2. Rename the class and type identifier
Inside your new module:
- Rename the class to something descriptive (e.g., `BannerView`).
- Update the `TYPE` constant to a unique string. This identifier is how `_BaseCanvas` discovers and instantiates your view. Discovery happens automatically through [`_BaseCanvas.find_available_views`](canvas/_base_canvas.py), which inspects modules in `canvas.views`, so make sure the file name and class name match your new view.

### 3. Define configuration parameters
Extend `_BaseView.DEFAULT_PARAMS` to describe any additional configuration keys your view needs. Each entry’s value should be a human-readable description of the parameter, similar to existing views such as [`CircleView`](canvas/views/circle.py).

```python
PARAMS = {
    **_BaseView.DEFAULT_PARAMS,
    "title": "Text displayed inside the banner",
    "background_color": "Fill color for the banner",
}
```

### 4. Implement the draw method
Implement a `@staticmethod draw(draw: ImageDraw.ImageDraw, config: dict) -> None` that uses the provided `PIL.ImageDraw` object to render your view. You can look at [`CircleView.draw`](canvas/views/circle.py) and other existing views for reference. Validate inputs from `config` and provide sensible defaults.

### 5. Export the view module
If you want the view to be importable via `canvas.views`, add an import in [`canvas/views/__init__.py`](canvas/views/__init__.py):
```python
from .banner import BannerView

__all__ = ["BannerView"]
```
This step is optional for discovery (the canvas loader imports modules dynamically), but it makes the view easier to access from other code.

### 6. Add configuration and tests
- Update any canvas configuration files or builders that should use the new view type so that it becomes accessible to users.
- Add or update tests to cover the rendering logic when feasible. When direct image comparison is impractical, test that your view’s configuration builder returns the expected dictionary structure.
- Document the new view in user-facing guides or examples if it introduces new capabilities.

Once you have verified your changes locally, follow the pull request workflow above to submit your contribution.
