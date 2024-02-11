import os

from openai import OpenAI
import google.generativeai as genai


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


class RemoteModelSession:
    def generate(self, message):
        return ''


class OpenAIGpt4(RemoteModelSession):
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        print(api_key)
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate(self, message):
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": message
                }],
            model="gpt-4"
        )
        return response['choices'][0]['message']['content']


class Gemini(RemoteModelSession):
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')

    def generate(self, message):
        response = self.model.generate_content(message)
        return response.text
