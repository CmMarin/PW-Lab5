import argparse
import socket
import ssl
import sys
import json
import urllib.parse
import os
import hashlib
import pickle
import time
import threading
import itertools
import re
from bs4 import BeautifulSoup

MAX_REDIRECTS = 5
CACHE_DIR = ".cache"
CACHE_TTL = 3600  # Cache expires after 1 hour

class Colors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class Spinner:
    def __init__(self, message="Working..."):
        self.spinner = itertools.cycle(['-', '\\', '|', '/'])
        self.stop_running = threading.Event()
        self.thread = threading.Thread(target=self.spin_task, args=(message,))

    def spin_task(self, message):
        while not self.stop_running.is_set():
            sys.stdout.write(f"\r{Colors.OKBLUE}{next(self.spinner)} {message}{Colors.ENDC}")
            sys.stdout.flush()
            time.sleep(0.1)
        # Clear the spinner
        sys.stdout.write('\r' + ' ' * (len(message) + 4) + '\r')
        sys.stdout.flush()

    def start(self):
        self.stop_running.clear()
        self.thread.start()

    def stop(self):
        self.stop_running.set()
        self.thread.join()

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cache_path(url):
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, url_hash)

def parse_url(url):
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme if parsed.scheme else 'http'
    netloc = parsed.netloc
    
    if ':' in netloc:
        host, port = netloc.split(':', 1)
        port = int(port)
    else:
        host = netloc
        port = 443 if scheme == 'https' else 80
        
    path = parsed.path if parsed.path else '/'
    if parsed.query:
        path += '?' + parsed.query
        
    return scheme, host, port, path

def make_request(url, redirects=0):
    if redirects > MAX_REDIRECTS:
        print(f"{Colors.FAIL}Too many redirects.{Colors.ENDC}")
        sys.exit(1)

    cache_path = get_cache_path(url)
    if os.path.exists(cache_path):
        if time.time() - os.path.getmtime(cache_path) < CACHE_TTL:
            with open(cache_path, 'rb') as f:
                headers, body_data = pickle.load(f)
                return headers, body_data
        else:
            os.remove(cache_path)
    
    scheme, host, port, path = parse_url(url)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if scheme == 'https':
        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=host)

    sock.settimeout(10.0)

    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"{Colors.FAIL}Connection error: {e}{Colors.ENDC}")
        sys.exit(1)

    request = f"GET {path} HTTP/1.1\r\n"
    request += f"Host: {host}\r\n"
    request += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
    request += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.8\r\n"
    request += "Connection: close\r\n"
    request += "\r\n"

    sock.sendall(request.encode('utf-8'))

    response = b""
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
    except socket.timeout:
        pass
    except Exception as e:
        print(f"{Colors.FAIL}Error reading data:{Colors.ENDC} {e}")

    sock.close()
    header_data, _, body_data = response.partition(b"\r\n\r\n")
    headers_text = header_data.decode('utf-8', errors='ignore')
    
    lines = headers_text.split("\r\n")
    status_line = lines[0]
    status_code = int(status_line.split(" ")[1])
    
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            headers[key.strip().lower()] = val.strip()
            
    if status_code in [301, 302, 303, 307, 308]:
        location = headers.get('location')
        if location:
            # Handle relative redirects
            if not location.startswith('http'):
                location = f"{scheme}://{host}{location}"
            return make_request(location, redirects + 1)
            
    with open(cache_path, 'wb') as f:
        pickle.dump((headers, body_data), f)
        
    return headers, body_data

def render_html(body, base_url):
    soup = BeautifulSoup(body, 'html.parser')
    
    # 1. Clean invisible and layout elements
    for element in soup(["script", "style", "meta", "noscript", "svg", "canvas", "video", "audio", "nav", "footer"]):
        element.decompose()
        
    # 2. Handle Images nicely
    for img in soup.find_all('img'):
        alt = img.get('alt', '').strip()
        if alt:
            img.replace_with(f" [🖼️  Image: {alt}] ")
        else:
            img.decompose()

    # 3. Extract links and build footnote references
    links = []
    for a in soup.find_all('a'):
        href = a.get('href')
        text = a.get_text(strip=True)
        if href and text and not href.startswith(('javascript:', 'mailto:', 'tel:')):
            if href.startswith('/'): # resolve relative paths
                parsed = urllib.parse.urlsplit(base_url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            elif not href.startswith('http'):
                continue
            
            if href not in links:
                links.append(href)
            ref_num = links.index(href) + 1
            
            # Reconstruct the text with a citation bracket
            a.clear()
            a.append(f"{text} [{ref_num}]")
            
    # 4. Format Headers to ANSI Bold+Blue uppercase 
    for header_tag in ['h1', 'h2', 'h3', 'h4']:
        for h in soup.find_all(header_tag):
            text = h.get_text(strip=True)
            if text:
                h.clear()
                h.append(f"\n{Colors.BOLD}{Colors.OKBLUE}{text.upper()}{Colors.ENDC}\n")
                
    # 5. Format List Items with bullets
    for li in soup.find_all('li'):
        text = li.get_text(strip=True)
        if text:
            li.clear()
            li.append(f"  • {text}")
            
    # 6. Final text extraction
    text = soup.get_text(separator='\n', strip=True)
    # Collapse 3+ newlines down to 2 for cleaner spacing
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    print(text)
    
    # 7. Print the collected external link References at the bottom
    if links:
        print(f"\n{Colors.BOLD}{Colors.WARNING}=== Page Links ==={Colors.ENDC}")
        for i, link in enumerate(links[:40], 1): # Max 40 links to avoid flooding term
            print(f" [{i}] {Colors.OKGREEN}{link}{Colors.ENDC}")
        if len(links) > 40:
            print(f"  ... and {len(links) - 40} more links.")

def handle_url(url):
    spinner = Spinner(f"Fetching {url}...")
    spinner.start()
    try:
        headers, body = make_request(url)
    finally:
        spinner.stop()
        
    content_type = headers.get('content-type', '')
    
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}►►► Result for: {url} ◄◄◄{Colors.ENDC}\n")
    
    if 'application/json' in content_type:
        try:
            print(json.dumps(json.loads(body.decode('utf-8')), indent=2))
        except json.JSONDecodeError:
            print(f"{Colors.FAIL}Failed to parse JSON{Colors.ENDC}")
            print(body.decode('utf-8', errors='ignore'))
    else:
        render_html(body, url)
        
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}►►► End of Response ◄◄◄{Colors.ENDC}\n")

def handle_search(term):
    # Using DuckDuckGo html version
    encoded_term = urllib.parse.quote_plus(term)
    url = f"https://html.duckduckgo.com/html/?q={encoded_term}"
    
    spinner = Spinner(f"Searching for '{term}'...")
    spinner.start()
    try:
        headers, body = make_request(url)
    finally:
        spinner.stop()
    
    soup = BeautifulSoup(body, 'html.parser')
    results = soup.find_all('a', class_='result__snippet', limit=10)
    titles = soup.find_all('h2', class_='result__title', limit=10)
    links = soup.find_all('a', class_='result__url', limit=10)
    
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}=== Top 10 Results for '{term}' ==={Colors.ENDC}\n")

    if not results:
        print(f"{Colors.WARNING}No results found.{Colors.ENDC}")
        return
        
    for i in range(len(results)):
        title = titles[i].get_text(strip=True) if i < len(titles) else "No title"
        link_href = links[i].get('href', '') if i < len(links) else ""
        if link_href.startswith('//'):
            link_href = 'https:' + link_href
        elif link_href.startswith('/'):
            link_href = "https://duckduckgo.com" + link_href
            
        if '/l/?uddg=' in link_href:
            parsed_link = urllib.parse.parse_qs(urllib.parse.urlsplit(link_href).query)
            if 'uddg' in parsed_link:
                link_href = urllib.parse.unquote(parsed_link['uddg'][0])
        
        snippet = results[i].get_text(strip=True)
        
        print(f"{Colors.BOLD}{Colors.OKBLUE}[{i+1}] {title}{Colors.ENDC}")
        print(f"    {Colors.WARNING}URL:{Colors.ENDC} {link_href}")
        print(f"    {snippet}\n")

def print_banner():
    banner = f"""{Colors.OKBLUE}{Colors.BOLD}
   ____      ___        __    _          _     
  / __ \____|__ \_      __  __| |        | |    
 / / _`/ __ \ / /| | /| / / _ \| '_ \ 
/ /_/ / /_/ // /_| |/ |/ /  __/| |_) |
\____/\____//____|__/|__/ \___||_.__/ 
{Colors.ENDC}"""
    print(banner)

def print_custom_help():
    print_banner()
    print(f"  {Colors.BOLD}go2web - a simple CLI HTTP client{Colors.ENDC}\n")
    print(f"  {Colors.BOLD}Usage:{Colors.ENDC}")
    print(f"    {Colors.OKGREEN}go2web -u <URL>{Colors.ENDC}         Fetch and display a URL")
    print(f"    {Colors.OKGREEN}go2web -s <term>{Colors.ENDC}        Search and print top 10 results")
    print(f"    {Colors.OKGREEN}go2web -h{Colors.ENDC}               Show this help\n")

def main():
    if len(sys.argv) == 1 or '-h' in sys.argv or '--help' in sys.argv:
        print_custom_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(description="go2web - a simple CLI HTTP client", add_help=False)
    parser.add_argument('-u', '--url', type=str, help="make an HTTP request to the specified URL and print the response")
    parser.add_argument('-s', '--search', type=str, nargs='+', help="make an HTTP request to search the term using your favorite search engine and print top 10 results")
    parser.add_argument('-h', '--help', action='store_true', help="show this help")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    args, unknown = parser.parse_known_args()
    
    if args.help:
        parser.print_help()
        sys.exit(0)
        
    if args.url:
        url = args.url
        if not url.startswith('http'):
            url = 'http://' + url
        handle_url(url)
        
    elif args.search:
        term = ' '.join(args.search)
        handle_search(term)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()