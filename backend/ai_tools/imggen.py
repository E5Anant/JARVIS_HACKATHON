import base64
import mimetypes
import os
from google import genai
from google.genai import types
from unisonai import BaseTool, Field
from ui.UI import create_image_widget

def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")

class GenerateImageTool(BaseTool):
    name = "Generate Image"
    description = "Generate an image based on a prompt"
    params = [
        Field(name="prompt", description="str: High Quality Prompt to generate image"),
    ]

    def _run(self, prompt: str):
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

        model = "gemini-2.0-flash-preview-image-generation"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
            response_mime_type="text/plain",
        )

        file_index = 0
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                file_name = f"outputs/image"
                file_index += 1
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                save_binary_file(f"{file_name}{file_extension}", data_buffer)
                create_image_widget(f"{file_name}{file_extension}")
            else:
                print(chunk.text)
        return "Image generated in 'outputs/image' successfully generated and opened on screen"

if __name__ == "__main__":
    while True:
        prompt = input(">>> ")
        GenerateImageTool._run(prompt)