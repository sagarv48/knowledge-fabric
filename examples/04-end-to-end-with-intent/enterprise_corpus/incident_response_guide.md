# Security Runbook: Incident Response & Remediation

**Document ID:** SEC-SOP-501  
**Severity Scope:** SEV-1 through SEV-4  

## §1. Triage and Initial Assessment
Upon receipt of a security anomaly or alert, the on-call Security Analyst evaluates IOCs, affected asset criticality, and data exposure risk.

## §2. Containment Procedures
Isolate compromised network segments immediately. If lateral movement is suspected, revoke associated API tokens and Active Directory sessions via automated orchestration playbooks.

## §6. Credential Rotation & Break-Glass Auditing
### §6.3 Break-Glass Account Reviews
Break-glass accounts are reviewed quarterly and after every active activation. When emergency access has been granted to any user (e.g. jdoe@corp.com), the incident response team must generate an audit ticket in Jira/ServiceNow, document all root-cause justifications, and dispatch a formal notification to the Security Review Board.
