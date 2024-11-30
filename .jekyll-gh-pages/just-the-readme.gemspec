# coding: utf-8

Gem::Specification.new do |spec|
  spec.name          = "just-the-readme"
  spec.version       = "0.0.1"
  spec.authors       = ["Ircama"]

  spec.summary       = %q{A modern, highly customizable, and responsive Jekyll theme for README documentation with built-in search.}
  spec.homepage      = "https://github.com/Ircama/just-the-readme"
  spec.license       = "MIT"

  spec.add_development_dependency "bundler", ">= 2.3.5"
  spec.add_runtime_dependency "sass-embedded", "~> 1.78.0"  # Fix use of deprecated sass lighten() and darken()
  spec.add_runtime_dependency "jekyll", ">= 3.8.5"
  spec.add_runtime_dependency "jekyll-seo-tag", ">= 2.0"
  spec.add_runtime_dependency "jekyll-include-cache"
  spec.add_runtime_dependency "rake", ">= 12.3.1"
  spec.add_runtime_dependency "base64"
  spec.add_runtime_dependency "csv"
end
