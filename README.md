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

## Features Implemented & Bonus Improvements:
### Core & Strict Requirements (+6 points)
* `go2web -u` - HTTP/HTTPS request processing (renders HTML to beautifully formatted human-readable strings).
* `go2web -s` - Search capability (retrieves top 10 DuckDuckGo results). 
* `go2web -h` - Custom Help functionality with ASCII banner.
* Built exclusively with raw TCP sockets (`socket`, `ssl`) per requirements—no third-party HTTP fetching libraries (like `requests` or `urllib.request`).

### Official Bonus Features
* **Link accessibility from search engine results (+1 point)**: DuckDuckGo URL encodings are recursively traced back and parsed to provide standard, clickable direct URLs.
* **HTTP Redirects (+1 point)**: Safely follows relative and absolute network redirects (HTTP `301`, `302`, `303`, `307`, `308`) with a recursion limit.
* **HTTP Cache Mechanism (+2 points)**: Uses `hashlib` to locally cache downloaded payloads inside `.cache/` with an intelligent 1-hour Time-to-Live (TTL) expiration via `pickle`.
* **Content Negotiation (+2 points)**: Sends proper Accept headers. Explicitly listens for `application/json` responses versus `text/html` and auto-prints indented JSON bodies.

### CLI Aesthetic Enhancements
* **Intelligent Terminal Web Renderer**: Behaves like a lightweight CLI browser. Extracts structural DOM tags (`h1-h4`, `li`, `pre`, `code`) and formats them perfectly.
* **"Wiki-Style" Referencing**: Scrapes inline `<a>` href links and generates bracketed numeric indexes `[1]`, dumping a clean clickable footnote appendix of links at the very bottom.
* **ANSI Terminal Highlighting**: Uses terminal colors (Blue, Green, Cyan) to stylize search results and HTML bodies. Simulated background colors are used to render visual `<pre>` code blocks.
* **Loading Spinners**: Uses multithreading to display animated UI indicators so you never wonder if the TCP socket has stalled.
* **Graceful Timeouts**: Integrated strict timeout handles on sockets so poorly coded external web servers don't crash or hang the script indefinitely.

## GIF Demo

