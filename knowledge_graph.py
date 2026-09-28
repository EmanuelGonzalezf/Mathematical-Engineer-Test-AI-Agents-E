"""
knowledge_graph.py
"""

KG: dict = {
    "hierarchy": {
        "Role": {
            "has_role_category": "Ownership Role",
        },
        "Ownership Role": {
            "has_role_type": ["GBR", "ZGBR"],
        },
    },
    "role_types": {
        "GBR": {
            "full_name": "Global Business Role",
            "access_model": "persistent",
            "session_verification": False,
            "description": (
                "Grants broad, persistent access across the organization. "
                "Access is validated at assignment time and does not require "
                "per-session re-verification."
            ),
            "differs_from": "ZGBR",
        },
        
        "ZGBR": {
            "full_name": "Zero Trust Global Business Role",
            "access_model": "session-based",
            "session_verification": True,
            "description": (
                "Grants access across the organization, but requires "
                "per-session verification. Access is validated at assignment "
                "time and re-verified for each session."
            ),
            "differs_from": "GBR",
        },
    },
    "documents": [
        {
            "source_id": "Policy-Doc-GBR-001",
            "title":     "GBR Access Policy",
            "content":   (
                "A Global Business Role (GBR) grants broad, persistent access "
                "to resources across the organization. Access is validated at "
                "the time of role assignment and does not require per-session "
                "verification."
            ),
            "keywords":  ["GBR", "global business role", "broad", "persistent"],
        },
        {
            "source_id": "Policy-Doc-ZGBR-002",
            "title":     "ZGBR Access Policy",
            "content":   (
                "A Zero-Trust Global Business Role (ZGBR) enforces per-session "
                "verification via MFA or just-in-time (JIT) approval. Used for "
                "privileged access to sensitive systems."
            ),
            "keywords":  ["ZGBR", "zero trust", "per-session", "JIT", "MFA"],
        },
        {
            "source_id": "Policy-Doc-CMP-003",
            "title":     "GBR vs ZGBR Comparison",
            "content":   (
                "The key distinction between a GBR and a ZGBR is access persistence. "
                "A GBR provides standing access that does not require re-validation "
                "per session. A ZGBR enforces real-time, per-session verification "
                "aligned with zero-trust principles. ZGBR is typically assigned to "
                "roles with elevated data sensitivity."
            ),
            "keywords":  ["difference", "compare", "comparison", "GBR", "ZGBR", "vs"],
       },
        {   
            "source_id": "Policy-Doc-Access-Review-004",
            "title":     "Access Review Process",
            "content":   (
                "Access reviews are conducted periodically to ensure that users "
                "have appropriate access to resources. Reviewers evaluate user "
                "access based on role requirements and compliance standards. "
                "Users may be required to justify their access or request "
                "additional permissions during the review process."
            ),
            "keywords":  ["access review", "review process", "compliance", "permissions"],

        },
        {
            "source_id": "Policy-Doc-Access-005",
            "title":     "Access Review Process",
            "content":   (
                "The access review process involves evaluating each user's "
                "current roles, checking for any changes in job responsibilities, "
                "and ensuring that access is aligned with the principle of least "
                "privilege. Reviewers must document their findings and submit "
                "their recommendations for approval or revocation."
            ),
            "keywords":  ["access review", "process", "evaluation", "least privilege"],
        },        

    ],
    "users": {
        "Priya": {
            "owns":       ["GBR-1234"],
            "role_type":  "GBR",
            "department": "Engineering",
            "review_history": [
                {"date": "2024-01-15", "status": "APPROVED", "reviewer": "Alice"},
                {"date": "2024-07-10", "status": "APPROVED", "reviewer": "Bob"},
                {"date": "2025-01-20", "status": "PENDING",  "reviewer": None},
            ],
        },
        "Alex": {
            "owns":       ["ZGBR-5678"],
            "role_type":  "ZGBR",
            "department": "Finance",
            "review_history": [
                {"date": "2024-02-05", "status": "APPROVED", "reviewer": "Charlie"},
                {"date": "2024-08-12", "status": "REVOKED",  "reviewer": "Dana"},
                {"date": "2025-02-18", "status": "APPROVED", "reviewer": "Eve"},
            ],
        },
        "Sam": {
            "owns":       ["GBR-9101", "ZGBR-1121"],
            "role_type":  "GBR",
            "department": "Marketing",
            "review_history": [
                {"date": "2024-03-22", "status": "APPROVED", "reviewer": "Frank"},
                {"date": "2024-09-30", "status": "APPROVED", "reviewer": "Grace"},
                {"date": "2025-03-25", "status": "PENDING",  "reviewer": None},
                {"date": "2025-09-15", "status": "PENDING",  "reviewer": None},
            ],
        },
        "Carlos": {
            "owns": ["ZGBR-5678"],
            "role_type": "ZGBR",
            "department": "Finance",
            "review_history": [
                {"date": "2024-03-10", "status": "APPROVED", "reviewer": "Carol"},
                {"date": "2024-09-18", "status": "FLAGGED",  "reviewer": "Carol"},
                {"date": "2025-02-05", "status": "APPROVED", "reviewer": "Dave"},
            ],
        },
        "Fatima": {
            "owns": ["GBR-9999", "ZGBR-0001"],
            "role_type": "mixed",
            "department": "Security",
            "review_history": [
                {"date": "2024-02-20", "status": "APPROVED", "reviewer": "Eve"},
                {"date": "2024-08-14", "status": "APPROVED", "reviewer": "Alice"},
                {"date": "2025-03-01", "status": "PENDING",  "reviewer": None},
            ],
        },
    },


}