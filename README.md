# SHiFT-Code-Watcher

## Version 1.0

[![Python CI](https://github.com/klept0/SHiFT-Code-Watcher/actions/workflows/python-ci.yml/badge.svg)](https://github.com/klept0/SHiFT-Code-Watcher/actions/workflows/python-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python automation tool that monitors multiple sources for new SHiFT codes for Borderlands 4, automatically attempts to redeem them, and sends notifications for updates and results.

**Disclaimer:** I'm not affiliated with Gearbox Software at all - just a passionate fan who built this so I don't miss SHiFT code drops while trying to adult responsibly. Because who has time to manually check websites when you could be automating your loot addiction?

## ⚠️ Security Notice

This tool requires storing SHiFT login credentials and session cookies. Use at your own risk and ensure you understand the security implications. The tool is provided "as is" without any warranties.

**Security Features:**

- Optional cookie encryption using Fernet symmetric encryption
- Secure key derivation using PBKDF2 with 100,000 iterations
- Environment variable-based configuration for sensitive data

## Features

- Scrapes multiple official and community sources for SHiFT codes.
- Handles login and session management with Playwright for manual cookie refresh.
- Rate-limited automation to mimic human-like code redemption timing.
- Sends notifications using Apprise (supports Telegram, etc.).
- Real-time console updates with colored status output and progress bar.
- Modular, extensible Python codebase.

## Requirements

- Python 3.10+
- Playwright (with installed browsers)
- Requests, Colorama, tqdm, python-dotenv, apprise Python packages

## Installation

Clone this repository:

```bash
git clone https://github.com/klept0/SHiFT-Code-Watcher.git
cd SHiFT-Code-Watcher
```

Create a Python virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright browsers:

```bash
playwright install
```

Copy `.env.example` to `.env` and update your APPRISE_URL for notifications:

```bash
cp .env.example .env
# Then edit .env to add your Apprise URL
```

## Usage

Run the watcher script to start monitoring and redeeming codes:

```bash
python shift_watcher.py
```

The script runs continuously, checking for new codes every hour by default, and provides live progress updates.

## Configuration

- Modify `SCAN_INTERVAL` in `config.py` to change how often the script runs.
- Add or remove URLs in the `SOURCES` list in `config.py` to customize code sources.
- Store login session cookies securely; the script uses Playwright to refresh cookies when needed.
- Configure Apprise notification endpoints via the `.env` file.

## Troubleshooting

### Common Issues

- **Login fails**: Ensure your SHiFT account credentials are correct and cookies are fresh
- **No codes found**: Check your internet connection and verify the sources are accessible
- **Playwright errors**: Run `playwright install` to ensure browsers are installed
- **Rate limiting**: The tool includes built-in delays; avoid running multiple instances

### Getting Help

- Check the console output for detailed error messages
- Verify your `.env` file contains the correct `APPRISE_URL`
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## Contributing

Contributions are welcome! Please:

- Fork the repository.
- Create feature branches.
- Submit pull requests with clear descriptions.
- Follow the existing code style and modular structure.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
