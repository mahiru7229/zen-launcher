# MCW Launcher

> A lightweight, modular, and open-source Minecraft Launcher built with Python.

> ⚠️ This project is currently in **Pre-Beta**.

---

## Features

### Minecraft

- ✅ Support **all** Minecraft versions.
- ✅ Automatic Java selection
- ✅ Vanilla launcher support
- ✅ Progress callback system

### Instance

- ✅ Create
- ✅ Rename
- ✅ Clone
- ✅ Delete
- ✅ Import / Export (`.mcwpack`)

### Account

- ✅ Offline Authentication
- 🚧 Microsoft Authentication (In Progress)

### Core

- ✅ Modular architecture
- ✅ Shared HTTP client
- ✅ Progress API
- ✅ Unit tests
- ✅ GitHub Actions CI

---

## Project Structure

```text
launcher.py
│
├── src/
│   ├── core/
│   ├── gui/
│   ├── models/
│   └── ...
│
├── docs/
├── test/
└── ...
```

---

## Build

### Run

```bash
python launcher.py
```

### Build EXE

```bash
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --clean ^
    launcher.py
```

---

## Documentation

| Document | Description |
|----------|-------------|
| docs/gui-api.en.md | GUI API Documentation |
| docs/gui-api.vi.md | Hướng dẫn phát triển GUI |

---

## Testing

Run all tests

```bash
pytest
```

GitHub Actions automatically runs all tests on every push and pull request.

---

## Roadmap

### Beta

- Microsoft Authentication
- Official GUI
- Fabric
- Forge
- NeoForge

### Future

- Theme System
- Plugin Support
- Multi-language GUI

---


## Project Status

| Component | Status |
|-----------|--------|
| Core | ✅ Stable |
| GUI | 🚧 Experimental |
| Offline Authentication | ✅ Stable |
| Microsoft Authentication | 🚧 In Progress |
| Instance System | ✅ Stable |
| Mod Loader | ⏳ Planned |
| Unit Tests | ✅ Core Covered |
| GitHub Actions | ✅ Enabled |

---

## License

MIT License