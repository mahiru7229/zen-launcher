# Zen Launcher

A lightweight Minecraft Launcher written in Python.

> ⚠️ This project is currently under active development.

> This document was created with assistance from ChatGPT.
---

## Features

### Minecraft

- Download Minecraft versions
- Download libraries
- Download assets
- Launch Minecraft
- Offline authentication

### Instance System

- Create instance
- Rename instance
- Delete instance
- Clone instance
- Per-instance metadata
- Per-instance settings

### Package System

- Export instance to `.mcwpack`
- Import `.mcwpack`
- Package validation

### Java

- Detect Java installation
- Custom JVM arguments
- Per-instance memory settings

---

## Project Structure

```text
src/
├── core/
│   ├── instance/
│   ├── java/
│   ├── minecraft/
│   ├── network/
│   └── package/
│
├── models/
│   ├── instance/
│   ├── java/
│   ├── minecraft/
│   └── package/
```

---

## Package Format

Zen Launcher uses its own package format:

```
.mcwpack
```

Example:

```text
package.mcwpack
│
├── package.json
├── instance.json
├── settings.json
├── mods/
├── resourcepacks/
└── ...
```

---

## Current Status

Current version:

```
v0.2.3-alpha
```

Implemented:

- Java Runtime
- Download System
- Launch Pipeline
- Instance System
- Package System
- Settings System

In Progress:

- Microsoft Authentication
- GUI
- Fabric / Forge support

---

## Requirements

- Python 3.12+
- Java 17+

Install dependencies

```bash
pip install -r requirements.txt
```

Run

```bash
python launcher.py
```

---

## Roadmap

### v0.3

- Microsoft Authentication
- Multiple Accounts
- Account Manager

### v0.4

- Fabric
- Forge
- NeoForge
- Quilt

### v0.5

- GUI
- Better UX
- Theme Support

---

## License

MIT License