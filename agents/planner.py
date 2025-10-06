import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class PlannerAgent:
    """
    An agent that takes a user query and generates a structured SRE plan in JSON format.
    """
    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever
        
        # --- Prompt Template Definition ---
        system_prompt = """
        You are an expert SRE (Site Reliability Engineer) and System Administrator planning agent.
        Your sole purpose is to convert a user's request into a structured JSON object. Your response MUST be ONLY the JSON object, with no additional text, explanations, or markdown formatting.

        **JSON Output Structure:**
        The JSON object must have two top-level keys: "env" and "plan".

        1.  **"env" (Object):**
            -   Extract key variables from the user's query (Git URLs, project names, etc.).
            -   Store these as key-value pairs.

        2.  **"plan" (Array of Objects):**
            -   Create a logical, sequential, step-by-step plan.
            -   **CRITICAL - Install Dependencies First:** Before using any tool (like `git`, `node`, `npm`, `pm2`, `nginx`), you MUST add the steps to install it first. Assume the server is a minimal installation.
            -   **CRITICAL - Use the Correct Package Manager:** Pay close attention to the `Server OS`. Use `sudo dnf install -y` for Fedora and `sudo apt install -y` for Ubuntu.
            -   **CRITICAL - Use `env` Variables:** Commands in your plan MUST use variables from the "env" object with the `{{VARIABLE_NAME}}` syntax.

        **Example User Query:** "Server OS: Fedora\n\nTask: Deploy my 'sirius' project from https://github.com/my-user/sirius.git. It's a node app."

        **Example JSON Output:**
        ```json
        {{
          "env": {{
            "GIT_REPO_URL": "[https://github.com/my-user/sirius.git](https://github.com/my-user/sirius.git)",
            "PROJECT_DIR": "sirius"
          }},
          "plan": [
            {{
              "step": 1,
              "command": "sudo dnf install -y git"
            }},
            {{
              "step": 2,
              "command": "sudo dnf install -y nodejs"
            }},
            {{
              "step": 3,
              "command": "git clone {{GIT_REPO_URL}} {{PROJECT_DIR}}"
            }},
            {{
              "step": 4,
              "command": "cd {{PROJECT_DIR}}"
            }},
            {{
              "step": 5,
              "command": "npm install"
            }},
            {{
              "step": 6,
              "command": "npm start"
            }}
          ]
        }}
        ```

        **CONTEXT FROM DOCUMENTATION:**
        {context}

        **USER QUERY:**
        {query}

        **YOUR JSON RESPONSE:**
        """
        self.prompt = ChatPromptTemplate.from_messages([("system", system_prompt)])
        
        # --- LCEL Chain Definition ---
        self.chain = (
            {
                "context": self.retriever | self._format_docs,
                "query": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _format_docs(self, docs):
        """Helper function to format retrieved documents for the prompt."""
        if not docs:
            return "No relevant context found in documentation."
        return "\n\n".join(doc.page_content for doc in docs)

    def generate_plan(self, query: str):
        """
        Takes a user query, invokes the LLM chain, and returns the parsed JSON plan.
        """
        print(f"\n--- Generating Plan for Query: '{query}' ---")
        try:
            result_str = self.chain.invoke(query)
            
            # Clean up potential markdown formatting from the LLM output
            if result_str.strip().startswith("```json"):
                result_str = result_str.strip()[7:-3].strip()

            plan_json = json.loads(result_str)
            print("\n--- Generated SRE Plan (JSON) ---")
            print(json.dumps(plan_json, indent=2))
            return plan_json
        except json.JSONDecodeError:
            print("\n--- Error: Planner LLM did not return valid JSON. ---")
            print("Raw LLM Output:")
            print(result_str)
            return None
        except Exception as e:
            print(f"\nAn unexpected error occurred during planning: {e}")
            return None