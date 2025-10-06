import os
import json
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from planner import PlannerAgent
from executor import ExecutorAgent
# Import the remote execution components
from remote_executor import build_ssh_backend_interactive, RemotePlanRunner

# --- 0. Load Environment Variables & Configuration ---
load_dotenv()
PERSIST_DIRECTORY = "rag_store"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PLANNER_LLM = "llama-3.1-8b-instant"
EXECUTOR_LLM = "llama-3.3-70b-versatile"

def run_agent_workflow():
    """
    Main function to orchestrate the Planner and Executor agents.
    """
    # --- 1. Initialize Shared Components ---
    print("--- Initializing Shared Components ---")
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={'device': 'cpu'})
    vectorstore = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding_model)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    planner_llm = ChatGroq(model=PLANNER_LLM, temperature=0)
    executor_llm = ChatGroq(model=EXECUTOR_LLM, temperature=0)
    print("Components initialized successfully.\n")

    # --- 2. Get User Query and Generate a Plan ---
    server_os = input("Enter the server OS for the plan (Ubuntu/Fedora): ").strip().capitalize()
    original_user_query = input("Query : ")
    user_query_with_context = f"Server OS: {server_os}\n\nTask: {original_user_query}"
    
    planner = PlannerAgent(llm=planner_llm, retriever=retriever)
    plan = planner.generate_plan(user_query_with_context)

    if not plan:
        print("\n--- Could not generate a plan. Halting execution. ---")
        return

    # --- 3. Choose Execution Target (Local vs. Remote) ---
    execution_target = input("Execute plan locally or on a remote server? [local/remote]: ").strip().lower()
    
    remote_runner = None
    if execution_target == 'remote':
        try:
            # Use the interactive function to get credentials and create an SSH backend
            backend = build_ssh_backend_interactive()
            print("\n--- Performing remote connectivity test... ---")
            backend.connect()
            code, out, err = backend.execute('echo "test"')
            if code == 0 and out.strip() == "test":
                print("[SUCCESS] Remote connection verified.\n")
                # Pass the backend and env to the RemotePlanRunner
                remote_runner = RemotePlanRunner(backend=backend, env=plan.get('env', {}))
            else:
                print(f"[FAILED] Could not verify remote connection. stderr: {err}")
                return
        except Exception as e:
            print(f"Failed to set up remote connection: {e}")
            return
    
    # --- 4. Execute the Plan ---
    print("\n--- Plan Generated. Handing off to Executor Agent. ---")
    executor = ExecutorAgent(
        plan_json=plan, 
        llm=executor_llm, 
        retriever=retriever,
        # Pass the remote runner if it was created, otherwise it's None for local execution
        remote_runner=remote_runner
    )
    executor.execute_plan()


if __name__ == "__main__":
    run_agent_workflow()