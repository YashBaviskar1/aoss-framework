from langchain_groq import ChatGroq
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
import os
load_dotenv()
GROQ_API_KEY = os.getenv("API_KEY")

# llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

# response = llm.invoke("Hello There! What is Critical Theory?")

template = """
You are an execuation agent of a Multi Agent System which handles the terminal of a server and has access to it's terminal, 
you will respond in JSON format only.

You are given a Task, and to execuate that tasks all the terminal commands 

Example of the input and the output you have to provide :
Input : 
{{
Question : "update system"
}}

Your Output : 
{{
Commands = ['sudo apt update', 'sudo apt upgrade']
}}


Question Query :
{{
Question : {question}
}}


"""
prompt = PromptTemplate.from_template(template=template)
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

response = llm.invoke(prompt.format(question="install Python"))
print(response.content)