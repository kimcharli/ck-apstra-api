# Documentation

This documentation is built using Jekyll and can be tested locally before deployment.

## Prerequisites

1. Install Ruby (2.7.0 or higher recommended)
   ```bash
   # For Ubuntu/Debian
   sudo apt-get install ruby ruby-dev build-essential

   # For macOS (using Homebrew)
   brew install ruby
   ```

2. Install Bundler
   ```bash
   gem install bundler
   ```

## Local Setup

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd docs
   ```

2. Install dependencies
   ```bash
   bundle install
   ```

3. Start the local server
   ```bash
   bundle exec jekyll serve
   ```

4. View the documentation
   - Open your browser and navigate to `http://localhost:4000`
   - Changes to the files will automatically rebuild the site

## Project Structure

```
docs/
├── assets/
│ └── css/
│ └── styles.css # Global styles including command-block formatting
├── notes/ # Documentation markdown files
├── config.yml # Jekyll configuration
├── Gemfile # Ruby dependencies
└── README.md # This file
```

## Writing Guidelines

- Use `<div class="command-block">` for command line examples
- Use `<span class="snapshot-name">` for dynamic values in commands
- Keep styles in the central `assets/css/styles.css` file

## Common Issues

1. Port already in use
   ```bash
   # Kill the process using port 4000
   lsof -ti:4000 | xargs kill -9
   ```

2. Bundle install fails
   ```bash
   # Update bundler
   gem update bundler
   
   # Clear and reinstall dependencies
   rm Gemfile.lock
   bundle install
   ```

## Gemfile

```
source "https://rubygems.org"

gem "jekyll", "~> 4.3.2"
gem "webrick", "~> 1.8"
gem "csv"     # Required for Ruby 3.4+
gem "logger"  # Required for Ruby 3.4+

group :jekyll_plugins do
  gem "jekyll-feed", "~> 0.12"
  gem "jekyll-seo-tag", "~> 2.8"
end

# Windows and JRuby does not include zoneinfo files, so bundle the tzinfo-data gem
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end
```
