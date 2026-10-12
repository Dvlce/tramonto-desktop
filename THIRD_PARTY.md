# Third-party software

Tramonto Desktop uses Electron (MIT), electron-builder (MIT), Python (PSF), aiohttp (Apache-2.0), cryptography (Apache-2.0/BSD), PyInstaller (GPL with its distribution exception), and ngspice (BSD-style licensing; upstream notices included in the simulator source package). The shared notebook assets retain their upstream vendor licenses, including KaTeX, MathLive, DOMPurify, html2canvas, OpenType.js and the bundled fonts.

The circuit importer contains an altered implementation of Mark Adler's PKWare DCL decoder; its complete notice is retained in `backend/source/lab.py`. No Cisco artwork, binaries or IOS code are distributed.

Sources: https://github.com/Dvlce/alba-tramonto and https://ngspice.sourceforge.io/.
