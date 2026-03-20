# Agent Repository Updater

A Python automation tool that maintains a local repository of **Qualys Cloud Agent** installers by checking for new versions via the Qualys API, downloading updates, and validating binary integrity using cryptographic checksums.

## Features

- **Automatic version detection** — only downloads when a new version is available
- **Multi-platform support** — Windows, macOS (Intel & Apple Silicon), Linux (RPM & DEB)
- **Hash validation** — verifies binary integrity using SHA-256/384/512
- **Audit logging** — timestamped log of all operations
- **Debug mode** — optional verbose logging

## Supported Platforms

| Platform       | Architecture | Extension |
|----------------|--------------|-----------|
| Windows        | x86_64       | `.exe`    |
| macOS          | x64          | `.pkg`    |
| macOS          | M1 ARM64     | `.pkg`    |
| Linux          | x64          | `.rpm`    |
| Linux (Ubuntu) | x64          | `.deb`    |

## Setup

1. **Clone the repository** and create a virtual environment:

   ```bash
   git clone <repo-url>
   cd agent_repository_updater
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your Qualys credentials:

   ```
   QUALYS_USERNAME=your_username
   QUALYS_PASSWORD=your_password
   QUALYS_URL=https://qualysapi.qualys.eu
   REPO_DIRECTORY=repo
   LOG_FILE=update_agents.log
   DEBUG=False
   ```

## Usage

```bash
python update_agents.py
```

The script will:

1. Query the Qualys API for the latest agent version for each platform
2. Compare against locally stored version metadata
3. Download and validate any new binaries
4. Save binaries and metadata to the `repo/` directory

## Repository Structure

After running, the `repo/` directory will contain:

```
repo/
├── Qualys_Agent_WINDOWS_X_86_64.exe
├── Qualys_Agent_MACOSX_X_64.pkg
├── Qualys_Agent_MACOSX_M_1_ARM_64.pkg
├── Qualys_Agent_LINUX_X_64.rpm
├── Qualys_Agent_LINUX_UBUNTU_X_64.deb
└── info/
    ├── WINDOWS_X_86_64_info.json
    ├── MACOSX_X_64_info.json
    ├── MACOSX_M_1_ARM_64_info.json
    ├── LINUX_X_64_info.json
    └── LINUX_UBUNTU_X_64_info.json
```

## Logging

All operations are logged to `update_agents.log`:

```
[17/03/2026, 17:08:39] Updated WINDOWS/X_86_64 : File Qualys_Agent_WINDOWS_X_86_64.exe, version 6.4.0.397
[17/03/2026, 17:08:49] Skipped LINUX_UBUNTU/X_64, no new version available
```

Enable `DEBUG=True` in `.env` for verbose output.

## Dependencies

- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable management
- [requests](https://pypi.org/project/requests/) — HTTP client
- [xmltodict](https://pypi.org/project/xmltodict/) — XML response parsing
