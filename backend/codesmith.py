import google.generativeai as genai
from os import environ
from dotenv import load_dotenv
from rich import print
from time import time as t
import re
import sys
import subprocess
from typing import Tuple, List, Dict
import asyncio
from functools import lru_cache
import logging
import os

load_dotenv()
genai.configure(api_key=environ['GEMINI_API_KEY'])

with open("backend\\prompts\\codesmith.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()
    f.close()

# Import guidance for the model
system_prompt_addition = """
IMPORTANT: When writing Python code to automate tasks, use these specific import paths:
- from Backend.func.automation import OpenAppTool, CloseAppTool, google_search
- DO NOT use paths like 'util.automation' or other incorrect paths

Example of correct code:
```python
from backend.func.automation import OpenAppTool

def main():
    # Open notepad application
    result = OpenAppTool()._run(["notepad", "Wordpad"]) # Opening and Closing Apps tool takes a list of apps
    print(result)
    return "Opened notepad successfully"

if __name__ == "__main__":
    output = main()
    print(output)
```
**Use This only don't try to use append or for loops in this kind of tasks**
"""

class Codesmith:
    def __init__(self):
        
        self.generation_config = {
            "temperature": 1,  # Balanced creativity and consistency
            "max_output_tokens": 2048,  # More tokens for complex tasks
            "top_p": 0.95,
            "top_k": 40,
        }

        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        self.system_prompt = SYSTEM_PROMPT + system_prompt_addition

        self.messages: List[Dict] = []
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite-preview-06-17",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            system_instruction=self.system_prompt
        )

    @lru_cache(maxsize=50)
    async def execute_code(self, response_text: str) -> Tuple[str, bool, bool]:
        """
        Execute Python code with advanced error handling and continuation support.
        
        Returns:
        - Execution output
        - Execution success status
        - Continuation flag
        """
        code_match = re.search(r"```python(.*?)```", response_text, re.DOTALL)
        if not code_match:
            print("No valid Python code found in response")
            return "", False, False

        code = code_match.group(1).strip()
        
        # Add module imports that point to the correct locations
        imports_to_add = """
import sys
import os
# Add the project root to path to ensure imports work correctly
sys.path.insert(0, os.path.abspath('.'))
# Import your commonly used functions
try:
    from backend.func.automation import OpenAppTool, CloseAppTool, google_search
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
"""
        
        code = imports_to_add + "\n\n" + code

        try:
            with open("temp.py", "w") as f:
                f.write(code)

            # Print the actual code being executed for debugging
            print("Executing code:")
            print("--------------------")
            print(code)
            print("--------------------")

            # Use standard subprocess instead of asyncio subprocess
            try:
                # Method 1: Use synchronous subprocess
                result = subprocess.run(
                    [sys.executable, "temp.py"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    is_continue = "CONTINUE" in output
                    clean_output = output.replace("CONTINUE", "").strip()
                    
                    print(f"Script executed successfully. Continuation needed: {is_continue}")
                    return clean_output, True, is_continue
                else:
                    error_output = result.stderr
                    print(f"Script execution failed: {error_output}")
                    return error_output, False, False
                
            except subprocess.SubprocessError as se:
                print(f"Subprocess error: {se}")
                return str(se), False, False

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Unexpected error during code execution:")
            print(error_details)
            return str(e), False, False

    async def automator(self, prompt: str, verbose: bool = True) -> Tuple[str, bool]:
        """
        Advanced automation handler with robust continuation support.
        """
        start_time = t()
        
        try:
            self.messages.append({"parts": [{"text": prompt}], "role": "user"})
            
            # Retry mechanism for response generation
            for attempt in range(3):
                try:
                    response = await asyncio.to_thread(self.model.generate_content, self.messages)
                    
                    # Check if the response was blocked by safety filters
                    if not hasattr(response, 'candidates') or not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
                        print("Response was blocked by safety filters. Retrying with modified prompt...")
                        # Try with a more explicit instruction to follow your guidelines
                        modified_prompt = f"Please help me perform this task using Python code: {prompt}. Remember to only use the functions from Functions.Automations."
                        self.messages[-1] = {"parts": [{"text": modified_prompt}], "role": "user"}
                        continue
                    
                    # Successfully got a response
                    if response.text:
                        break
                except Exception as gen_error:
                    print(f"Generation attempt {attempt + 1} failed: {gen_error}")
                    if attempt == 2:
                        raise
            
            # If we still don't have a valid response after retries
            if not hasattr(response, 'text') or not response.text:
                return "The AI was unable to generate a suitable response. This might be due to safety filters or API limitations.", False
                
            if verbose:
                print(f"Generated response: {response.text}")
            self.messages.append({"parts": [{"text": response.text}], "role": "model"})
            
            # Execute and check for continuation
            output, success, needs_continue = await self.execute_code(response_text=response.text)
            
            # Manage message history
            if len(self.messages) > 10:
                self.messages = self.messages[:2] + self.messages[-8:]
            
            execution_time = t() - start_time
            print(f"Execution completed in {execution_time:.2f}s")
            
            # Recursive continuation handling
            if needs_continue:
                print("Continuation stage triggered")
                self.messages.append({"parts": [{"text": f"LAST SCRIPT OUTPUT:\n\n {output}"}], "role": "user"})
                return await self.automator("CONTINUE")
            
            return output, success
            
        except Exception as e:
            print(f"Automation process failed: {e}")
            return str(e), False

    async def main(self):
        print("[bold green]Rawdog AI Assistant[/bold green]")
        print("[yellow]Type your command or 'exit' to quit[/yellow]")
        
        while True:
            try:
                prompt = input(">>> ")
                
                if prompt.lower() in ['exit', 'quit', 'q']:
                    break
                
                start_time = t()
                output, success = await self.automator(prompt)
                
                execution_time = t() - start_time
                print(f"[bold green]Execution Time:[/bold green] {execution_time:.2f}s")
                print(f"[bold blue]Output:[/bold blue] {output}")
                print(f"[bold yellow]Success:[/bold yellow] {success}")
                    
            except KeyboardInterrupt:
                print("\nExiting Rawdog...")
                break
            except Exception as e:
                print(f"[bold red]Error:[/bold red] {str(e)}")

from unisonai import BaseTool, Field

class CodesmithTool(BaseTool):
    name = "Codesmith"
    description = (
        "A versatile automation and code-generation assistant powered by LLM. "
        "It can understand natural-language prompts, generate and execute Python scripts, "
        "summarize files or codebases, handle multi-step workflows, and provide detailed logs and error handling. "
        "Ideal for automating repetitive tasks, opening/closing applications, web searches, and more. It can open websites or youtube channel and more."
    )
    params = [
        Field("prompt", "A clear description of the task or code operation to perform, e.g. 'Summarize the contents of report.pdf' or 'Open Notepad and write Hello World'.")
    ]

    async def _run(self, prompt: str):
        """
        Synchronously invoke the Codesmith.automator() coroutine and return its output.

        Returns:
            dict: {
                "output": str,    # The console or summarization result
                "success": bool   # True if execution was error-free
            }
        """
        assistant = Codesmith()
        output, success = await assistant.automator(prompt, verbose=False)
        return {"output": output, "success": success}

if __name__ == "__main__":
    assistant = Codesmith()
    asyncio.run(assistant.main())