#!/usr/bin/env python3
"""MediaDL - Universal Media Downloader.

Entry point for the application.
Run: python run.py
"""

from mediadl.app import MediaDLApp


def main():
    """Launch the MediaDL TUI application."""
    app = MediaDLApp()
    app.run()


if __name__ == "__main__":
    main()
