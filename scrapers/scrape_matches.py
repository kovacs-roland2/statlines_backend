import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
from pathlib import Path

def get_match_results():
    """Scrape Premier League match results from FBref."""
    url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Add a small delay to be respectful to the server
        time.sleep(2)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find the main table with match results
        table = soup.find('table', {'id': 'sched_2024-2025_9_1'})
        if not table:
            raise Exception("Match results table not found")
        
        # Extract headers - only get the visible headers
        headers = []
        header_row = table.find('thead').find('tr')
        for th in header_row.find_all('th'):
            # Skip hidden headers
            if 'data-stat' in th.attrs:
                headers.append(th.get_text(strip=True))
        
        # Extract rows
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            row = []
            for td in tr.find_all(['td', 'th']):
                # Skip hidden columns
                if 'data-stat' in td.attrs:
                    # Get the text content
                    text = td.get_text(strip=True)
                    
                    # For team names, get the full name from the link if available
                    if td.find('a'):
                        text = td.find('a').get_text(strip=True)
                    
                    row.append(text)
            
            if row:  # Only add non-empty rows
                rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Clean up the DataFrame
        df = df.replace('', pd.NA)  # Replace empty strings with NA
        df = df.dropna(how='all')  # Drop rows that are all NA
        
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = data_dir / f'premier_league_matches_{timestamp}.csv'
        df.to_csv(output_file, index=False)
        
        print(f"Successfully scraped {len(df)} matches")
        print(f"Data saved to: {output_file}")
        
        # Print column names for verification
        print("\nColumns in the dataset:")
        for col in df.columns:
            print(f"- {col}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error processing the data: {e}")
        return None

if __name__ == "__main__":
    get_match_results() 