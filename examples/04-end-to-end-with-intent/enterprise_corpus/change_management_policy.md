# Global IT Policy: Change & Release Governance

**Policy Code:** POL-IT-204  
**Effective Date:** 2026-01-01  
**Audience:** All Engineering, DevOps, and Infrastructure Personnel  

## §1. Policy Statement
All configuration modifications, code deployments, and schema migrations affecting production systems must undergo formal change review to mitigate operational risk and service disruption.

## §2. Change Classifications
### §2.1 Standard Changes
Pre-approved, low-risk, repeatable procedures with documented rollback plans. Standard changes do not require per-instance CAB approval.

### §2.2 Emergency Changes
All emergency changes must be logged and linked directly to an active P1/P2 incident record. Emergency change approvals require verbal or digital authorization from at least one authorized Change Approver and the Duty Engineering Lead before execution. A post-implementation review (PIR) must conclude within 48 hours.

## §3. Segregation of Duties
Engineers who author code or changes cannot approve their own release into production environments.
