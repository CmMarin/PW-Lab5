# go2web

`go2web` is a simple command-line HTTP client using Python's raw TCP sockets (no `urllib` or `requests` for fetching). It parses and renders remote HTTP responses into a human-readable format without HTML tags, supports basic HTTP redirect handling, caching, content negotiation, and searching via duckduckgo.

## Installation

```bash
git clone <repo>
cd PW-Lab5
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
```

## Usage

```bash
# Make an HTTP request to the specified URL and print the response:
go2web -u <URL>

# Make an HTTP request to search the term using a search engine and print top 10 results:
go2web -s <search-term>

# Show help:
go2web -h
```

## Features Implemented:
* `go2web -u` - HTTP/HTTPS request processing and HTML/JSON formatting (renders HTML to human-readable strings). 
* `go2web -s` - Search capability (retrieves DuckDuckGo results). DuckDuckGo redirecting links are automatically decoded.
* `go2web -h` - Help functionality.
* Clean raw HTTP socket network code.
* Caches responses in `.cache/` footprint to avoid redundant socket connections.
* Content negotiation by resolving headers for `application/json` output as well.
* Follows redirects (`301`, `302`, etc.).

## GIF Demo
> Include a gif demo execution here per grading rules.
