#!/usr/bin/env python3
"""Test scan against demo.testfire.net and monitor agent traces."""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
TARGET_URL = "https://demo.testfire.net"
PROJECT_ID = "altoro-test"
DEV_USERNAME = "admin@agentviper.local"
DEV_PASSWORD = "Harbor-Quartz-Meadow-58"

token = None

def log(msg):
    """Print with timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_auth_token():
    """Authenticate and get JWT token."""
    global token
    log("Authenticating...")

    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": DEV_USERNAME, "password": DEV_PASSWORD}
    )

    if response.status_code != 200:
        log(f"ERROR: Authentication failed: {response.status_code}")
        log(f"Response: {response.text}")
        return False

    # Token is in httpOnly cookie, extract from response headers or use from cookies
    if 'agent_viper_token' in response.cookies:
        token = response.cookies['agent_viper_token']
    else:
        # Fallback: try to read from response
        log("WARNING: Token not in cookies, checking response")
        data = response.json()
        token = data.get("access_token") or "fallback-token"

    log(f"[OK] Authenticated as {DEV_USERNAME}")
    return True

def create_scan():
    """Create and execute a scan."""
    log("Creating scan against demo.testfire.net...")

    # Create form data for multipart upload
    files = {
        'target_url': (None, TARGET_URL),
        'project_id': (None, PROJECT_ID),
    }

    response = requests.post(
        f"{BASE_URL}/scan/execute",
        files=files,
        headers={"Authorization": f"Bearer {token}"}  # Dev auth
    )

    if response.status_code != 200:
        log(f"ERROR: Failed to create scan: {response.status_code}")
        log(f"Response: {response.text}")
        return None

    data = response.json()
    scan_id = data.get("scan_id")
    log(f"[OK] Scan created: {scan_id}")
    return scan_id

def monitor_scan(scan_id, timeout_seconds=300):
    """Monitor scan progress until completion."""
    log(f"Monitoring scan {scan_id}...")
    start = time.time()
    last_phase = None

    while time.time() - start < timeout_seconds:
        response = requests.get(
            f"{BASE_URL}/scan/status/{scan_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code != 200:
            log(f"  Status check failed: {response.status_code}")
            time.sleep(2)
            continue

        data = response.json().get("data", {})
        status = data.get("status")
        phase = data.get("current_phase")
        progress = data.get("progress", 0)

        # Log phase changes
        if phase != last_phase:
            log(f"  > Phase: {phase} ({progress}%)")
            last_phase = phase

        # Check completion
        if status in ["completed", "failed", "stopped"]:
            log(f"[OK] Scan {status}: {phase} at {progress}%")
            return status == "completed"

        time.sleep(2)

    log(f"ERROR: Scan timeout after {timeout_seconds}s")
    return False

def get_agent_traces(scan_id):
    """Retrieve agent execution traces."""
    log(f"Fetching agent traces for {scan_id}...")

    response = requests.get(
        f"{BASE_URL}/agents/{scan_id}/traces",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        log(f"ERROR: Failed to get traces: {response.status_code}")
        return None

    data = response.json().get("data", {})
    traces = data.get("traces", [])

    log(f"[OK] Retrieved {len(traces)} agent traces")
    return traces

def display_traces(traces):
    """Display trace information."""
    if not traces:
        log("No traces available")
        return

    for trace in traces:
        agent = trace.get("agent_name", "unknown")
        status = trace.get("status", "unknown")
        duration = trace.get("total_duration_ms", 0)

        log(f"\n{'='*60}")
        log(f"Agent: {agent} | Status: {status} | Duration: {duration}ms")
        log(f"{'='*60}")

        # LLM Calls
        llm_calls = trace.get("llm_calls", [])
        if llm_calls:
            log(f"\n[LLM Calls: {len(llm_calls)}]")
            for i, call in enumerate(llm_calls, 1):
                log(f"  Call #{i}:")
                log(f"    Model: {call.get('model', 'unknown')}")
                log(f"    Tokens: {call.get('tokens', 0)}")
                log(f"    Duration: {call.get('duration_ms', 0)}ms")
                prompt = call.get('prompt', '')[:200]
                response_text = call.get('response', '')[:200]
                if prompt:
                    log(f"    Prompt: {prompt}...")
                if response_text:
                    log(f"    Response: {response_text}...")

        # Decision Points
        decisions = trace.get("decision_points", [])
        if decisions:
            log(f"\n[Decision Points: {len(decisions)}]")
            for decision in decisions:
                log(f"  - {decision}")

        # Input/Output
        input_data = trace.get("input_data", {})
        output_data = trace.get("output_data", {})

        if input_data:
            log(f"\n[Input Data]")
            log(f"  {json.dumps(input_data, indent=2)}")

        if output_data:
            log(f"\n[Output Data]")
            log(f"  {json.dumps(output_data, indent=2)}")

        # Errors
        error = trace.get("error_message")
        if error:
            log(f"\n[ERROR] {error}")

def main():
    """Run test scan."""
    log("=" * 60)
    log("Agent Viper Platform - Agent Trace Test")
    log("=" * 60)

    # Check servers are running
    try:
        requests.get(f"{BASE_URL}/docs", timeout=2)
    except:
        log("ERROR: Backend not responding at http://localhost:8000")
        sys.exit(1)

    # Authenticate
    if not get_auth_token():
        sys.exit(1)

    # Create scan
    scan_id = create_scan()
    if not scan_id:
        sys.exit(1)

    # Monitor until complete
    time.sleep(2)  # Brief delay to ensure processing started
    success = monitor_scan(scan_id, timeout_seconds=300)

    if not success:
        log("Scan did not complete successfully")
        return

    # Get and display traces
    time.sleep(1)  # Brief delay for database writes
    traces = get_agent_traces(scan_id)
    if traces:
        display_traces(traces)
        log(f"\n{'='*60}")
        log(f"[OK] Test complete! View full results at:")
        log(f"  Frontend: http://localhost:5173/results?scan_id={scan_id}")
        log(f"  Agent Debugging tab to see complete execution traces")
        log(f"{'='*60}")
    else:
        log("Could not retrieve agent traces")

if __name__ == "__main__":
    main()

