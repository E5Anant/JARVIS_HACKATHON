from googlesearch import search as netsearch
from duckduckgo_search import DDGS
from unisonai import BaseTool, Field
try:
    from custom.web.googleImageScraper import ImageUI
    from ui.UI import create_text_widget
except:
    print("No UI available")


class WebSearchTool(BaseTool):
    name = "Web Search"
    description = "Use this tool for any Researching and Search on the internet for any information of any website on any Topic."
    params = [Field("query", "The query to search for")]

    def _run(self, query: str):
        return self.websearch(query)

    def websearch(self, query: str):
        output = ""
        print("via google search...")
        results = list(netsearch(query, advanced=True, num_results=5))
        if results:
            print("got results")
            for i, result in enumerate(results):
                output += f"{i+1}. \nTitle: {result.title}\nDescription: {result.description}\nSource: {result.url}\n\n"    
        else:
            print(f"Error using google search: No results found trying...")

        # If Online_Scraper fails or is not found use DuckDuckGo
            try:
                ddg = DDGS()
                ddg_results = ddg.text(query, max_results=6)
                
                if ddg_results:
                    for result in ddg_results:
                        output+=f"TITLE:\n{result.get('title', 'No Title Found')}\n\nBODY:\n{result.get('body', 'No Body Found')}\n\n"
                else:
                    print("No results from DuckDuckGo")
                    return "Failed to retrieve search results"

            except Exception as e:
                print(f"Error using DuckDuckGo Search: {e}")
                return "Failed to retrieve search results"
        print(output)
        try:
            ImageUI(query=query)
            create_text_widget(output, title="Web Results")
        except Exception as e:
            print(f"Error displaying images: {e}")
        try:
            return output + "\n **Use This Info To Answer.**"
        except:
            return output + "\n **Use This Info To Answer.**"
        
if __name__ == "__main__":
    tool = WebSearchTool()
    print(tool._run("Latest AI news"))