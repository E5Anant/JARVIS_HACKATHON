import sys
import re
import yaml
import json
import os
import asyncio
import inspect
from typing import Any, List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

import colorama
from colorama import Fore, Style

# Assuming these are from your library, otherwise define them
from unisonai.llms import Gemini
from unisonai.prompts.individual import INDIVIDUAL_PROMPT

colorama.init(autoreset=True)

class Single_Agent:
    def __init__(self,
                 llm: Gemini,
                 identity: str,
                 description: str,
                 verbose: bool = True,
                 tools: list[Any] = [],
                 output_file: str = None,
                 history_folder: str = "history"):
        
        self.llm = llm
        self.identity = identity
        self.description = description
        self.verbose = verbose
        self.output_file = output_file
        self.history_folder = history_folder
        self.rawtools = tools
        
        # --- Performance Optimizations ---
        # 1. Pre-compile regex for faster matching inside the recursive loop
        self.yaml_pattern = re.compile(r"```(?:yaml|yml)(.*?)```", re.DOTALL)
        
        # 2. Instantiate tools once and create a dictionary for O(1) lookup
        self.tool_map: Dict[str, Any] = {}
        if tools:
            for tool in self.rawtools:
                tool_instance = tool() if isinstance(tool, type) else tool
                self.tool_map[tool_instance.name.lower()] = tool_instance
        
        # 3. Use a more efficient method to build the tool string
        self.tools_string = self._create_tools_string()

        # Set up history file path for later use
        if self.history_folder:
            os.makedirs(self.history_folder, exist_ok=True)
            self.history_file_path = os.path.join(self.history_folder, f"{self.identity}.json")
        else:
            self.history_file_path = None
            
        # This will hold our background task manager
        self.executor: Optional[ThreadPoolExecutor] = None

    def _create_tools_string(self) -> str:
        """Efficiently creates the formatted string for tools."""
        if not self.tool_map:
            return "No Provided Tools"
        
        # Using a list join is faster than repeated string concatenation
        tool_parts = []
        for i, tool_instance in enumerate(self.tool_map.values()):
            params_str = ' '.join(p.format() for p in tool_instance.params)
            tool_parts.append(
                f"-TOOL{i+1}:\n"
                f"  NAME: {tool_instance.name}\n"
                f"  DESCRIPTION: {tool_instance.description}\n"
                f"  PARAMS: {params_str}"
            )
        return "\n".join(tool_parts)

    # --- Background I/O Functions ---
    def _save_history_in_background(self):
        """Task to save history file in a separate thread."""
        if self.history_file_path and self.llm.messages:
            try:
                # Make a thread-safe copy of messages
                messages_to_save = list(self.llm.messages)
                with open(self.history_file_path, "w", encoding="utf-8") as f:
                    json.dump(messages_to_save, f, indent=4)
            except Exception as e:
                print(f"{Fore.RED}Background history save failed: {e}")

    def _write_output_in_background(self, content: str):
        """Task to write final result in a separate thread."""
        if self.output_file:
            try:
                with open(self.output_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                print(f"{Fore.RED}Background output write failed: {e}")

    # Your original helper functions, kept for logic consistency
    def _ensure_dict_params(self, params_data):
        if isinstance(params_data, str):
            params_data = params_data.strip()
            try:
                return json.loads(params_data)
            except json.JSONDecodeError:
                try:
                    parsed = yaml.safe_load(params_data)
                    return parsed if isinstance(parsed, dict) else {"value": parsed}
                except yaml.YAMLError:
                    return {"raw_input": params_data}
        return params_data if params_data is not None else {}

    def _execute_tool(self, name: str, params: dict):
        tool = self.tool_map.get(name.lower())
        if not tool:
            raise ValueError(f"Tool '{name}' not found.")

        method = tool._run
        sig = inspect.signature(method)
        try:
            bound = sig.bind_partial(**params)
        except TypeError as e:
            raise ValueError(f"Invalid params for tool '{name}': {e}")

        filtered = bound.arguments
        if self.verbose:
            kind = 'ASYNC' if inspect.iscoroutinefunction(method) else 'SYNC'
            print(Fore.CYAN + f"Status: Executing {kind} Tool ({name}) with params {filtered}...")

        if inspect.iscoroutinefunction(method):
            return asyncio.run(method(**filtered))
        else:
            return method(**filtered)


    def _recursive_unleash(self, task: str) -> str:
        """
        This is the core recursive logic from your original code, but without
        the slow file I/O and re-initialization.
        """
        # --- LLM Call (The main blocking operation) ---
        response = self.llm.run(task, save_messages=True)
        
        # --- PARALLEL I/O ---
        # Submit the history save task to the background and continue immediately
        if self.executor:
            self.executor.submit(self._save_history_in_background)

        if self.verbose:
            print("Response:")
            print(response)

        # --- Parse and Act (Your original logic) ---
        yaml_match = self.yaml_pattern.search(response)
        if not yaml_match:
            return response

        try:
            data = yaml.safe_load(yaml_match.group(1).strip())
            assert "thoughts" in data and "name" in data and "params" in data
        except (yaml.YAMLError, AssertionError):
            print(Fore.RED + "YAML block found, but it doesn't match the expected format.")
            return response

        thoughts, name, params_raw = data["thoughts"], data["name"], data["params"]
        params = self._ensure_dict_params(params_raw)
        
        if self.verbose:
            print(f"{Fore.MAGENTA}Thoughts: {thoughts[:120]}...\n{Fore.GREEN}Using Tool ({name})\n{Fore.LIGHTYELLOW_EX}Params: {params}")

        # --- Action Dispatch (Your original logic) ---
        if name == "ask_user":
            question = params.get("question", str(params))
            print("QUESTION: " + question)
            return self._recursive_unleash(input("You: "))

        elif name == "pass_result":
            result = str(params.get("result", params))
            print("RESULT: " + result)
            # Submit final output write to background
            if self.executor:
                self.executor.submit(self._write_output_in_background, result)
            return result

        else: # Tool call
            try:
                tool_response = self._execute_tool(name, params)
                print("Tool Response:")
                print(tool_response)
                return self._recursive_unleash(f"Here is your tool response:\n\n{str(tool_response)}")
            except Exception as e:
                print(f"{Fore.RED}Error executing tool '{name}': {e}")
                # Provide feedback to the LLM about the error
                return self._recursive_unleash(f"The tool '{name}' failed with error: {e}")

    def unleash(self, task: str) -> str:
        """
        Public entry point. Sets up the environment ONCE, then starts the
        fast, recursive loop.
        """
        # --- 1. SETUP (Done ONCE per task) ---
        messages = []
        if self.history_file_path:
            try:
                with open(self.history_file_path, "r", encoding="utf-8") as f:
                    messages = json.loads(f.read() or "[]")
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        
        # Configure LLM state for the entire task
        self.llm.reset()
        self.llm.__init__(
            messages=messages,
            model=self.llm.model,
            temperature=self.llm.temperature,
            system_prompt=INDIVIDUAL_PROMPT.format(
                identity=self.identity,
                description=self.description,
                user_task=task,
                tools=self.tools_string,
            ),
            max_tokens=self.llm.max_tokens,
            verbose=self.llm.verbose,
            api_key=self.llm.client.api_key if hasattr(self.llm, 'client') and hasattr(self.llm.client, 'api_key') else None
        )

        print(Fore.LIGHTCYAN_EX + "Status: Evaluating Task...\n")

        # --- 2. START RECURSION WITH PARALLEL I/O ---
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix='AgentIO') as executor:
            self.executor = executor
            # Start the fast recursive loop
            final_result = self._recursive_unleash(task)
            # The 'with' block ensures background tasks are given time to complete
            
        self.executor = None # Clean up executor
        return final_result