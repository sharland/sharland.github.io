source "https://rubygems.org"

# Pins Jekyll and every plugin to the exact versions GitHub Pages runs,
# so a local build is a faithful preview of the deployed site.
gem "github-pages", group: :jekyll_plugins

# Windows has no system timezone database, so Jekyll needs this one to honour
# `timezone:` in _config.yml. Not installed on any other platform.
gem "tzinfo-data", platforms: %i[windows jruby]

# Lets `jekyll serve` watch for file changes through the Windows API instead
# of polling the folder. Windows only.
gem "wdm", ">= 0.1.0", platforms: %i[windows]
