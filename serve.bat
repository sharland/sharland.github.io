@echo off
rem Local preview of the site. Double-click, or run "serve" from a terminal here.
rem Rebuilds and refreshes the browser on every save. Stop with Ctrl+C.
rem Extra options pass straight through, e.g.:  serve --unpublished   (shows drafts)

cd /d "%~dp0"

where bundle >nul 2>nul
if errorlevel 1 (
  echo Ruby is not on the PATH. See "Previewing" in README.md.
  pause
  exit /b 1
)

call bundle check >nul 2>nul
if errorlevel 1 (
  echo Gems are missing or out of date. Installing...
  call bundle install || (pause & exit /b 1)
)

call bundle exec jekyll serve --livereload --open-url %*
if errorlevel 1 pause
