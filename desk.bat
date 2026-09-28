@echo off
REM Convenience wrapper so `desk <command>` works from the praman folder instead of
REM `python desk\cli.py <command>`. Resolves relative to this file's own location (%~dp0), so it
REM still works even if invoked by a full path from elsewhere -- not just from this exact folder.
python "%~dp0desk\cli.py" %*
