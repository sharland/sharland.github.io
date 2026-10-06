@echo off
rem Create, check and publish notes and work entries.
rem   site                     list the commands
rem   site new --title "..."   start a draft note
rem   site check               check everything
rem   site check my-slug       is this note ready to publish?
rem   site publish my-slug     mark it published (does not commit or push)
rem Preview with: serve   (or: serve --unpublished   to see drafts)

cd /d "%~dp0"
python tools\sitetool.py %*
if "%~1"=="" pause
