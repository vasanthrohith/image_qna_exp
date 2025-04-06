from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import PIL.Image

load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# image = PIL.Image.open(r'C:\Users\CVHS ADMIN\Documents\github_repos\image_qna\source_images\SID.jpg')


def get_image_qna():
    question = input("Enter your question: ")
    image = PIL.Image.open(r'C:\Users\CVHS ADMIN\Documents\github_repos\image_qna\source_images\SID_modified_rects.jpg')

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[f"Answer the user question by focusing on the marked 'red color rectange' in the image \n\n user question : {question}", image])

    print(response.text)