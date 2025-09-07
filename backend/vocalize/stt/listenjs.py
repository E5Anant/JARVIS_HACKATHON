from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import warnings
import mtranslate as mt
# from time import sleep
import os

# warnings.filterwarnings("module")
# warnings.filterwarnings("error")
# warnings.filterwarnings("ignore")

env_vars = dotenv_values(".env")

HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

class ListenJS:
    def __init__(self):
       
        self.HtmlCode = str(HtmlCode).replace("recognition.lang = '';", f"recognition.lang = 'en';")

        with open('data\\voice.html', 'w') as file:
            file.write(HtmlCode)
            
        self.current_dir = os.getcwd()

        self.Link = f"{self.current_dir}/data/voice.html"

        self.chrome_options = Options()
        self.chrome_options.add_argument("--use-fake-ui-for-media-stream")
        self.chrome_options.add_argument("--use-fake-device-for-media-stream")
        self.chrome_options.add_argument("--headless=new")
        self.chrome_driver_path = ChromeDriverManager().install()
        self.service = Service(executable_path=self.chrome_driver_path)
        self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
        
    def QueryModifier(self, Query):
        new_query = Query.lower().strip()
        query_words = new_query.split()
        question_words = ['what', 'when', 'where', 'why', 'how', 'who', 'which', 'whom', 'can you', 'could you', 'would you', 'will you', 'may you', 'is it', 'are you', 'do you', 'did you', 'have you', 'has it', 'had you', 'should you', 'shall you', 'may i', 'can i', 'could i', 'would i', 'will i', 'is there', 'are there', 'do i', 'did i', 'have i', 'has it', 'had i', 'should i', 'shall i', 'may we', 'can we', 'could we', 'would we', 'will we', 'are we', 'do we', 'did we', 'have we', 'has it', 'had we', 'should we', 'shall we', 'may they', 'can they', 'could they', 'would they', 'will they', 'are they', 'do they', 'did they', 'have they', 'has it', 'had they', 'should they', 'shall they', 'may he', 'can he', 'could he', 'would he', 'will he', 'is he', 'are they', 'do they', 'did they', 'has he', 'had he', 'should he', 'shall he', 'may she', 'can she', 'could she', 'would she', 'will she', 'is she', 'are she', 'do she', 'did she', 'has she', 'had she', 'should she', 'shall she']
        
        if any(word +  " " in new_query for word in question_words):
            if query_words[-1][-1] in ['.', '?', '!']:
                new_query = new_query[:-1] + '?'
            else:
                new_query += '.'
            
        else:
            if query_words[-1][-1] in ['.', '?', '!']:
                new_query = new_query[:-1] + '.'
            else:
                new_query += '.'
            
        return new_query.capitalize()

    def UniversalTranslator(Text):
        english_translate = mt.translate(Text, "en",'auto')
        return english_translate.capitalize()
    
    def SpeechRecognition(self):
        self.driver.get(self.Link)
        # sleep(10)
        self.driver.find_element(by=By.ID, value='start').click()
        print("Listening...", end='\r', flush=True) # Clear the "Listening..." line
        
        while True:
        
            try:
                Text=self.driver.find_element(by=By.ID, value='output').text
                if Text:
                    self.driver.find_element(by=By.ID, value='end').click()
                    # print("You: " + Text)
                    
                    Text = self.QueryModifier(Text)
                    print("You: " + Text)
                    return Text
                    
            except Exception as e:
                pass
            

if __name__=="__main__":
    stt = ListenJS()
    while True:
        stt.SpeechRecognition()