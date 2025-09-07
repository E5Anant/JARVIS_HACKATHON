import requests
import urllib.parse
import re
from ui.UI import create_image_widget

def get_image_urls(query, num_images=20):
    """
    Get image URLs from multiple sources without downloading
    
    Args:
        query (str): Search term for images
        num_images (int): Number of image URLs to find
    
    Returns:
        list: List of image URLs
    """
    print(f"Searching for '{query}' image URLs...")
    
    all_urls = []
    
    # Method 1: Try Bing Images (often works better than Google)
    bing_urls = get_bing_image_urls(query, num_images)
    if bing_urls:
        print(f"Found {len(bing_urls)} URLs from Bing Images")
        all_urls.extend(bing_urls)
    
    # Method 2: DuckDuckGo Images
    if len(all_urls) < num_images:
        ddg_urls = get_duckduckgo_image_urls(query, num_images - len(all_urls))
        if ddg_urls:
            print(f"Found {len(ddg_urls)} URLs from DuckDuckGo")
            all_urls.extend(ddg_urls)
    
    # Method 3: Pixabay (if you have API key)
    if len(all_urls) < num_images:
        pixabay_urls = get_pixabay_urls(query, num_images - len(all_urls))
        if pixabay_urls:
            print(f"Found {len(pixabay_urls)} URLs from Pixabay")
            all_urls.extend(pixabay_urls)
    
    # Method 4: Pexels (if you have API key)
    if len(all_urls) < num_images:
        pexels_urls = get_pexels_urls(query, num_images - len(all_urls))
        if pexels_urls:
            print(f"Found {len(pexels_urls)} URLs from Pexels")
            all_urls.extend(pexels_urls)
    
    # Remove duplicates while preserving order
    unique_urls = []
    seen = set()
    for url in all_urls:
        if url not in seen:
            unique_urls.append(url)
            seen.add(url)
    
    return unique_urls[:num_images]

def get_bing_image_urls(query, num_images):
    """Get image URLs from Bing Images"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&form=HDRSC2&first=1&tsc=ImageBasicHover"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract image URLs from Bing's response
        image_urls = []
        
        # Look for different patterns in Bing's HTML
        patterns = [
            r'"murl":"([^"]+)"',
            r'"src":"([^"]+)"',
            r'imgurl:"([^"]+)"',
            r'mediaurl=([^&]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response.text)
            for match in matches:
                if match.startswith('http') and any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    if match not in image_urls:
                        image_urls.append(match)
                        if len(image_urls) >= num_images:
                            break
            
            if len(image_urls) >= num_images:
                break
        
        return image_urls
        
    except Exception as e:
        print(f"Bing search failed: {e}")
        return []

def get_duckduckgo_image_urls(query, num_images):
    """Get image URLs from DuckDuckGo Images"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # DuckDuckGo images search
        search_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&t=h_&iax=images&ia=images"
        
        session = requests.Session()
        session.headers.update(headers)
        
        # Get the search page first
        response = session.get(search_url, timeout=10)
        response.raise_for_status()
        
        # Extract vqd token (needed for DuckDuckGo API)
        vqd_match = re.search(r'vqd=([\d-]+)', response.text)
        if not vqd_match:
            return []
        
        vqd = vqd_match.group(1)
        
        # Get images from DuckDuckGo's API
        params = {
            'l': 'us-en',
            'o': 'json',
            'q': query,
            'vqd': vqd,
            'f': ',,,',
            'p': '1',
            'v7exp': 'a'
        }
        
        api_url = "https://duckduckgo.com/i.js"
        api_response = session.get(api_url, params=params, timeout=10)
        
        if api_response.status_code == 200:
            data = api_response.json()
            image_urls = []
            
            for result in data.get('results', []):
                image_url = result.get('image')
                if image_url and image_url.startswith('http'):
                    # Decode URL-encoded characters multiple times if needed
                    decoded_url = image_url
                    while '%' in decoded_url and decoded_url != urllib.parse.unquote(decoded_url):
                        decoded_url = urllib.parse.unquote(decoded_url)
                    
                    image_urls.append(decoded_url)
                    if len(image_urls) >= num_images:
                        break
            
            return image_urls
        
        return []
        
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
        return []

def get_pixabay_urls(query, num_images):
    """Get image URLs from Pixabay"""
    api_key = ""  # Add your Pixabay API key here
    
    if not api_key:
        return []
    
    try:
        url = f"https://pixabay.com/api/?key={api_key}&q={urllib.parse.quote(query)}&image_type=photo&per_page={min(num_images, 200)}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        return [hit['largeImageURL'] for hit in data.get('hits', [])]
    except:
        return []

def get_pexels_urls(query, num_images):
    """Get image URLs from Pexels"""
    api_key = ""  # Add your Pexels API key here
    
    if not api_key:
        return []
    
    try:
        headers = {'Authorization': api_key}
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page={min(num_images, 80)}"
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        return [photo['src']['large'] for photo in data.get('photos', [])]
    except:
        return []

def print_image_urls(query, num_images=10):
    """Print image URLs nicely formatted"""
    urls1 = get_image_urls(query, num_images)
    
    print(f"\n=== Image URLs for '{query}' ===")
    print(f"Found {len(urls1)} URLs:\n")
    urls2 = []
    
    for url in urls1:
        clean_url = url
        for i in range(5):
            new_url = urllib.parse.unquote(clean_url)
            if new_url == clean_url:
                break
            clean_url = new_url
            print(f"Round {i+1}: {clean_url}")
            urls2.append(clean_url)

    print(f"\nTotal: {len(urls2)} image URLs")
    return urls2


def download_from_urls(urls, query, download_folder="images"):
    """Download images from a list of URLs"""
    import os
    import time
    
    safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_query = safe_query.replace(' ', '_')
    folder_path = os.path.join(download_folder, safe_query)
    os.makedirs(folder_path, exist_ok=True)
    
    downloaded = 0
    for i, url in enumerate(urls):
        try:
            print(f"Downloading {i+1}/{len(urls)}...")
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Determine extension
            if '.png' in url.lower():
                ext = '.png'
            elif '.gif' in url.lower():
                ext = '.gif'
            elif '.webp' in url.lower():
                ext = '.webp'
            else:
                ext = '.jpg'
            
            filename = f"{safe_query}_{i+1:03d}{ext}"
            filepath = os.path.join(folder_path, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            downloaded += 1
            print(f"✓ {filename}")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    print(f"\nDownloaded {downloaded} images to '{folder_path}'")

def ImageUI(query:str):
    image = print_image_urls(query, num_images=1)
    create_image_widget(image[0])

# Example usage
if __name__ == "__main__":
    # Test URL decoding
    test_url = "https%3a%2f%2fwallpapercave.com%2fwp%2fxkjRk54.jpg"
    print("Testing URL decoding:")
    print(f"Original: {test_url}")
    
    clean_url = test_url
    for i in range(5):
        new_url = urllib.parse.unquote(clean_url)
        if new_url == clean_url:
            break
        clean_url = new_url
        print(f"Round {i+1}: {clean_url}")
    
    print("\n" + "="*50 + "\n")
    
    # Get small image URLs
    urls = print_image_urls("sports cars", 5)
    
    # Download only images smaller than 500px
    # download_from_urls(urls[:10], "sports cars", max_size=500)
    
    # Or use different size limits:
    # download_from_urls(urls[:5], "sports cars", max_size=300)  # Very small images
    # download_from_urls(urls[:5], "sports cars", max_size=800)  # Medium images