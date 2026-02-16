Image Flow is a professional desktop application for organizing and tagging large image collections.
Built with Python and PyQt6, it provides:

AI‑powered scene detection and auto‑tagging (using ONNX models)

Portable catalogs (.iocat files) that can be shared via cloud storage – no server required

Persistent tags & custom filenames – saved instantly and synced across teams

Explorer‑style gallery with dynamic grid layout and instant search by tag/filename

Undo/redo history for all metadata changes

Multi‑user ready – multiple people can edit the same catalog (last‑write‑wins)

Perfect for photographers, designers, and teams who need to find images fast without complex DAM systems.#

## Installation

### Prerequisites
- Python 3.12 or higher (3.13 recommended)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/image-generator-pro.git
   cd image-generator-pro

2. ```bash 
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install Dependencies:
   ```bash
   pip install -r requirements.txt

4. Run application:
   ```bash
   python launcher.py


## 🔁 5. (Optional) Create a `setup.py` or `pyproject.toml`

For a more professional distribution, you can add a `setup.py` or `pyproject.toml` with entry points. This allows users to install your app as a package. Here's a minimal `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "image-generator-pro"
version = "1.0.0"
description = "AI-powered image organizer"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "Pillow>=9.0.0",
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "transformers>=4.30.0",
    "qtawesome>=1.3.0",
    "PyQt6>=6.5.0",
    "pyinstaller>=6.0.0",
    "qdarktheme @ git+https://github.com/TsynkPavel/PyQtDarkTheme.git@tsynk/support_python_312_plus_versions"
]

[project.scripts]
image-organizer = "src.gui.__main__:main"