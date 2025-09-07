ai_expert = {
    "name": "AI_Expert",
    "description": "Delegates complex, specialized AI-related tasks like generating an image or performing detailed data analysis to a specialist AI model.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {
                "type": "STRING",
                "description": "A clear, specific, and self-contained prompt for the specialized AI task. For example: 'generate a photorealistic image of an astronaut riding a horse'."
            }
        },
        "required": ["prompt"]
    }
}

system_automator = {
    "name": "System_Automator",
    "description": "Automates tasks on the local computer system. Use this for actions like opening an application, executing a command line command, or managing files and folders.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {
                "type": "STRING",
                "description": "A clear command for the system automation. For example: 'open notepad' or 'list all files in the current directory'."
            }
        },
        "required": ["prompt"]
    }
}

web_crawler = {
    "name": "Web_Crawler",
    "description": "Handles all web-based tasks. Use this to get the content of a webpage, send an email, or interact with online services like WhatsApp.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {
                "type": "STRING",
                "description": "A clear instruction for the web task. For example: 'get the main text from the webpage at http://example.com' or 'send an email to test@example.com'."
            }
        },
        "required": ["prompt"]
    }
}

create_text_widget = {
    "name": "create_text_widget",
    "description": "Creates a visual text widget on the user's screen. This is the best tool for presenting long-form text, code snippets, or any information that is too long for a simple verbal response.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "text": {
                "type": "STRING",
                "description": "The main text content to be displayed in the widget."
            },
            "title": {
                "type": "STRING",
                "description": "An optional title for the text widget."
            }
        },
        "required": ["text"]
    }
}

Vision_tool = {
    "name": "VisionTool",
    "description": "Captures the user's screen or takes a picture with the webcam for analysis. Use mode='screen' for UI content, reading text on the screen, or summarizing visual elements on the desktop. Use mode='camera' for analyzing the user's real-world environment and objects nearby.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {
                "type": "STRING",
                "description": "A specific question or instruction for the analysis. For example: 'What text is in this window?', 'Describe the main objects on the desk', or 'Summarize the content of the screen'."
            },
            "mode": {
                "type": "STRING",
                "description": "The source of the image to analyze. Defaults to 'screen' if not specified.",
                "enum": ["screen", "camera"]
            }
        },
        "required": ["prompt", "mode"]
    }
}