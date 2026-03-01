# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Image-to-DXF converter: a Python pipeline that converts PNG/JPEG images (line art or photographs) into DXF files for CNC machining.

## Commands

```bash
# Activate virtualenv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run all tests
pytest

# Run a single test file
pytest tests/test_classify.py

# Run a specific test
pytest tests/test_classify.py::test_classify_lineart -v

# Regenerate test fixture images
python tests/create_fixtures.py
```

## Architecture

The pipeline flows linearly through five modules in `backend/`:

```
Input Image → classify → preprocess → trace → bezier flatten → dxf_writer → DXF bytes
```

1. **classify.py** — Histogram heuristic classifies images as `ImageType.LINE_ART` or `ImageType.PHOTO` (>70% pixels near black/white = line art)
2. **preprocess.py** — Converts to binary bitmap using type-specific strategies (Otsu for line art, adaptive threshold for photos). Output is always a 2D numpy array with values 0 or 255.
3. **trace.py** — Wraps Potrace library to produce vector paths. Defines the shared data models: `Point`, `BezierSegment`, `TracedPath` (dataclasses). Image is inverted before tracing (Potrace expects nonzero=filled).
4. **bezier.py** — Recursive De Casteljau subdivision converts Bezier curves to polylines. Default tolerance 0.1mm (CNC-appropriate).
5. **dxf_writer.py** — Writes polylines as LWPOLYLINE entities via ezdxf. Units are millimeters, default scale 1 pixel = 1mm.

## Key Dependencies

- **opencv-python-headless** for image processing
- **potracer** for bitmap-to-vector tracing
- **ezdxf** for DXF file generation
- **fastapi/uvicorn** declared but API layer not yet implemented

## Conventions

- Data models are dataclasses in `trace.py` — other modules import from there
- All functions use full type annotations
- Images are represented as numpy arrays (uint8)
- Coordinates are `tuple[float, float]` in pixel/mm space
- Commit messages use `feat:` / `fix:` prefixes
- Tests use pytest; one test file per backend module

## Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration and parallelizable tasks to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

## Architecture Principles

- **DRY Principle** Don't repeat yourself. Avoid code duplication.
- **KISS Principle** Keep it simple, stupid. Avoid over-engineering.
- **YAGNI Principle** You ain't gonna need this. Avoid premature optimization.
- **SOLID Principles** Apply SOLID principles to the codebase.

## Core Principles

- **Simplicity First** Make every change as simple as possible. Impact minimal code.
- **No Laziness** Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact** Changes should only touch what's necessary. Avoid introducing new bugs.
- **Security First** Security is everyone's responsibility.
