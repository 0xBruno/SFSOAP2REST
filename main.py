import requests
import xml.etree.ElementTree as ET
import os

def get_salesforce_session_id(username, password, security_token, is_sandbox=False):
    """
    Authenticate with Salesforce SOAP API to get session ID and server URL
    
    Args:
        username: Salesforce username (email)
        password: Salesforce password  
        security_token: Salesforce security token
        is_sandbox: True for sandbox, False for production
    
    Returns:
        tuple: (session_id, server_url) or (None, None) if failed
    """
    
    # Determine the login URL - Use Partner WSDL endpoint
    if is_sandbox:
        login_url = "https://mysandbox.my.salesforce.com/services/Soap/u/60.0"
    else:
        login_url = "https://login.salesforce.com/services/Soap/u/60.0"
    
    # Construct SOAP envelope with Partner WSDL namespace
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com">
    <soapenv:Header/>
    <soapenv:Body>
        <urn:login>
            <urn:username>{username}</urn:username>
            <urn:password>{password}{security_token}</urn:password>
        </urn:login>
    </soapenv:Body>
</soapenv:Envelope>"""

    # Set headers
    headers = {
        'Content-Type': 'text/xml; charset=UTF-8',
        'SOAPAction': 'login'
    }
    
    try:
        # Make SOAP request
        response = requests.post(login_url, data=soap_body, headers=headers, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text[:500]}...")  # First 500 chars for debugging
        
        if response.status_code == 200:
            return parse_login_response(response.text)
        else:
            print(f"Login failed with status {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"Error during SOAP login: {e}")
        return None, None

def parse_login_response(response_xml):
    """
    Parse the SOAP login response to extract session ID and server URL
    
    Args:
        response_xml: Raw XML response from Salesforce
        
    Returns:
        tuple: (session_id, server_url) or (None, None) if parsing failed
    """
    try:
        # Parse XML
        root = ET.fromstring(response_xml)
        
        # Define namespaces used in Salesforce SOAP response (Partner WSDL)
        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns': 'urn:partner.soap.sforce.com'
        }
        
        # Extract session ID
        session_id_element = root.find('.//ns:sessionId', namespaces)
        server_url_element = root.find('.//ns:serverUrl', namespaces)
        
        if session_id_element is not None and server_url_element is not None:
            session_id = session_id_element.text
            server_url = server_url_element.text
            
            print(f"Login successful!")
            print(f"Session ID: {session_id[:20]}...")  # Show first 20 chars
            print(f"Server URL: {server_url}")
            
            return session_id, server_url
        else:
            print("Could not find sessionId or serverUrl in response")
            return None, None
            
    except ET.ParseError as e:
        print(f"Error parsing XML response: {e}")
        return None, None

def test_rest_api_with_session(session_id, server_url):
    """
    Test making a REST API call using the session ID from SOAP login
    
    Args:
        session_id: Session ID from SOAP login
        server_url: Server URL from SOAP login (we'll modify this for REST)
    """
    if not session_id or not server_url:
        print("No valid session to test with")
        return
        
    try:
        # Convert SOAP server URL to REST base URL
        # SOAP URL: https://domain.my.salesforce.com/services/Soap/u/60.0/00Dxxxxxxxxxxxxxxx
        # REST URL: https://domain.my.salesforce.com/services/data/v60.0/
        
        base_url = server_url.split('/services/')[0]
        rest_base_url = f"{base_url}/services/data/v60.0"
        
        # Test with a simple REST API call
        headers = {
            'Authorization': f'Bearer {session_id}',
            'Content-Type': 'application/json'
        }
        
        # Get available API versions
        response = requests.get(f"{rest_base_url}/", headers=headers)
        
        print(f"\nREST API Test:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Successfully authenticated with REST API using SOAP session!")
            print(f"Available versions: {len(response.json())} versions found")
        else:
            print(f"❌ REST API call failed: {response.text}")
            
    except Exception as e:
        print(f"Error testing REST API: {e}")

# Example usage
if __name__ == "__main__":
    # Replace these with your actual credentials
    USERNAME = "USER"
    PASSWORD = "PASS"
    SECURITY_TOKEN = "TOKEN"
    IS_SANDBOX = True  # Set to True for sandbox orgs
    
    print("Attempting SOAP login to Salesforce...")
    session_id, server_url = get_salesforce_session_id(
        USERNAME, 
        PASSWORD, 
        SECURITY_TOKEN, 
        IS_SANDBOX
    )
    
    if session_id:
        print(f"\n🎉 SOAP Authentication successful!")
        
        # Test using the session ID with REST API
        test_rest_api_with_session(session_id, server_url)
        
        print(f"\nYou can now use this session ID for API calls:")
        print(f"Session ID: {session_id}")
        print(f"Authorization header: Bearer {session_id}")
    else:
        print("❌ SOAP Authentication failed")
