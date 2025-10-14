# SHiFT-Code-Watcher

A Python automation tool that monitors multiple sources for new SHiFT codes for Borderlands 4, automatically attempts to redeem them, and sends notifications for updates and results.

**Disclaimer:** I'm not affiliated with Gearbox Software at all - just a passionate fan who built this so I don't miss SHiFT code drops while trying to adult responsibly. Because who has time to manually check websites when you could be automating your loot addiction?

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
cd shiftwatcher
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

## Contributing

Contributions are welcome! Please:

- Fork the repository.
- Create feature branches.
- Submit pull requests with clear descriptions.
- Follow the existing code style and modular structure.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
