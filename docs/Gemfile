source "https://rubygems.org"

# For GitHub Pages, use specific versions
gem "webrick"
gem "csv"     # Required for Ruby 3.4+
gem "logger"  # Required for Ruby 3.4+
gem "base64"  # Required for Ruby 3.4+
gem "bigdecimal" # Required for Ruby 3.4+

group :jekyll_plugins do
  gem "github-pages"          # Moved here
  gem "jekyll-remote-theme"   # If needed by the new theme
  gem "jekyll-theme-leap-day" # Or the latest version
  gem "jekyll-feed"
  gem "jekyll-seo-tag"        # Unless the theme handles this
end

# Windows and JRuby does not include zoneinfo files, so bundle the tzinfo-data gem
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end
