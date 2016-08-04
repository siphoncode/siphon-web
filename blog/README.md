# Based on: https://github.com/kippt/jekyll-incorporated

## Prequisites

Install rbenv:

```
brew update
brew install rbenv ruby-build
```

Paste this into your `.bash_profile`:

```
eval "$(rbenv init -)"
```

Install Ruby 1.9.3:

```
rbenv install 1.9.3-p551
```

Install bundler and run it:

```
gem install bundler
cd /path/to/blog
bundle install
```

## Making changes / publishing

Test locally:

```
cd /path/to/blog
./run-local.sh
```

The blog is visible at http://localhost:4000/blog/

When it looks fine, do the standard deploy to the staging/production branches.

## Deployment

The final blog gets generated in the `Dockerfile` using this command:

```
rake site:publish
```

## Configuration

Edit: _config.yml (general options), main.css (theme colors &amp; fonts)

```
_config.yml
_assets/
	├── stylesheets/
    ├── main.scss
```

_Note: when editing _config.yml, you need to restart jekyll to see the changes.__
