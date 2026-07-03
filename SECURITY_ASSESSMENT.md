# Security Assessment Report - AI-Assisted Penetration Testing Workflow

**Date:** 2026-05-23  
**Assessor Role:** Penetration Tester  
**Application:** Agent Viper (AI-Assisted Pentesting Platform)

---

## Executive Summary

The application demonstrates **good security fundamentals** with several standard protections in place (parameterized queries, bcrypt hashing, JWT authentication). However, **3 medium-to-high severity vulnerabilities** were identified that require remediation before production deployment.

**Risk Level:** 🟡 MEDIUM  
**Remediation Priority:** HIGH

---

## Vulnerabilities Identified

### 1. 🔴 PATH TRAVERSAL / DIRECTORY TRAVERSAL (High Severity)

**Location:** `backend/utils/source_resolver.py:83-114`

**Vulnerability:**
```python
def _load_local(file_path: str) -> dict:
    p = Path(file_path)
    if p.is_dir():
        all_files = sorted(p.iterdir())  # ← No path normalization
        supported = [f for f in all_files 
                     if f.suffix.lower() in (".json", ".xml") and f.is_file()]
```

**Attack Scenario:**
1. Attacker submits a malicious path like `../../etc/` or `/etc/`
2. The code doesn't validate that the path is within a safe directory
3. If the system has JSON/XML files outside the intended directory, they can be read
4. Example: `sast_sources=["../../../../../../etc/passwd.json"]` could potentially read sensitive files

**Proof of Concept:**
```bash
# An attacker with access to the API could:
POST /scan/preview-source
sast_source: "/etc/passwd"  # or "C:\Windows\System32\config\SAM"

# If XML/JSON files exist outside intended directories, they would be accessible
```

**Impact:**
- **Information Disclosure** - Read arbitrary files on the system
- **Data Exfiltration** - Access configuration files, source code, credentials
- **System Reconnaissance** - Map file system structure

**Remediation:**
```python
from pathlib import Path
import os

ALLOWED_BASE_DIRS = [
    Path("/var/pentesting/inputs").resolve(),
    Path(os.getcwd()).resolve(),
]

def _load_local(file_path: str) -> dict:
    p = Path(file_path).resolve()  # ← Resolve symlinks & normalize
    
    # Ensure the file is within allowed directories
    if not any(
        p.is_relative_to(allowed) or p.parent.is_relative_to(allowed)
        for allowed in ALLOWED_BASE_DIRS
    ):
        raise PermissionError(f"Access denied: {file_path} is outside allowed directories")
    
    # Rest of the code...
```

---

### 2. 🟡 SERVER-SIDE REQUEST FORGERY (SSRF) (Medium Severity)

**Location:** `backend/utils/source_resolver.py:151-154`

**Vulnerability:**
```python
def _fetch_remote(url: str) -> dict:
    resp = httpx.get(url, timeout=30.0, follow_redirects=True)  # ← No URL validation
    resp.raise_for_status()
    return resp.json()
```

**Attack Scenario:**
1. Attacker provides a malicious URL like `http://localhost:8000/admin`
2. The backend makes a request to this URL
3. This could be used to:
   - Access internal services (port scanning from backend perspective)
   - Bypass firewalls/network restrictions
   - Perform internal network reconnaissance

**Proof of Concept:**
```bash
# Attacker could provide:
scout_source: "http://localhost:5432"  # Probe internal database port
scout_source: "http://127.0.0.1:8000/api/admin/stats"  # Access internal API
scout_source: "http://192.168.1.1"  # Scan internal network (if accessible)
```

**Impact:**
- **Internal Network Reconnaissance** - Map internal services
- **Port Scanning** - Identify open internal ports
- **Credential Theft** - Access internal APIs that don't require auth
- **RCE Potential** - If internal services have exploitable endpoints

**Remediation:**
```python
import ipaddress
from urllib.parse import urlparse

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Localhost
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local
    ipaddress.ip_network("192.168.0.0/16"),   # Private
    ipaddress.ip_network("10.0.0.0/8"),       # Private
    ipaddress.ip_network("172.16.0.0/12"),    # Private
]

def _fetch_remote(url: str) -> dict:
    parsed = urlparse(url)
    
    # Validate URL scheme
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP/HTTPS URLs are allowed")
    
    # Validate hostname is not internal
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        for blocked in BLOCKED_NETWORKS:
            if ip in blocked:
                raise PermissionError(f"Cannot access internal network: {url}")
    except ValueError:
        # It's a domain name, do a DNS check against known dangerous domains
        pass
    
    resp = httpx.get(url, timeout=10.0, follow_redirects=False)  # No redirects
    resp.raise_for_status()
    return resp.json()
```

---

### 3. 🟡 MISSING RATE LIMITING ON PUBLIC ENDPOINTS (Medium Severity)

**Location:** `backend/api/routes/scan.py:128-160`

**Vulnerability:**
```python
@router.post("/scan/execute", ...)
@limiter.limit("10/hour")  # ← Only 10 per hour - very restrictive!
async def execute_scan(...):
```

The `/scan/preview-source` endpoint doesn't appear to have rate limiting:

```python
@router.post("/scan/preview-source", summary="Preview content of a source file or URL")
@limiter.limit("30/minute")  # ← 30 per minute - could be abused
async def preview_source(source: str):
```

**Attack Scenario:**
1. Attacker could brute-force file paths using the preview endpoint
2. Combined with Path Traversal vulnerability, attacker could enumerate files
3. Could perform resource exhaustion attacks

**Impact:**
- **Brute Force Attacks** - Enumerate file system
- **DoS/Resource Exhaustion** - Flood backend with requests
- **Information Disclosure** - Map file structure systematically

**Remediation:**
```python
# Implement stricter rate limiting
@limiter.limit("5/hour")  # Strict limit for file operations
async def preview_source(source: str):
    # Rate limit by IP + endpoint combination
    pass

# Implement account-level limits
@limiter.limit("2/hour", key_func=get_current_user)
async def execute_scan():
    pass
```

---

## Low Severity Issues

### 4. ℹ️ POTENTIAL XXE (XML External Entity) INJECTION

**Location:** `backend/utils/source_resolver.py:124-125`

```python
def _load_burp_xml(file_path: str) -> dict:
    tree = ET.parse(file_path)  # ← Standard ElementTree is vulnerable to XXE
```

**Mitigation Status:** PARTIALLY MITIGATED - Only JSON/XML files controlled by user can trigger this. Since the app only accepts file paths (not URLs for XML), the risk is lower. Still recommended to use defusedxml.

**Fix:**
```python
from defusedxml.ElementTree import parse as safe_parse

def _load_burp_xml(file_path: str) -> dict:
    tree = safe_parse(file_path)  # Safe against XXE
```

---

## Security Best Practices Already Implemented ✅

| Feature | Status | Notes |
|---------|--------|-------|
| Password Hashing | ✅ bcrypt | Secure algorithm with proper salting |
| JWT Authentication | ✅ HS256 | Proper token expiration set |
| SQL Injection | ✅ Parameterized | Using SQLAlchemy ORM properly |
| XSS (Frontend) | ✅ React sanitization | JSX escaping is automatic |
| CORS | ✅ Configured | Proper origin validation |
| CSRF | ✅ JWT-based | Stateless auth prevents CSRF |
| Secrets | ✅ Environment vars | Not hardcoded in source |

---

## Recommended Security Roadmap

### Immediate (Week 1)
1. **FIX:** Path traversal vulnerability - implement path validation
2. **FIX:** SSRF vulnerability - add URL/IP whitelisting
3. **FIX:** Rate limiting - stricter limits on file operations

### Short-term (Week 2-3)
4. **ADD:** Input validation for all file paths
5. **ADD:** Audit logging for all file access
6. **ADD:** Security headers (CSP, X-Frame-Options, etc.)
7. **ADD:** Defusedxml for XXE protection

### Medium-term (Month 1-2)
8. **IMPLEMENT:** WAF (Web Application Firewall) rules
9. **ADD:** Intrusion detection for path traversal attempts
10. **AUDIT:** Dependency scanning (npm audit, pip audit)
11. **ADD:** Security testing in CI/CD pipeline

### Long-term (Ongoing)
12. **SCHEDULE:** Monthly penetration testing
13. **MAINTAIN:** Dependency updates and security patches
14. **IMPLEMENT:** Bug bounty program
15. **DOCUMENT:** Security policies and incident response

---

## Testing Commands

To verify these vulnerabilities:

```bash
# Test 1: Path Traversal
curl -X POST http://localhost:8000/scan/preview-source \
  -H "Authorization: Bearer $TOKEN" \
  -d "source=../../etc/passwd"

# Test 2: SSRF
curl -X POST http://localhost:8000/scan/preview-source \
  -H "Authorization: Bearer $TOKEN" \
  -d "source=http://localhost:5432"

# Test 3: Rate Limiting
for i in {1..31}; do
  curl -X POST http://localhost:8000/scan/preview-source \
    -H "Authorization: Bearer $TOKEN" \
    -d "source=/some/file.json"
done
```

---

## Conclusion

The application is **functionally secure** but needs **3 critical fixes** before production deployment:

1. ✅ Path validation (prevents directory traversal)
2. ✅ URL/IP validation (prevents SSRF)
3. ✅ Strict rate limiting (prevents enumeration attacks)

All fixes are straightforward to implement and can be completed in < 4 hours of development time.

**Recommendation:** **DO NOT deploy to production** until these vulnerabilities are remediated.

---

*Report prepared for security review and remediation.*

