from .graph_connector import GraphConnector

class ComplianceService:
    
    @staticmethod
    def check_health():
        """
        Checks if the Graph DB is accessible.
        """
        return GraphConnector.verify_connection()

    @staticmethod
    def initialize_schema():
        """
        Creates constraints or initial indexes if needed.
        Reference: Could port over constraints from reference implementation later.
        """
        # Example of ensuring unique constraint
        # GraphConnector.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Rule) REQUIRE r.id IS UNIQUE")
        pass

    @staticmethod
    def get_all_rules():
        """
        Fetches all rules currently defined in the Graph.
        Assuming nodes labeled :Rule
        """
        query = "MATCH (r:Rule) RETURN r"
        return GraphConnector.run(query)

    @staticmethod
    def add_rule(name: str, description: str, rule_type: str):
        """
        Adds a rule node to the graph.
        """
        query = """
        MERGE (r:Rule {name: $name})
        SET r.description = $description,
            r.type = $rule_type,
            r.created_at = datetime()
        RETURN r
        """
        params = {
            "name": name, 
            "description": description, 
            "rule_type": rule_type
        }
        return GraphConnector.run(query, params)

    @staticmethod
    def add_gdpr_policy(service_name: str, data_types: list, purpose: str, region: str):
        """
        Creates a graph structure: (Service)-[:PROCESSES]->(Data)-[:LOCATED_IN]->(Region)
        """
        query = """
        MERGE (s:Service {name: $service_name})
        MERGE (p:Purpose {name: $purpose})
        MERGE (reg:Region {name: $region})
        
        MERGE (s)-[:HAS_PURPOSE]->(p)
        
        FOREACH (dt IN $data_types |
            MERGE (d:DataType {name: dt})
            MERGE (s)-[:PROCESSES]->(d)
            MERGE (d)-[:STORED_IN]->(reg)
        )
        
        RETURN s, p, reg
        """
        params = {
            "service_name": service_name,
            "data_types": data_types,
            "purpose": purpose,
            "region": region
        }
        return GraphConnector.run(query, params)

    @staticmethod
    def add_org_policy(role: str, action: str, resource: str, effect: str):
        """
        Creates (Role)-[:PERFORMED]->(Action)-[:ON]->(Resource) with effect property.
        """
        query = """
        MERGE (r:Role {name: $role})
        MERGE (act:Action {name: $action})
        MERGE (res:Resource {name: $resource})
        
        MERGE (r)-[perm:CAN_PERFORM]->(act)
        SET perm.effect = $effect
        
        MERGE (act)-[:AFFECTS]->(res)
        
        RETURN r, act, res
        """
        params = {
            "role": role,
            "action": action,
            "resource": resource,
            "effect": effect
        }
        return GraphConnector.run(query, params)

    @staticmethod
    def add_sre_rule(service: str, env: str, action: str, risk: str, needs_approval: bool):
        """
        Creates (Service)-[:DEPLOYED_IN]->(Env) and (Action)-[:HAS_RISK]->(RiskLevel)
        """
        query = """
        MERGE (s:Service {name: $service})
        MERGE (e:Environment {name: $env})
        MERGE (act:Action {name: $action})
        MERGE (r:Risk {name: $risk})
        
        MERGE (s)-[:RUNS_IN]->(e)
        MERGE (act)-[:HAS_RISK]->(r)
        
        MERGE (s)-[rel:ALLOWS_ACTION]->(act)
        SET rel.needs_approval = $needs_approval
        
        RETURN s, e, act, r
        """
        params = {
            "service": service,
            "env": env,
            "action": action,
            "risk": risk,
            "needs_approval": needs_approval
        }
        return GraphConnector.run(query, params)

    @staticmethod
    def get_compliance_context() -> str:
        """
        Fetches all active rules, policies, and safety checks and formats them 
        into a natural language string for the LLM.
        """
        context = ["COMPLIANCE AND SAFETY RULES (YOU MUST ADHERE TO THESE):"]
        
        # 1. Fetch General Rules
        try:
            rules = ComplianceService.get_all_rules()
            if rules:
                context.append("\n-- GENERAL RULES --")
                for r in rules:
                    # Neo4j returns a dictionary structure inside the Record
                    node = r['r']
                    context.append(f"- [{node.get('type', 'INFO')}] {node.get('name')}: {node.get('description')}")
        except Exception as e:
            print(f"Error fetching rules: {e}")

        # 2. Fetch Org Policies (simplified query for context)
        # Assuming we just dump the relationships: (Role)-[CAN_PERFORM]->(Action)
        try:
            query = "MATCH (r:Role)-[rel:CAN_PERFORM]->(a:Action) RETURN r.name, rel.effect, a.name"
            policies = GraphConnector.run(query)
            if policies:
                context.append("\n-- ORGANIZATIONAL POLICIES --")
                for p in policies:
                    context.append(f"- Role '{p['r.name']}' is {p['rel.effect']} to perform '{p['a.name']}'")
        except Exception as e:
            print(f"Error fetching org policies: {e}")
            
        # 3. Fetch SRE Risks
        try:
            query = "MATCH (s:Service)-[:RUNS_IN]->(e:Environment), (s)-[rel:ALLOWS_ACTION]->(a:Action)-[:HAS_RISK]->(r:Risk) RETURN s.name, e.name, a.name, r.name, rel.needs_approval"
            risks = GraphConnector.run(query)
            if risks:
                context.append("\n-- SRE SAFETY RISKS --")
                for risk in risks:
                     approval_txt = "REQUIRES APPROVAL" if risk['rel.needs_approval'] else "Automated"
                     context.append(f"- Action '{risk['a.name']}' on '{risk['s.name']}' in '{risk['e.name']}': Risk {risk['r.name']} [{approval_txt}]")
        except Exception as e:
            print(f"Error fetching SRE risks: {e}")

        return "\n".join(context)
