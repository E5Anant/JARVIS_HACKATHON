import requests
from pywhatkit import search
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from bs4 import BeautifulSoup
from rich import print
from unisonai import BaseTool, Field
import webbrowser
from googlesearch import search as netsearch

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

def open_top_n(query: str, n: int = 1):
    for url in netsearch(query, num_results=n):
        print("Opening:", url)
        webbrowser.open_new_tab(url)

def google_search(prompt):
    search(prompt)
    return True

class OpenAppTool(BaseTool):
    name = "Open App"
    description = "Launches desktop applications, web applications. Handles both local installed programs and web-based applications."
    params = [
        Field(
            "apps",
            "list : The list of names of the application to open.",
        )
    ]
    def _run(self, apps:list):
        return self.open_app(apps)
    def open_app(self, apps:list, sess=requests.session()):
        """
        Attempts to open an application.  First tries using AppOpener.
        If that fails, it attempts to find the app's website via Google search 
        and opens it in the browser.  If the website search also fails, it defaults 
        to a generic Google search for the app name.
        """
        for app in apps:
            try:
                print(appopen(app, match_closest=True, output=True, throw_error=True))
            except Exception as e:
                print(f"AppOpener failed: {e}")  # Print the exception for debugging

                try:
                    open_top_n(app)
                except Exception as e2:
                    print(f"Website search and fallback failed: {e2}")
                    print(f"Falling back to generic Google search for {app}")
                    google_search(app)  # As a last resort

        return "Successfully opened apps"
    
def youtube_search(prompt):
    url4search = f"https://www.youtube.com/results?search_query={prompt}"
    webopen(url4search)
    return True
    
class CloseAppTool(BaseTool):
    name = "Close App"
    description = "Closes desktop applications."
    params = [
        Field(
            "apps",
            "list : The list of names of the application to close.",
        )
    ]
    def _run(self, apps:list):
        return self.close_app(apps)
    def close_app(self, apps:list):
        for app in apps:
            if "chrome" in app:
                print("Chrome can't be closed due to speech recognition software")
            try:
                print(close(app, match_closest=True, output=True, throw_error=True))
            except Exception:
                return f"Failed to close {app}"

        return "Successfully closed apps"
    
# OpenAppTool()._run(['notepad', 'facebook'])
# CloseAppTool()._run(['notepad'])
