import os
import sys
import shutil
import subprocess
import platform

def check_requirements():
    """Check if PyInstaller is installed, if not install it."""
    try:
        import PyInstaller
        print("PyInstaller already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully.")

def build_executable():
    """Build the executable using PyInstaller."""
    print("\n=== Building JARVIS-IV Executable ===\n")
    
    # Determine the system
    system = platform.system()
    print(f"Building for {system} platform...")
    
    # Create spec file with custom options
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Add data files
added_files = [
    ('ui', 'ui'),
    ('backend', 'backend'),
    ('history', 'history'),
    ('README.md', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['pyttsx3.drivers', 'pyttsx3.drivers.sapi5', 'google.generativeai.types'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JARVIS-IV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ui/favicon.ico' if os.path.exists('ui/favicon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JARVIS-IV',
)
"""

    # Write the spec file
    with open('JARVIS-IV.spec', 'w') as f:
        f.write(spec_content)
    
    # Create a temporary favicon if not exists
    if not os.path.exists('ui/favicon.ico'):
        os.makedirs('ui', exist_ok=True)
        try:
            # Create a simple empty icon file to avoid PyInstaller errors
            # This will be replaced by a proper icon in a real app
            with open('ui/favicon.ico', 'wb') as f:
                f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00 \x00h\x04\x00\x00\x16\x00\x00\x00')
            print("Created temporary favicon for building.")
        except:
            print("Could not create temporary favicon, continuing without icon.")
    
    # Build using the spec file
    print("\nBuilding executable... This may take several minutes.")
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "JARVIS-IV.spec", "--clean"])
    
    print("\n=== Build Complete ===")
    print(f"Executable is located in the 'dist/JARVIS-IV' directory.")
    
    # Additional instructions based on platform
    if system == "Windows":
        print("\nTo run the application, execute 'dist/JARVIS-IV/JARVIS-IV.exe'")
    elif system == "Linux":
        print("\nTo run the application, execute 'dist/JARVIS-IV/JARVIS-IV'")
    elif system == "Darwin":  # macOS
        print("\nTo run the application, execute 'dist/JARVIS-IV/JARVIS-IV'")

if __name__ == "__main__":
    check_requirements()
    build_executable()
