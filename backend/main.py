from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import engine, get_db

# Create tables (if not handled by migration tool, though init.sql usually handles it)
# models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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
