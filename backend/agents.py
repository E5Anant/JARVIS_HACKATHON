from unisonai import Single_Agent
from unisonai.llms import Gemini
from backend.func.automation import CloseAppTool, OpenAppTool
from backend.func.websearch import WebSearchTool
from backend.func.weather import WeatherTool
from backend.func.youtube import YoutubePlay
from backend.func.location import UserLocation
from backend.func.time import TimezoneCurrentTime
from backend.func.YTSummarize import YTSummarize
from backend.codesmith import CodesmithTool
from backend.vision import VisionTool
from backend.ai_tools.imggen import GenerateImageTool

with open("backend/prompts/workflow_maker.md", "r") as f:
    WorkFlow_Maker_Prompt = f.read()
    f.close()

with open("backend/prompts/web_crawler.md", "r") as f:
    Web_Crawler_Prompt = f.read()
    f.close()

with open("backend/prompts/system_automator.md", "r") as f:
    System_Automator_Prompt = f.read()
    f.close()

with open("backend/prompts/ai_expert.md", "r") as f:
    AI_Expert_Prompt = f.read()
    f.close()

with open("backend/prompts/code_generator.md", "r") as f:
    Code_Generator_Prompt = f.read()
    f.close()

WorkFlow_Maker = Single_Agent(
    llm=Gemini(model="gemini-2.5-flash-lite"),
    identity="WorkFlow Maker",
    description=WorkFlow_Maker_Prompt,
    tools=[],
    verbose=True,
    output_file="outputs/workflow_maker.txt",
)

Web_Crawler = Single_Agent(
    llm=Gemini(model="gemini-2.5-flash-lite"),
    identity="Web Crawler",
    description=Web_Crawler_Prompt,
    tools=[WeatherTool, WebSearchTool, YoutubePlay, UserLocation, TimezoneCurrentTime, CodesmithTool, YTSummarize],
    verbose=True,
    output_file="outputs/web_crawler.txt",
)

System_Automator = Single_Agent(
    llm=Gemini(model="gemini-2.5-flash-lite"),
    identity="System Automator",
    description=System_Automator_Prompt,
    tools=[OpenAppTool, CloseAppTool, CodesmithTool],
    verbose=True,
    output_file="outputs/system_automator.txt",
)

AI_Expert = Single_Agent(
    llm=Gemini(model="gemini-2.5-flash-lite"),
    identity="AI Expert",
    description=AI_Expert_Prompt,
    tools=[GenerateImageTool, VisionTool, CodesmithTool],
    verbose=True,
    output_file="outputs/ai_expert.txt",
)

Code_Generator = Single_Agent(
    llm=Gemini(model="gemini-2.5-flash-lite"),
    identity="Code Generator",
    description=Code_Generator_Prompt,
    tools=[],
    verbose=True,
    output_file="outputs/code_generator.txt",
)
    