from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from .compliance_service import ComplianceService

router = APIRouter(
    prefix="/api/compliance",
    tags=["compliance"],
    responses={404: {"description": "Not found"}},
)

# --- Pydantic Models ---
class RuleCreate(BaseModel):
    name: str
    description: str
    rule_type: str # e.g., "GDPR", "SRE", "ORG"

class RuleResponse(BaseModel):
    name: str
    description: str
    type: str

class GdprRequest(BaseModel):
    service_name: str
    purpose: str
    data_types: List[str]
    region: str

class OrgPolicyRequest(BaseModel):
    role: str
    action: str
    resource: str
    effect: str

# --- Endpoints ---

@router.get("/health")
def health_check():
    """
    Checks connection to Neo4j.
    """
    is_connected = ComplianceService.check_health()
    if is_connected:
        return {"status": "connected", "database": "neo4j"}
    else:
        raise HTTPException(status_code=503, detail="Neo4j not reachable")

@router.get("/rules")
def list_rules():
    """
    Returns lists of rules from the graph.
    """
    try:
        results = ComplianceService.get_all_rules()
        # Flatten structure: result is [{'r': {'name':..., 'prop':...}}]
        rules = [r['r'] for r in results if 'r' in r]
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rules")
def create_rule(rule: RuleCreate):
    """
    Creates a new compliance rule in the graph.
    """
    try:
        results = ComplianceService.add_rule(rule.name, rule.description, rule.rule_type)
        return {"status": "created", "rule": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seed")
def seed_rules():
    """
    Populates the graph with default example rules.
    """
    try:
        defaults = [
            ("GDPR-1", "Data must be encrypted at rest", "required"),
            ("GDPR-2", "User consent is required for tracking", "required"),
            ("SRE-1", "No deployments on Friday", "forbidden"),
            ("SRE-2", "All services must have health checks", "required"),
            ("ORG-1", "Only Admin can delete users", "forbidden")
        ]
        
        created = []
        for name, desc, r_type in defaults:
            ComplianceService.add_rule(name, desc, r_type)
            created.append(name)
            
        return {"status": "seeded", "count": len(created), "rules": created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gdpr")
def add_gdpr_policy(request: GdprRequest):
    """
    Adds a GDPR processing activity to the graph.
    """
    try:
        ComplianceService.add_gdpr_policy(
            request.service_name,
            request.data_types,
            request.purpose,
            request.region
        )
        return {"status": "success", "message": "GDPR policy added to graph"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/org-policy")
def add_org_policy(request: OrgPolicyRequest):
    """
    Adds an Organizational Access policy to the graph.
    """
    try:
        ComplianceService.add_org_policy(
            request.role,
            request.action,
            request.resource,
            request.effect
        )
        return {"status": "success", "message": "Org policy added to graph"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
