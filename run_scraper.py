from web_scraper import WebScraper



def get_valid_int_input(prompt, default_val, min_val=1, max_val=1000):

    """Hjälpfunktion för att säkerställa giltig numerisk input"""

    while True:

        try:

            value = input(prompt).strip()

            if value == "":  # Om användaren trycker enter

                return default_val

            value = int(value)

            if min_val <= value <= max_val:

                return value

            print(f"Vänligen ange ett nummer mellan {min_val} och {max_val}")

        except ValueError:

            print("Vänligen ange ett giltigt nummer")



def main():

    # Hantera URL-input

    base_url = input("Ange URL att skrapa (t.ex. www.example.com): ").strip()

    

    # Hantera djup med validering och default värde (ändrat till 10)

    max_depth = get_valid_int_input("Ange maximalt skrapningsdjup (1-10) [default=10]: ", 10, 1, 10)

    

    # Hantera antal sidor med validering och default värde

    max_pages = get_valid_int_input("Ange maximalt antal sidor att skrapa (1-1000) [default=1000]: ", 1000, 1, 1000)

    

    scraper = WebScraper(base_url, max_depth=max_depth, max_pages=max_pages)

    print(f"\nBörjar processa {scraper.base_url}...")

    scraper.scrape_page(scraper.base_url)

    

    print("\nSparar data...")

    scraper.save_content()

    

    # Beräkna och visa statistik

    total_words = sum(len(page['content'].split()) 
                     for depth in scraper.text_content.values() 
                     for page in depth)

    print("\nSKRAPNINGSSTATISTIK:")

    print(f"Antal skrapade sidor: {len(scraper.visited_urls)}")

    print(f"Totalt antal ord: {total_words:,}".replace(",", " "))

    print(f"Genomsnittligt antal ord per sida: {total_words // len(scraper.visited_urls):,}".replace(",", " "))

    print("Fördelning per djup:")

    for depth, pages in sorted(scraper.text_content.items()):

        print(f"  Nivå {depth}: {len(pages)} sidor")

    print("\nProcessen slutförd!")



if __name__ == "__main__":

    main() 
