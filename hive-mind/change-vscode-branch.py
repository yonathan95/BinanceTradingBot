#!/usr/bin/env python3
"""
Command-line tool to change branch in VS Code from the backend.
"""

import requests
import json
import time
import sys
import argparse
import traceback

# Helper to print dictionary nicely for logs
def format_dict_for_log(d):
    return json.dumps(d, indent=2, sort_keys=True)

def list_clients(base_url):
    """List all connected VS Code clients. Prints details to stderr, returns list of client IDs."""
    print("--- Entering list_clients --- ", file=sys.stderr)
    print(f"[list_clients] Base URL: {base_url}", file=sys.stderr)
    target_url = f"{base_url}/api/vscode/clients"
    print(f"[list_clients] Requesting client list from: {target_url}", file=sys.stderr)
    try:
        response = requests.get(target_url, timeout=10)
        print(f"[list_clients] Response status code: {response.status_code}", file=sys.stderr)
        print(f"[list_clients] Response headers: {format_dict_for_log(dict(response.headers))}", file=sys.stderr)
        print(f"[list_clients] Response body (raw text): {response.text}", file=sys.stderr)

        if response.status_code != 200:
            print(f"Error: [list_clients] API request failed. Status: {response.status_code}, Body: {response.text}", file=sys.stderr)
            print("--- Exiting list_clients (API error) --- ", file=sys.stderr)
            return []
        
        try:
            clients_data = response.json()
            print(f"[list_clients] Parsed JSON response: {format_dict_for_log(clients_data)}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"Error: [list_clients] Failed to decode JSON response from API. Error: {str(e)}", file=sys.stderr)
            print(f"[list_clients] Raw response text that caused error: {response.text}", file=sys.stderr)
            print("--- Exiting list_clients (JSON decode error) --- ", file=sys.stderr)
            return []

        clients = clients_data.get("clients", {})
        
        if not clients:
            print("[list_clients] No VS Code clients connected.", file=sys.stderr)
            print("--- Exiting list_clients (no clients) --- ", file=sys.stderr)
            return []
        
        connected_clients_ids = []
        print(f"[list_clients] Found {len(clients)} client(s):", file=sys.stderr)
        for client_id, client in clients.items():
            connection_status = "Connected" if client.get("connected") else "Disconnected"
            print(f"  ID: {client_id}", file=sys.stderr)
            print(f"    • Status: {connection_status}", file=sys.stderr)
            print(f"    • Workspace: {client.get('workspace_name')}", file=sys.stderr)
            print(f"    • Current Branch: {client.get('current_branch')}", file=sys.stderr)
            if client.get("connected"):
                connected_clients_ids.append(client_id)
        print(file=sys.stderr) # Extra newline for readability in stderr
        
        print(f"[list_clients] Returning connected client IDs: {connected_clients_ids}", file=sys.stderr)
        print("--- Exiting list_clients (success) --- ", file=sys.stderr)
        return connected_clients_ids
    except requests.exceptions.Timeout:
        print(f"Error: [list_clients] Timeout when fetching client list from {target_url}", file=sys.stderr)
        print("--- Exiting list_clients (timeout error) --- ", file=sys.stderr)
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error: [list_clients] Request failed when fetching client list: {str(e)}", file=sys.stderr)
        print("--- Exiting list_clients (request error) --- ", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error: [list_clients] Failed to decode JSON response from client list API: {str(e)}", file=sys.stderr)
        print(f"[list_clients] Response text was: {response.text if 'response' in locals() else 'N/A'}", file=sys.stderr)
        print("--- Exiting list_clients (JSON error) --- ", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error: [list_clients] An unexpected error occurred: {str(e)}", file=sys.stderr)
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)
        print("--- Exiting list_clients (unexpected error) --- ", file=sys.stderr)
        return []

def change_branch(base_url, client_id, branch, commit=None):
    """Change branch for a specific VS Code client."""
    print("--- Entering change_branch --- ", file=sys.stderr)
    print(f"[change_branch] Parameters: base_url='{base_url}', client_id='{client_id}', branch='{branch}', commit='{commit}'", file=sys.stderr)
    try:
        checkout_data = {
            "branch": branch,
            "clientId": client_id,
            "commit": commit,
            "message": f"Branch change from backend to {branch}{f' at commit {commit}' if commit else ''}"
        }
        
        checkout_url = f"{base_url}/api/vscode/checkout"
        print(f"[change_branch] Attempting to POST checkout command to: {checkout_url}", file=sys.stderr)
        print(f"[change_branch] Checkout payload being sent: {format_dict_for_log(checkout_data)}", file=sys.stderr)
        
        response = requests.post(
            checkout_url, 
            json=checkout_data,
            timeout=15 # Increased timeout slightly
        )
        
        print(f"[change_branch] Checkout command response status code: {response.status_code}", file=sys.stderr)
        print(f"[change_branch] Checkout command response headers: {format_dict_for_log(dict(response.headers))}", file=sys.stderr)
        print(f"[change_branch] Checkout command response body (raw text): {response.text}", file=sys.stderr)

        if response.status_code in (200, 201):
            print("[change_branch] Checkout command sent successfully to backend.", file=sys.stderr)
            try:
                response_data = response.json()
                print(f"[change_branch] Parsed checkout response data: {format_dict_for_log(response_data)}", file=sys.stderr)
            except json.JSONDecodeError:
                print(f"[change_branch] Checkout response was not valid JSON, using raw text: '{response.text}'", file=sys.stderr)
            
            print("[change_branch] Waiting 5 seconds for VS Code to process the change and backend to update...", file=sys.stderr) # Increased wait time slightly
            time.sleep(5)
            
            verify_url = f"{base_url}/api/vscode/client/{client_id}"
            print(f"[change_branch] Verifying branch change by GETting client info from: {verify_url}", file=sys.stderr)
            client_info_response = requests.get(verify_url, timeout=10)

            print(f"[change_branch] Verification GET response status code: {client_info_response.status_code}", file=sys.stderr)
            print(f"[change_branch] Verification GET response headers: {format_dict_for_log(dict(client_info_response.headers))}", file=sys.stderr)
            print(f"[change_branch] Verification GET response body (raw text): {client_info_response.text}", file=sys.stderr)

            if client_info_response.status_code == 200:
                try:
                    client_data = client_info_response.json()
                    print(f"[change_branch] Parsed verification client data: {format_dict_for_log(client_data)}", file=sys.stderr)
                except json.JSONDecodeError as e_json_verify:
                    print(f"Error: [change_branch] Failed to decode JSON from verification response. Error: {str(e_json_verify)}", file=sys.stderr)
                    print(f"[change_branch] Raw verification response text: {client_info_response.text}", file=sys.stderr)
                    print("--- Exiting change_branch (verification JSON decode error) --- ", file=sys.stderr)
                    return False

                new_branch = client_data.get("current_branch")
                current_commit = client_data.get("current_commit") # Assuming backend provides this
                # Also log other potentially relevant fields like 'workspace_name', 'connected_client_id'
                workspace_name = client_data.get("workspace_name")
                connected_client_id_from_api = client_data.get("connected_client_id") # This field name is an assumption

                print(f"[change_branch] Verification Details:", file=sys.stderr)
                print(f"  > Target Client ID: '{client_id}'", file=sys.stderr)
                print(f"  > Workspace Name (from API): '{workspace_name}'", file=sys.stderr)
                print(f"  > Connected Client ID (from API): '{connected_client_id_from_api}'", file=sys.stderr) # Log assumed field
                print(f"  > Expected Branch: '{branch}'", file=sys.stderr)
                print(f"  > Actual Branch (from API): '{new_branch}'", file=sys.stderr)
                print(f"  > Expected Commit (starts with): '{commit if commit else 'N/A'}'", file=sys.stderr)
                print(f"  > Actual Commit (from API): '{current_commit if current_commit else 'N/A'}'", file=sys.stderr)

                branch_match = (new_branch == branch)
                commit_match = True # Assume true if target commit is not specified
                if commit: 
                    commit_match = (current_commit and current_commit.startswith(commit))

                print(f"[change_branch] Branch Match Result: {branch_match}", file=sys.stderr)
                print(f"[change_branch] Commit Match Result (if applicable): {commit_match if commit else 'N/A'}", file=sys.stderr)

                if branch_match and (not commit or commit_match): # If commit is specified, it must match
                    success_message = f"Success: [change_branch] VS Code client '{client_id}' branch successfully changed to '{new_branch}'"
                    if commit:
                        success_message += f" and commit starts with '{commit}' (Actual: '{current_commit}')"
                    success_message += "."
                    print(success_message, file=sys.stderr)
                    print("--- Exiting change_branch (success) --- ", file=sys.stderr)
                    return True
                else:
                    print(f"Warning: [change_branch] Verification failed. Branch/commit did not match expected values for client '{client_id}'.", file=sys.stderr)
                    # Detailed reasons already printed above
                    print("  Possible reasons include:", file=sys.stderr)
                    print("  • Target branch/commit does not exist in the repository.", file=sys.stderr)
                    print("  • VS Code encountered an error during the git operation (check VS Code's Git output/logs).", file=sys.stderr)
                    print("  • Backend API did not reflect the change yet or reported stale data.", file=sys.stderr)
                    print("  • Discrepancy in commit hash (e.g. full vs. short, or different commit on the same branch if not specified).", file=sys.stderr)
                    print("--- Exiting change_branch (verification mismatch) --- ", file=sys.stderr)
                    return False
            else:
                print(f"Warning: [change_branch] Could not verify branch change. Verification GET request for client '{client_id}' failed. Status: {client_info_response.status_code}", file=sys.stderr)
                print(f"[change_branch] Raw verification response: {client_info_response.text}", file=sys.stderr)
                print("--- Exiting change_branch (verification HTTP error) --- ", file=sys.stderr)
                return False
        else:
            print(f"Error: [change_branch] Backend failed to process checkout command for client '{client_id}'. Status: {response.status_code}", file=sys.stderr)
            print(f"[change_branch] Backend response: {response.text}", file=sys.stderr)
            print("--- Exiting change_branch (checkout command API error) --- ", file=sys.stderr)
            return False
            
    except requests.exceptions.Timeout as e_timeout:
        print(f"Error: [change_branch] Timeout during operation: {str(e_timeout)}", file=sys.stderr)
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)
        print("--- Exiting change_branch (timeout error) --- ", file=sys.stderr)
        return False
    except requests.exceptions.RequestException as e_req:
        print(f"Error: [change_branch] Request failed: {str(e_req)}", file=sys.stderr)
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)
        print("--- Exiting change_branch (request error) --- ", file=sys.stderr)
        return False
    except json.JSONDecodeError as e_json_main:
        error_context = "an unknown API response"
        response_text_to_log = "N/A"
        if 'client_info_response' in locals() and client_info_response.status_code == 200: # Error was in parsing verification response
            error_context = "client info API verification response"
            response_text_to_log = client_info_response.text
        elif 'response' in locals() and response.status_code in (200,201): # Error was in parsing initial checkout response
            error_context = "checkout API command response"
            response_text_to_log = response.text
        print(f"Error: [change_branch] Failed to decode JSON from {error_context}: {str(e_json_main)}", file=sys.stderr)
        print(f"[change_branch] Raw response text that caused JSON error: {response_text_to_log}", file=sys.stderr)
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)
        print("--- Exiting change_branch (JSON error) --- ", file=sys.stderr)
        return False
    except Exception as e_unexpected:
        print(f"Error: [change_branch] An unexpected error occurred: {str(e_unexpected)}", file=sys.stderr)
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)
        print("--- Exiting change_branch (unexpected error) --- ", file=sys.stderr)
        return False

def main():
    """Main function."""
    print("=== Script Starting ===", file=sys.stderr)
    start_time = time.time()

    parser = argparse.ArgumentParser(description="Change branch in VS Code via backend API.")
    parser.add_argument("--url", "-u", default="http://localhost:5000", help="Backend URL (default: http://localhost:5000)")
    parser.add_argument("--list", "-l", action="store_true", help="List connected clients (outputs JSON list of IDs to stdout, details to stderr)")
    parser.add_argument("--client", "-c", help="Client ID for branch change operation")
    parser.add_argument("--branch", "-b", help="Branch name to checkout")
    parser.add_argument("--commit", help="Commit hash (or short hash) to checkout (optional)")
    
    args = parser.parse_args()
    print(f"[main] Parsed arguments: Namespace(url='{args.url}', list={args.list}, client='{args.client}', branch='{args.branch}', commit='{args.commit}')", file=sys.stderr)

    # Initial backend check (lightweight)
    print(f"[main] Performing initial backend check at {args.url}...", file=sys.stderr)
    try:
        response = requests.get(args.url, timeout=5) 
        if response.status_code == 200:
            print(f"[main] Backend check successful: {args.url} responded with {response.status_code}.", file=sys.stderr)
        else:
            print(f"Warning: [main] Backend at {args.url} responded with status: {response.status_code}. Body: {response.text[:200]}...", file=sys.stderr)
    except requests.exceptions.Timeout:
        print(f"Error: [main] Timeout connecting to the backend at {args.url}. Is it running and accessible?", file=sys.stderr)
        # For --list, list_clients will try again and handle its own errors.
        # For change_branch, it will also try and handle its errors.
        # No early exit here, let sub-commands try.
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)
    except requests.exceptions.ConnectionError as e_conn:
        print(f"Error: [main] Connection refused by backend at {args.url}. Is it running? Error: {e_conn}", file=sys.stderr)
        # If not --list, and backend is clearly down, might be good to exit early for other commands.
        if not args.list and not (args.client and args.branch):
            print("[main] Exiting due to connection error before specific command execution.", file=sys.stderr)
            print("=== Script Ended (Connection Error) ====", file=sys.stderr)
            return 1 # Critical error if backend is down and we need to change branch
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)
    except Exception as e:
        print(f"Error: [main] Could not verify backend status at {args.url}: {str(e)}", file=sys.stderr)
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)

    exit_code = 0
    if args.list:
        print("[main] Action: List clients", file=sys.stderr)
        clients_ids = list_clients(args.url)
        print(json.dumps(clients_ids)) # To stdout for PowerShell
        # list_clients prints its own success/failure to stderr
    
    elif args.client and args.branch:
        print(f"[main] Action: Change branch for client '{args.client}' to branch '{args.branch}' (commit: '{args.commit}')", file=sys.stderr)
        success = change_branch(args.url, args.client, args.branch, args.commit)
        if success:
            print("[main] Branch change operation reported success.", file=sys.stderr)
            exit_code = 0
        else:
            print("[main] Branch change operation reported failure.", file=sys.stderr)
            exit_code = 1
    
    else:
        print("[main] No specific action requested (e.g., --list or --client/--branch).", file=sys.stderr)
        print("[main] Printing help message and defaulting to verbose client list (to stderr).", file=sys.stderr)
        parser.print_help(sys.stderr)
        print("\n[main] Current connected clients (verbose to stderr):", file=sys.stderr)
        list_clients(args.url) # Verbose output to stderr for user info
        exit_code = 0 # Or 1 if this should be an error? For now, 0 as it's informational.
    
    end_time = time.time()
    print(f"[main] Total execution time: {end_time - start_time:.2f} seconds", file=sys.stderr)
    print(f"=== Script Ended (Exit Code: {exit_code}) ====", file=sys.stderr)
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 