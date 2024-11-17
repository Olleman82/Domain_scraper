import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from collections import defaultdict
import datetime

class WebScraper:
    def __init__(self, base_url, max_depth=5, max_pages=1000, ignore_languages=None):
        """Initierar web scraper med grundläggande konfiguration"""
        self.base_url = self._format_url(base_url)
        self.domain = urlparse(self.base_url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls = set()
        self.text_content = defaultdict(list)
        self.ignore_languages = ignore_languages or ['en']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def _format_url(self, url):
        """Formaterar URL till standardformat med https://"""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url

    def is_valid_url(self, url):
        """Förbättrad URL-validering med språkhantering"""
        try:
            parsed = urlparse(url)
            
            # Normalisera domänerna för jämförelse
            site_domain = parsed.netloc.replace('www.', '')
            base_domain = self.domain.replace('www.', '')
            
            # Kontrollera om detta är en alternativ språkversion
            path = parsed.path.lower()
            if '/en/' in path:  # Ignorera engelska versionen
                return False
            
            # Ignorera tomma länkar och ankarlänkar
            if not url or url.startswith('#'):
                return False
            
            # Kontrollera domän och filtyper
            is_valid = (
                site_domain == base_domain and  # Matcha domäner utan www
                not any(ext in url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.css', '.js']) and
                '#' not in url and  # Ignorera URL:er med fragment
                'tel:' not in url.lower()  # Ignorera telefonnummer
            )
            
            if is_valid:
                print(f"Godkänd URL: {url}")
            
            return is_valid
            
        except Exception as e:
            print(f"Fel vid URL-validering av {url}: {str(e)}")
            return False

    def extract_text(self, soup):
        """Förbättrad textextraktion"""
        # Ta bort oönskade element
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript']):
            element.decompose()
        
        # Samla text från viktiga element i rätt ordning
        text_elements = []
        
        # Extrahera meta-beskrivning
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            text_elements.append(f"BESKRIVNING: {meta_desc['content']}\n")
        
        # Extrahera huvudinnehåll
        main_content = soup.find('main') or soup.find(id='main') or soup
        
        # Hantera rubriker och innehåll hierarkiskt
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol']):
            if element.name.startswith('h'):
                level = int(element.name[1])
                text = element.get_text().strip()
                if text:
                    text_elements.append(f"{'#' * level} {text}")
            elif element.name == 'p':
                text = element.get_text().strip()
                if text:
                    text_elements.append(text)
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li', recursive=False):
                    text = li.get_text().strip()
                    if text:
                        text_elements.append(f"- {text}")
        
        return '\n\n'.join(filter(None, text_elements))

    def scrape_page(self, url, depth=0):
        """Förbättrad sidskrapning"""
        try:
            formatted_url = self._format_url(url)
            
            if depth >= self.max_depth or len(self.visited_urls) >= self.max_pages:
                return

            if formatted_url in self.visited_urls:
                return

            print(f"\nSkrapar nivå {depth}: {formatted_url}")
            response = requests.get(formatted_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Fel: Status kod {response.status_code} för {formatted_url}")
                return

            self.visited_urls.add(formatted_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extrahera text
            text_content = self.extract_text(soup)
            if text_content:
                self.text_content[depth].append({
                    'url': formatted_url,
                    'content': text_content
                })

            # Hitta och följ länkar
            links = soup.find_all('a', href=True)
            print(f"Hittade {len(links)} länkar på {formatted_url}")
            
            for link in links:
                href = link['href']
                # Hantera relativa länkar
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(formatted_url, href)
                
                if self.is_valid_url(href):
                    print(f"Följer länk: {href}")
                    self.scrape_page(href, depth + 1)

        except Exception as e:
            print(f"Fel vid skrapning av {formatted_url}: {str(e)}")

    def save_content(self, output_dir='scraped_content'):
        """Sparar skrapad data i tidsstämplade filer med naturlig uppdelning"""
        # Beräkna totalt antal ord
        total_words = sum(len(page['content'].split()) 
                         for depth in self.text_content.values() 
                         for page in depth)
        
        # Skapa tidsstämplad katalog
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        domain_name = self.domain.replace('.', '_')
        output_path = os.path.join(output_dir, f'{domain_name}_{timestamp}')
        os.makedirs(output_path, exist_ok=True)
        
        # Initiera variabler för filhantering
        current_file = 1
        current_word_count = 0
        current_content = []
        total_files = (total_words // 500000) + 1

        # Skapa sammanfattning
        summary = f"""
Skrapning av: {self.base_url}
Tidpunkt: {timestamp}
Antal skrapade sidor: {len(self.visited_urls)}
Skrapningsdjup: {self.max_depth}
Totalt antal ord: {total_words:,}
{f'Innehållet är uppdelat på {total_files} filer' if total_words > 500000 else 'All data i en fil'}
-------------------
""".replace(",", " ")
        
        current_content.append(summary)
        
        # Spara innehåll med naturlig uppdelning
        for depth in sorted(self.text_content.keys()):
            for page in self.text_content[depth]:
                content = f"\n\nKÄLLA: {page['url']}\nDJUP: {depth}\n{page['content']}"
                words = len(content.split())
                
                # Om denna sida skulle göra att vi överstiger 500 000 ord, spara current_content först
                if current_word_count + words > 500000 and current_content:
                    self._save_file(current_content, current_file, output_path)
                    current_file += 1
                    current_content = [summary]  # Börja ny fil med sammanfattningen
                    current_word_count = len(summary.split())
                
                current_content.append(content)
                current_word_count += words

        # Spara sista filen
        if current_content:
            self._save_file(current_content, current_file, output_path)
        
        print(f"\nData sparad i: {output_path}")
        if total_words > 500000:
            print(f"Innehållet delat på {current_file} filer")

    def _save_file(self, content, file_number, output_dir):
        """Sparar innehåll till fil"""
        filename = os.path.join(output_dir, f'scraped_content_{file_number}.txt')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))