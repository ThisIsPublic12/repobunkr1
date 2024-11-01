import sys
import xbmcgui
import xbmcplugin
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlencode, parse_qsl

# Kodi-specific constants
_handle = int(sys.argv[1])
_base_url = sys.argv[0]

def build_url(query):
    return _base_url + '?' + urlencode(query)

def search_bunkr(query):
    """
    Searches bunkr-albums.io for albums.
    """
    base_url = "https://bunkr-albums.io/"
    search_url = f"{base_url}?search={query}"
    response = requests.get(search_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    results = []
    for result_div in soup.find_all("div", class_="group/item"):
        title = result_div.find("p", class_="text-subs").text.strip()
        url = result_div.find("a", class_="ic-chevron-right")["href"]
        files = result_div.find("p", class_="text-xs").find("span").text
        thumbnail = result_div.find("span", class_="ic-albums")["src"]  
        results.append({
            "title": title,
            "url": url,
            "files": files,
            "thumbnail": thumbnail
        })
    return results

def get_album_details(url):
    """
    Fetches an album page and extracts video URLs.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    
    # *** IMPORTANT ***
    # Replace this with the actual code to extract video URLs from the album page
    video_urls = []  
    # Example (adapt based on the page structure):
    # for video_div in soup.find_all("div", class_="video-item"):
    #     video_url = video_div.find("a")["href"]
    #     video_urls.append(video_url)

    return video_urls

def get_video_details(url):
    """
    Fetches a video page and extracts the actual video URL.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.find("div", class_="flex items-center").find("h1").text.strip()
    thumbnail = soup.find("video")["data-poster"]
    download_url = soup.find("a", class_="ic-download-01")["href"]
    script_tag = soup.find("script", text=lambda text: "var jsSlug =" in text)
    js_slug = script_tag.text.split("var jsSlug = '")[1].split("'")[0]
    api_url = "https://bunkr.black/api/gimmeurl"  # Make sure this is the correct domain
    api_response = requests.post(api_url, json={"slug": js_slug})
    api_response.raise_for_status()
    video_url = api_response.json()["data"]["newUrl"]
    return {
        "title": title,
        "thumbnail": thumbnail,
        "download_url": download_url,
        "video_url": video_url
    }

def show_search_results(query):
    results = search_bunkr(query)
    for result in results:
        li = xbmcgui.ListItem(result['title'])
        li.setArt({'thumb': result['thumbnail']})
        li.setInfo('video', {'title': result['title'], 'plot': f"Files: {result['files']}"})
        url = build_url({'mode': 'list_album', 'url': result['url']})
        xbmcplugin.addDirectoryItem(_handle, url, li, True)
    xbmcplugin.endOfDirectory(_handle)

def list_album(url):
    video_urls = get_album_details(url)
    for video_url in video_urls:
        video_details = get_video_details(video_url)
        li = xbmcgui.ListItem(video_details['title'])
        li.setArt({'thumb': video_details['thumbnail']})
        li.setInfo('video', {'title': video_details['title']})
        url = build_url({'mode': 'play_video', 'url': video_details['video_url']})
        xbmcplugin.addDirectoryItem(_handle, url, li)
    xbmcplugin.endOfDirectory(_handle)

def play_video(url):
    li = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(_handle, True, li)

def main():
    args = dict(parse_qsl(sys.argv[2][1:]))
    mode = args.get('mode', 'search')
    if mode == 'search':
        query = xbmcgui.Dialog().input("Enter your search query")
        if query:
            show_search_results(query)
    elif mode == 'list_album':
        url = args.get('url')
        if url:
            list_album(url)
    elif mode == 'play_video':
        url = args.get('url')
        if url:
            play_video(url)

if __name__ == '__main__':
    main()