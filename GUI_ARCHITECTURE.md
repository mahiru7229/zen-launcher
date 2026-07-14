# GUI Architecture — SRP map

```text
launcher.py
└── MainWindow
    ├── SidebarWidget
    ├── QStackedWidget
    │   ├── HomePage
    │   ├── AccountPage
    │   ├── InstancesPage
    │   ├── InstanceSettingsPage
    │   ├── LauncherSettingsPage
    │   ├── LogsPage
    │   └── AboutPage
    ├── RightPanelWidget
    └── LaunchControlWidget
```

## Responsibilities

| Layer | Responsibility |
|---|---|
| `main_window_2.py` | Assemble the shell and connect signals only |
| `pages/` | Render a screen, collect input, emit user intent |
| `controllers/` | Validate input and call public MCW Core APIs |
| `task_runner.py` | Own `QThread`, worker lifetime, busy state, and task results |
| `widget/` | Reusable visual components with local rendering state |
| `style.py` | One centralized QSS theme |
| `config.py` | App constants and resource paths |

## Data flow

```text
User action
→ Page signal
→ Controller validation
→ Public Core API
→ TaskRunner when blocking work is required
→ Controller result signal
→ Page/widget render method
```

The GUI does not read launcher JSON or the account database directly. Instance settings are loaded and saved through `SettingsManager`; launches go through `MinecraftExecutor.run()`.
