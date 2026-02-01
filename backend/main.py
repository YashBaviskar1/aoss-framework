from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models
import models
import models
import schemas
from database import engine, get_db
from agents.planner import PlannerAgent
from agents.executor import RemoteExecutor
import monitoring 
from fastapi.responses import StreamingResponse
import json
from compliance.router import router as compliance_router

# Create tables (if not handled by migration tool, though init.sql usually handles it)
models.Base.metadata.create_all(bind=engine)

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Include Routers
app.include_router(monitoring.router)
app.include_router(compliance_router)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Vite/React default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AOSS Framework Backend API"}

@app.get("/api/user/{user_id}/status", response_model=schemas.UserStatus)
def check_user_status(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        return {"exists": True, "username": user.username}
    return {"exists": False, "username": None}

@app.post("/api/profile", status_code=status.HTTP_201_CREATED)
def create_profile(profile: schemas.ProfileSubmit, db: Session = Depends(get_db)):
    try:
        # 1. Create or Update User
        db_user = db.query(models.User).filter(models.User.id == profile.userId).first()
        if not db_user:
            db_user = models.User(
                id=profile.userId,
                email=profile.email,
                username=profile.userName
            )
            db.add(db_user)
            # Do not commit here yet to ensure atomicity
            db.flush() 
        else:
            # Update name if changed
            if db_user.username != profile.userName:
                db_user.username = profile.userName
                db.add(db_user)
                db.flush()

        # 2. Add Servers
        created_servers = []
        for s_data in profile.servers:
            # Check if server tag exists for this user
            existing_server = db.query(models.Server).filter(
                models.Server.user_id == profile.userId, 
                models.Server.server_tag == s_data.serverTag
            ).first()

            if existing_server:
                continue
                
            new_server = models.Server(
                user_id=profile.userId,
                server_tag=s_data.serverTag,
                ip_address=str(s_data.ipAddress), # Pydantic IPvAnyAddress needs to be converted to str for SQLAlchemy INET
                hostname=s_data.hostname,
                ssh_username=s_data.sshUsername
            )

            # Handle Key File logic here (omitted for brevity in this replace, assuming helper or inline)
            # Re-adding the key logic below within the loop

            if s_data.sshKeyContent:
                import os
                keys_dir = "keys"
                if not os.path.exists(keys_dir):
                    os.makedirs(keys_dir)
                
                safe_tag = "".join(x for x in s_data.serverTag if x.isalnum() or x in "-_")
                filename = f"{profile.userId}_{safe_tag}.{s_data.selectedFileType or 'pem'}"
                file_path = os.path.join(keys_dir, filename)
                
                with open(file_path, "w") as f:
                    f.write(s_data.sshKeyContent)
                
                new_server.ssh_key_path = file_path

            db.add(new_server)
            created_servers.append(new_server)
        
        db.commit()
        return {"message": "Profile created successfully", "servers_added": len(created_servers)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/dashboard/{user_id}", response_model=schemas.DashboardData)
def get_dashboard_data(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    servers = db.query(models.Server).filter(models.Server.user_id == user_id).all()
    
    # Map to schema
    server_list = []
    for s in servers:
        server_list.append(schemas.ServerResponse(
            id=s.id,
            server_tag=s.server_tag,
            ip_address=str(s.ip_address),
            hostname=s.hostname,
            # We don't verify connection here, filtering it out for speed. 
            # Client calls test-connection separately.
        ))

    return {
        "user_name": user.username,
        "servers": server_list
    }

@app.delete("/api/reset", status_code=status.HTTP_200_OK)
def reset_database(db: Session = Depends(get_db)):
    try:
        # Delete all users (cascades to servers)
        db.query(models.User).delete()
        db.commit()

        # Clear keys directory
        import os
        import glob
        keys_dir = "keys"
        if os.path.exists(keys_dir):
            files = glob.glob(os.path.join(keys_dir, "*"))
            for f in files:
                try:
                    os.remove(f)
                except OSError as e:
                    print(f"Error checking {f}: {e}")

        return {"message": "Database and keys reset successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/server/{server_id}/test-connection")
def test_connection(server_id: str, db: Session = Depends(get_db)):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
        
    import paramiko
    import io
    
    # Setup client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        connect_kwargs = {
            "hostname": str(server.ip_address),
            "username": server.ssh_username,
            "timeout": 5
        }
        
        # Handle Keys/Password
        if server.ssh_key_path:
            # Paramiko needs a file path or file-like object.
            # Assuming ssh_key_path is an absolute path on this server.
            connect_kwargs["key_filename"] = server.ssh_key_path
        elif server.ssh_password_encrypted:
            # Note: Decrypt here if stored encrypted
            connect_kwargs["password"] = server.ssh_password_encrypted
        else:
            # Try connecting without auth (rare) or maybe key is in default loc
            pass

        client.connect(**connect_kwargs)
        
        # Run simple command
        stdin, stdout, stderr = client.exec_command('echo "Connection Successful"', timeout=5)
        output = stdout.read().decode().strip()
        
        client.close()
        
        if output == "Connection Successful":
            return {"status": "Online", "message": "Successfully connected"}
        else:
            return {"status": "Offline", "message": "Connected but unexpectedly failed check"}
            
    except Exception as e:
        return {"status": "Offline", "message": str(e)}

# --- Orchestration Endpoints ---

@app.post("/api/chat/plan", response_model=schemas.PlanResponse)
def generate_plan(request: schemas.PlanRequest, db: Session = Depends(get_db)):
    print(f"Request: {request}") # Debug log
    
    # Fetch Server Context
    server = db.query(models.Server).filter(models.Server.id == request.serverId).first()
    server_context = server.server_metadata if server else {}

    # Initialize planner
    planner = PlannerAgent()
    # Pass model, agent_type, AND context
    plan_json = planner.generate_plan(
        query=request.query, 
        model=request.model, 
        agent_type=request.agent_type,
        server_context=server_context
    )
    
    if "error" in plan_json:
        raise HTTPException(status_code=500, detail=plan_json["error"])
        
    return {"plan": plan_json.get("plan", [])}


@app.post("/api/chat/execute")
def execute_plan_stream(request: schemas.ExecuteRequest, db: Session = Depends(get_db)):
    # 1. Fetch Server
    server = db.query(models.Server).filter(models.Server.id == request.serverId).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    def execution_generator():
        # 2. Initialize Executor inside generator to keep scope
        executor = RemoteExecutor(
            host=str(server.ip_address),
            user=server.ssh_username,
            key_path=server.ssh_key_path,
            password=server.ssh_password_encrypted
        )
        
        execution_queue = request.plan.copy()
        results = []
        final_status = "Success"
        
        planner = PlannerAgent()
        max_retries = 3
        current_retries = 0

        try:
            executor.connect()
            
            # --- THE SMART LOOP ---
            while execution_queue:
                current_step = execution_queue.pop(0) 
                
                # Notify: Step Started
                yield json.dumps({
                    "type": "step_start",
                    "step": current_step.step,
                    "command": current_step.command
                }) + "\n"

                # Execute
                step_result = executor.execute_step(current_step.command)
                step_result["step"] = current_step.step 
                
                if step_result["exit_code"] == 0:
                    results.append(step_result)
                    # Notify: Step Success
                    yield json.dumps({
                        "type": "step_result",
                        "status": "success",
                        "result": step_result
                    }) + "\n"
                else:
                    results.append(step_result)
                    
                    # Notify: Step Failed
                    yield json.dumps({
                        "type": "step_result",
                        "status": "failure",
                        "result": step_result
                    }) + "\n"

                    if current_retries < max_retries:
                        print(f"⚠️ Step failed: {current_step.command}. Attempting Self-Heal...")
                        
                        # Notify: Healing Start
                        yield json.dumps({
                            "type": "healing_start",
                            "stderr": f"Command '{current_step.command}' failed. Consulting Planner..."
                        }) + "\n"
                        
                        fix_data = planner.generate_fix(
                            original_query=request.query,
                            failed_command=current_step.command,
                            error_output=step_result["stderr"],
                            model="llama-3.3-70b-versatile" 
                        )
                        
                        new_steps_data = fix_data.get("plan", [])
                        
                        if new_steps_data:
                            # Notify: Healing Plan Generated
                            yield json.dumps({
                                "type": "healing_plan",
                                "stdout": json.dumps(new_steps_data, indent=2)
                            }) + "\n"
                            
                            recovery_steps = [
                                schemas.PlanStep(
                                    step=999, 
                                    command=s["command"],
                                    description=f"Recovery: {s.get('description', 'Fixing error')}"
                                ) for s in new_steps_data
                            ]
                            
                            execution_queue = recovery_steps + execution_queue
                            current_retries += 1
                            continue
                    
                    final_status = "Failed"
                    break 

        except Exception as e:
            final_status = "Failed"
            import traceback
            traceback.print_exc()
            err_res = {
                "command": "System Execution Error",
                "exit_code": 999,
                "stdout": "",
                "stderr": f"An error occurred: {str(e)}",
                "status": "Failed"
            }
            results.append(err_res)
            yield json.dumps({
                "type": "error",
                "result": err_res
            }) + "\n"
            
        finally:
            if 'executor' in locals():
                executor.close()

        # 4. Generate Summary & UPDATE KNOWLEDGE BASE
        agent_summary = None
        if results:
            try:
                # Notify: Summarizing
                yield json.dumps({"type": "summarizing"}) + "\n"
                
                # A. Summary
                agent_summary = planner.summarize_execution(
                    query=request.query,
                    results=results,
                    model="llama-3.3-70b-versatile"
                )
                
                # B. Update Knowledge Base (The Memory)
                current_metadata = server.server_metadata or {}
                new_metadata = planner.update_knowledge_base(
                    current_context=current_metadata,
                    execution_logs=results,
                    model="llama-3.3-70b-versatile"
                )
                
                # We need a new session context to update DB safely inside generator? 
                # Actually, the 'server' object is attached to 'db' session passed in Depends(get_db).
                # But 'yield' suspends execution. AnyIO/FastAPI threading might be tricky with db session lifespan.
                # However, usually the request session is open until response closes.
                # We should use a fresh session or careful handling. 
                # For simplicity here, we assume the session is valid or re-query if needed.
                # Re-querying is safer to avoid detached instance issues.
                
                # Use a separate temporary DB session for the update to avoid conflicts with streaming response transaction
                # (FastAPI Depends(get_db) usually closes after yield... wait, StreamingResponse works differently)
                # We will try using the existing 'db' session. If it fails, we handle it.
                
                server.server_metadata = new_metadata
                db.add(server)
                db.commit() # Commit the new state

                # Notify: Summary Ready
                yield json.dumps({
                    "type": "agent_summary",
                    "content": agent_summary
                }) + "\n"

            except Exception as e:
                print(f"Post-execution processing failed: {e}")

        # 5. Save Logs
        new_log = models.ExecutionLog(
            user_id=server.user_id,
            server_id=server.id,
            query=request.query,
            plan=[step.model_dump() for step in request.plan],
            execution_results=results,
            agent_summary=agent_summary,
            status=final_status
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        # Final Event
        yield json.dumps({
            "type": "complete",
            "log_id": str(new_log.id),
            "final_status": final_status
        }) + "\n"

    return StreamingResponse(execution_generator(), media_type="application/x-ndjson")

@app.get("/api/chat/history/{server_id}", response_model=schemas.ExecutionHistory)
def get_execution_history(server_id: str, db: Session = Depends(get_db)):
    logs = db.query(models.ExecutionLog)\
        .filter(models.ExecutionLog.server_id == server_id)\
        .order_by(models.ExecutionLog.created_at.desc())\
        .all()
    return {"logs": logs}
