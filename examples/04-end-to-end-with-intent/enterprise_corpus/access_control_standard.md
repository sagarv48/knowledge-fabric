# Enterprise Standard: Access Control & Privileged Identity

**Version:** 4.2  
**Owner:** Information Security & Compliance  
**Classification:** Internal Confident

## §1. Overview & Scope
This standard establishes mandatory identity governance, authentication controls, and privileged session restrictions across all corporate systems, cloud subscriptions, and production workloads.

## §2. Principle of Least Privilege
Access must only be granted to the minimum resources necessary for a specific job function. Permanent elevated credentials in production environments are strictly prohibited.

## §3. Role-Based Access Control (RBAC)
All resource access must map to approved Active Directory security groups aligned with documented job roles. Direct user-to-resource permission grants require exception approval from Security Architecture.

## §4. Emergency Access Provisioning (Break-Glass)
### §4.2 Break-Glass Protocol
Emergency access provisioning requires explicit CISO or designated Incident Commander sign-off. When break-glass credentials are checked out:
1. An automated security alert is broadcast to the Security Operations Center (SOC).
2. All session activity is recorded with tamper-evident audit logging.
3. Access expires automatically after four (4) hours unless a formal extension is granted.
4. An automated access review ticket must be generated within one hour of checkout to initiate post-incident reconciliation.
