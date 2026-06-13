import sys
from cx_Freeze import setup, Executable
from mediadl import __version__

# Packages and files to include
build_exe_options = {
    "packages": ["textual", "yt_dlp", "mediadl", "asyncio", "rich", "rich._unicode_data"],
    "excludes": ["tkinter"],
    "include_files": [
        ("mediadl/styles.tcss", "lib/mediadl/styles.tcss"),
    ],
}

# Shortcut table definition for MSI installation
# Columns: Shortcut, Directory_, Name, Component_, Target, Arguments, Description, Hotkey, Icon, IconIndex, ShowCmd, WkDir
shortcut_table = [
    (
        "DesktopShortcut",          # Shortcut ID
        "DesktopFolder",            # Directory where shortcut is placed (Desktop)
        "MediaDL",                  # Name of the shortcut
        "TARGETDIR",                # Component_
        "[TARGETDIR]MediaDL.exe",   # Target executable path
        None,                       # Arguments
        "Tải video và âm thanh từ mọi website", # Description
        None,                       # Hotkey
        None,                       # Icon
        None,                       # IconIndex
        None,                       # ShowCmd
        "TARGETDIR"                 # Working directory (Start in)
    ),
    (
        "StartMenuShortcut",        # Shortcut ID
        "ProgramMenuFolder",        # Directory where shortcut is placed (Start Menu)
        "MediaDL",                  # Name of the shortcut
        "TARGETDIR",                # Component_
        "[TARGETDIR]MediaDL.exe",   # Target executable path
        None,                       # Arguments
        "Tải video và âm thanh từ mọi website", # Description
        None,                       # Hotkey
        None,                       # Icon
        None,                       # IconIndex
        None,                       # ShowCmd
        "TARGETDIR"                 # Working directory (Start in)
    )
]

bdist_msi_options = {
    "upgrade_code": "{7F7B3A43-60CF-45AC-A347-1F0848CB80C8}",
    "add_to_path": False,
    "initial_target_dir": "[ProgramFilesFolder]\\MediaDL",
    "data": {"Shortcut": shortcut_table},
}

# TUI applications require a console (base = None)
base = None

setup(
    name="MediaDL",
    version=__version__,
    author="MediaDL Team",
    description="Universal Media Downloader TUI",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=[
        Executable(
            "run.py",
            base=base,
            target_name="MediaDL.exe",
        )
    ],
)
