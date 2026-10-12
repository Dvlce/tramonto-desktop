# Tramonto Desktop

A standalone notebook for **Windows 64 bit**, **macOS Apple Silicon** and **macOS Intel**. It runs on your computer, stores your notebooks locally and works offline. **No AI, no models, no Ollama and no Raspberry connection.**

[Download the installers](https://github.com/Dvlce/tramonto-desktop/releases/latest).

Use the Windows `.exe` installer or the macOS `.dmg` matching your processor. The app includes its web editor, Python runtime and ngspice circuit simulator. No system Python, Node.js or account is required. Windows and macOS builds are currently unsigned; macOS builds are not notarized. Your operating system may require its standard confirmation for downloaded applications.

The notebook includes selected text sizes, transparent formulas, point charts, movable images, electronic schematics and an adjustable oscilloscope with Fourier analysis. The network editor provides hardware models, physical port choices and saved device CLI notes; its IPv4 simulation is educational and does not execute Cisco IOS or contact physical equipment.

Your data lives in the app's standard user-data folder. Open it with **Quaderno → Apri cartella dei dati**. Installing a newer version keeps the data. Use **Backup di tutti i quaderni** to save a consistent SQLite copy; per-notebook exports include images and can be imported through the editor. The app does not sync with the Raspberry.

## Where to work

- **This repository:** desktop launcher, native packaging, updates, offline notebook server, installer tests and release workflows.
- **[alba-tramonto](https://github.com/Dvlce/alba-tramonto):** shared notebook web UI, circuit/network validation and Android app. Make shared editor fixes there first, then refresh this repo with `python scripts/sync_portal.py ../alba-tramonto`.
- `portal-manifest.json` records the exact shared source revision and every bundled public asset hash. Never copy `.env`, notebook databases, credentials, screenshots of private notes or model files.

## Development

Node.js 22+, Python 3.12+ and ngspice are needed **only to develop/build**:

```sh
npm ci
python -m pip install -r backend/requirements.txt
python scripts/sync_portal.py ../alba-tramonto
# macOS: compile the pinned simulator without extra system libraries
python scripts/build_spice.py
# Windows: bundle the verified upstream ngspice executable
# python scripts/bundle_spice.py /path/to/ngspice.exe
python scripts/build_backend.py
npm start
npm test
npm run build
```

Build macOS apps on macOS and Windows installers on Windows. The release workflow checks the frozen backend, offline persistence and actual circuit output before publishing installers and SHA-256 checksums. Native signing can be added later without changing the notebook format. Updates are checked explicitly from the app menu and installed from this repository's releases.

To restore a full backup, close the app, keep a copy of the current data folder, then replace `notebook/notebook.sqlite3` with your backup and reopen Tramonto. Per-notebook exports can be imported directly from the notebook UI.
