from kivy_deps import sdl2, glew
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['..\\main.py'],
             pathex=[],
             binaries=[],
             datas=[('..\\help\\*.*', '.\\help\\'), ('..\\data\\*.*', '.\\data\\'), ('..\\snuclipboardmanager.kv', '.'), ('..\\icon.ico', '.'), ('..\\Readme.md', '.')],
             hiddenimports=['plyer.platforms.win.filechooser'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['beautifulsoup4', 'Pillow', 'ffpyplayer', 'numpy', 'PIL', 'cv2', 'scipy', 'docutils', 'kivy-deps.gstreamer', 'kivy_deps.gstreamer', 'gstplayer', 'cryptography'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Snu Clipboard Manager',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='..\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='Snu Clipboard Manager')
