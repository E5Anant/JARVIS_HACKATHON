import os
import google.generativeai as genai
from backend.agents import AI_Expert, System_Automator, Web_Crawler
from tools import ai_expert, system_automator, web_crawler, create_text_widget, Vision_tool
import re
from backend.vision import Vision
import asyncio
from concurrent.futures import ThreadPoolExecutor
import base64
from shared_queue import ui_update_queue

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

generation_config = {
    "temperature": 1,
    "max_output_tokens": 2048,
    "top_p": 0.95,
    "top_k": 40,
}

def load_prompt_from_file(file_path: str) -> str:
    """
    Reads a prompt template from a file and substitutes placeholders
    in the format {ENV_VAR_NAME} with corresponding environment variables.
    """
    try:
        with open(file_path, "r") as f:
            template_string = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        raise

    def get_env_var(match: re.Match) -> str:
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise KeyError(f"Environment variable '{var_name}' not found, but is required by the prompt.")
        return value

    processed_string = re.sub(r"{(\w+)}", get_env_var, template_string)
    return processed_string

System = load_prompt_from_file("backend/prompts/base.md")

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel("gemini-2.5-flash-lite", safety_settings=safety_settings, generation_config=generation_config, system_instruction=System)
AssistantMessages = []
executor = ThreadPoolExecutor(max_workers=5)

# --- REWRITTEN execute_function ---
async def execute_function(function_name, args):
    """
    Executes a function. For UI functions, it queues a command.
    For backend functions, it runs them in a separate thread.
    """
    loop = asyncio.get_running_loop()
    
    try:
        # --- UI Function Handling ---
        if function_name == "create_text_widget":
            print(f"Queueing UI command: {function_name}")
            # Put the command and its arguments on the queue for the main thread
            ui_update_queue.put(('create_widget', {
                'type': 'text',
                'title': args.get('title', 'INFORMATION'), # Use .get for safety
                'text': args.get('text')
            }))
            # Return a success message to the AI
            return f"Successfully queued the creation of a text widget with title '{args.get('title', 'INFORMATION')}'."

        # --- Backend Agent Handling (no change) ---
        elif function_name == "AI_Expert":
            result = await loop.run_in_executor(
                executor, AI_Expert.unleash, args["prompt"]
            )
        elif function_name == "System_Automator":
            result = await loop.run_in_executor(
                executor, System_Automator.unleash, args["prompt"]
            )
        elif function_name == "Web_Crawler":
            result = await loop.run_in_executor(
                executor, Web_Crawler.unleash, args["prompt"]
            )
        elif function_name == "VisionTool":
            result = await loop.run_in_executor(
                executor, Vision, args["prompt"], args["mode"]
            )
        else:
            result = "Unknown function called."
        
        # print("Got Result:", result)
        if not result or len(str(result).strip()) == 0:
            return "Error: Empty result from tool"
        return result
    except Exception as e:
        print(f"Error executing {function_name}: {str(e)}")
        return f"Error executing {function_name}: {str(e)}"

# --- REWRITTEN handle_function_calls ---
async def handle_function_calls(function_calls):
    """
    Handle multiple function calls concurrently.
    This version correctly unpacks the (name, args) tuples.
    """
    # THE FIX: Use call[0] for the name and call[1] for the args.
    tasks = [
        execute_function(call[0], dict(call[1])) for call in function_calls
    ]
    results = await asyncio.gather(*tasks)
    
    # THE FIX: Use call[0] for the name when zipping the results.
    return [(call[0], result) for call, result in zip(function_calls, results)]


# --- MODIFIED generate function ---
async def generate(prompt, files=None): # Function is already async, which is correct
    global AssistantMessages
    
    user_parts = []
    if prompt:
        user_parts.append({"text": prompt})

    if files:
        print(f"Processing {len(files)} files...")
        for file_info in files:
            try:
                header, encoded_data = file_info['data'].split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
                user_parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded_data
                    }
                })
                print(f"Successfully processed and added file: {file_info['name']}")
            except Exception as e:
                print(f"Error processing file data for {file_info.get('name', 'unknown file')}: {e}")

    if not user_parts:
        print("Generate function called with no prompt or files. Aborting.")
        return "Please provide a prompt or a file."

    AssistantMessages.append({
        "role": "user", 
        "parts": user_parts
    })
    
    # Note: The format for tools with generate_content is slightly different
    tools = [ai_expert, system_automator, web_crawler, create_text_widget, Vision_tool]
    
    while True:
        try:
            # Using the synchronous generate_content as requested
            response = model.generate_content(AssistantMessages, tools=tools)
            
            # This parsing logic is correct for the synchronous response
            function_calls = []
            if response.candidates and hasattr(response.candidates[0].content, 'parts'):
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        func_name = part.function_call.name
                        # Appending the (name, args) tuple
                        function_calls.append((func_name, part.function_call.args))
                        # Add the model's thinking to the history
                        AssistantMessages.append({
                            "role": "model",
                            "parts": [{"function_call": {"name": func_name, "args": part.function_call.args}}]
                        })
            
            # If there are no function calls, we have our final answer
            if not function_calls:
                final_text = response.text
                AssistantMessages.append({"role": "model", "parts": [{"text": final_text}]})
                return final_text
            
            # Execute the functions. This call is now fixed.
            results = await handle_function_calls(function_calls)
            
            # Add tool results back to the conversation
            for name, result in results:
                AssistantMessages.append({
                    "role": "tool", # Use "tool" role for function responses
                    "parts": [{
                        "function_response": {
                            "name": name,
                            "response": {"content": str(result)}
                        }
                    }]
                })
        except Exception as e:
            print(f"FATAL: An error occurred in the generate loop: {e}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, an unexpected error occurred."

if __name__ == "__main__":
    while True:
        prompt = input(">>> ")
        # To test this file directly, you still need asyncio.run here
        print(asyncio.run(generate(prompt=prompt)))