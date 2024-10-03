import asyncio
import websockets
from random import choices
from string import ascii_letters, digits
from re import findall, search, DOTALL




class SIPClient:
    def __init__(self, uri, me, caller=None, port="80", callee=None, invite=False):
        self.uri = uri
        self.port = port
        self.me = me
        self.caller = caller
        self.callee = callee
        self.invite = invite
        self.websocket = None
        self.call_id = self.generate_call_id()
        self.branch = self.generate_branch()
        self.tag = self.generate_tag()
    
    def generate_call_id(self):
        """Generate a random Call-ID for the SIP session."""
        return ''.join(choices(ascii_letters + digits, k=20))

    def generate_branch(self):
        """Generate a unique branch parameter for the Via header."""
        return "z9hG4bK" + ''.join(choices(ascii_letters + digits, k=10))

    def generate_tag(self):
        """Generate a random tag for the From/To headers."""
        return ''.join(choices(ascii_letters + digits, k=10))


    async def create_socket(self):
        """Establish WebSocket connection."""
        self.websocket = await websockets.connect(f"ws://{self.uri}", subprotocols=["sip"])

    async def send_message(self, message):
        """Send a SIP message over WebSocket."""
        await self.websocket.send(message)
        print(f"Sent:\n{message}")

    async def receive_message(self):
        """Receive a SIP message over WebSocket."""
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=30)
            print(f"Received:\n{response}")
            return response
        except asyncio.TimeoutError:
            print("No response received within the timeout period.")
            return None

    async def register(self):
        """Send SIP REGISTER message over WebSocket."""
        sip_register = (
            f'REGISTER sip:{self.uri};transport:ws SIP/2.0\r\n'
            f'Via: SIP/2.0/WS {self.uri};rport;branch={self.branch}\r\n'
            'Max-Forwards: 70\r\n'
            f'To: <sip:{self.me}@{self.uri}>\r\n'
            f'From: <sip:{self.me}@{self.uri}>;tag={self.tag}\r\n'
            f'Call-ID: abcdefg123456@{self.uri}\r\n'
            'CSeq: 1 REGISTER\r\n'
            f'Contact: <sip:{self.me}@{self.uri}:{self.port};transport=ws>\r\n'
            'Expires: 3600\r\n'
            'Content-Length: 0\r\n\r\n'
        )
        await self.send_message(sip_register)

    async def invite_call(self):
        """Send SIP INVITE message."""
        sdp_body = (
            "v=0\r\n"
            "o=- 13760799956958020 13760799956958020 IN IP4 127.0.0.1\r\n"
            "s=-\r\n"
            "c=IN IP4 192.168.21.45\r\n"
            "t=0 0\r\n"
            "m=audio 49170 RTP/AVP 0\r\n"
            "a=rtpmap:0 PCMU/8000\r\n"
        )
        content_length = len(sdp_body.encode('utf-8'))

        sip_invite = (
            f"INVITE sip:{self.callee}@{self.uri} SIP/2.0\r\n"
            f"Via: SIP/2.0/WS {self.uri};branch={self.branch}\r\n"
            "Max-Forwards: 70\r\n"
            f'To: <sip:{self.callee}@{self.uri}>\r\n'
            f'From: <sip:{self.caller}@{self.uri}>;tag={self.tag}\r\n'
            f"Call-ID: {self.call_id}\r\n"
            "CSeq: 1 INVITE\r\n"
            f"Contact: <sip:{self.caller}@{self.uri}:{self.port};transport=ws;ob>\r\n"
            "Content-Type: application/sdp\r\n"
            f"Content-Length: {content_length}\r\n\r\n"
            f"{sdp_body}"
        )
        await self.send_message(sip_invite)

    
    # ----------------------------------------------- For reciving, Not Working ---------------------
    def extract_via_headers(self, response):
        """Extract all Via headers from the INVITE response."""
        regex = r"(Via:.*?)(?:\r\n|\n)"
        via_headers = findall(regex, response)
        print(f"Extracted Via headers: {via_headers}")
        return via_headers
    
    async def send_ringing(self, response):
        """Send 180 Ringing response."""
        route = self.extract_record_route(response)
        req_line = self.extract_request_line(response)
        from_tag = self.extract_from_tag(response)
        
        # Extract all Via headers from the INVITE
        via_headers = self.extract_via_headers(response)
        via_headers_str = "\r\n".join(via_headers)  # Convert list of headers into string

        routes_headers = "\r\n".join([f"Record-Route: <{route[i]}>" for i in range(len(route))])
        sip_ringing = (
            f"SIP/2.0 180 Ringing\r\n"
            f"{via_headers_str}\r\n"  # Include all Via headers
            f"{routes_headers}\r\n"
            f'To: <sip:{self.callee}@{self.uri}>;tag={self.tag}\r\n'
            f'From: <sip:{self.caller}@{self.uri}>;tag={from_tag}\r\n'
            f"Call-ID: {self.call_id}\r\n"
            "CSeq: 1 INVITE\r\n"
            f"Contact: <sip:{req_line};ob> \r\n"
            "Content-Length: 0\r\n\r\n"
        )
        await self.send_message(sip_ringing)


    def extract_sdp(self, response):
        """Extract the SDP body from the INVITE response."""
        sdp_regex = r"v=0\r\n(.*?)(?:\r\n|\r\n\r\n)"  # Matches from 'v=0' to the end of SDP
        sdp_match = search(sdp_regex, response, DOTALL)
        if sdp_match:
            sdp_body = sdp_match.group(0)
            print(f"Extracted SDP:\n{sdp_body}")
            return sdp_body
        else:
            print("No SDP found in the INVITE.")
            return None
    
    def generate_sdp_response(self, sdp_body):
        """Generate an SDP body for the 200 OK response, possibly modifying the received SDP."""
        # Extract IP and media port from the SDP for dynamic SDP response (Optional: adjust parameters if needed)
        ip_regex = r"c=IN IP4 (\d+\.\d+\.\d+\.\d+)"
        media_port_regex = r"m=audio (\d+)"
        
        ip_match = search(ip_regex, sdp_body)
        media_port_match = search(media_port_regex, sdp_body)
        
        ip_address = ip_match.group(1) if ip_match else "127.0.0.1"
        media_port = media_port_match.group(1) if media_port_match else "49170"
        
        # Generate the SDP response
        sdp_response = (
            "v=0\r\n"
            f"o=- 13760799956958020 13760799956958021 IN IP4 {ip_address}\r\n"
            "s=-\r\n"
            f"c=IN IP4 {ip_address}\r\n"
            "t=0 0\r\n"
            f"m=audio {media_port} RTP/AVP 0\r\n"
            "a=rtpmap:0 PCMU/8000\r\n"
            "a=sendrecv\r\n"
        )
        
        print(f"Generated SDP for 200 OK:\n{sdp_response}")
        return sdp_response

    async def send_200ok(self, response):
        """Send 200 OK response."""
        route = self.extract_record_route(response)
        req_line = self.extract_request_line(response)
        from_tag = self.extract_from_tag(response)

        # Extract the SDP from the INVITE
        sdp_body = self.extract_sdp(response)
        # Generate the SDP for the 200 OK response
        sdp_response = self.generate_sdp_response(sdp_body)
        content_length = len(sdp_response.encode('utf-8'))

        # Extract all Via headers from the INVITE
        via_headers = self.extract_via_headers(response)
        via_headers_str = "\r\n".join(via_headers)  # Convert list of headers into string

        # Create the 200 OK message with SDP and all Via headers
        routes_headers = "\r\n".join([f"Record-Route: <{route[i]}>" for i in range(len(route))])
        sip_200_ok = (
            f"SIP/2.0 200 OK\r\n"
            f"{via_headers_str}\r\n"  # Include all Via headers
            f"{routes_headers}\r\n"
            f'To: <sip:{self.callee}@{self.uri}>;tag={self.tag}\r\n'
            f'From: <sip:{self.caller}@{self.uri}>;tag={from_tag}\r\n'
            f"Call-ID: {self.call_id}\r\n"
            "CSeq: 1 INVITE\r\n"
            f"Contact: <sip:{req_line};ob> \r\n"
            "Content-Type: application/sdp\r\n"
            f"Content-Length: {content_length}\r\n\r\n"
            f"{sdp_response}"
        )
        await self.send_message(sip_200_ok)

    async def send_bye(self, response):
        contact = self.extract_contact(response)
        to_tag = self.extract_to_tag(response)
        route = self.extract_record_route(response)

        self.branch = self.generate_branch()

        routes_headers = "\r\n".join([f"Route: <{route[i]}>" for i in range(len(route)-1, -1, -1)])

        """Send SIP BYE message."""
        sip_bye = (
            f"BYE {contact} SIP/2.0\r\n"
            f"Via: SIP/2.0/WS {self.uri};branch={self.branch}\r\n"
            f'To: <sip:{self.callee}@{self.uri}>;tag={to_tag}\r\n'
            f'From: <sip:{self.caller}@{self.uri}>;tag={self.tag}\r\n'
            f"Call-ID: {self.call_id}\r\n"
            "CSeq: 2 BYE\r\n"
            f"{routes_headers}\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        await self.send_message(sip_bye)
    # ----------------------------------------------- Handle bye is not working ---------------------
    async def handle_bye(self):
        """Handle receiving SIP BYE message and send 200 OK for it."""
        sip_200_ok_bye = (
            f"SIP/2.0 200 OK\r\n"
            f"Via: SIP/2.0/WS {self.uri};branch={self.branch}\r\n"
            f'To: <sip:{self.callee}@{self.uri}>;tag={"server123"}\r\n'
            f'From: <sip:{self.caller}@{self.uri}>;tag={self.tag}\r\n'
            f"Call-ID: {self.call_id}\r\n"
            "CSeq: 2 BYE\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        await self.send_message(sip_200_ok_bye)

    async def send_ack(self, response):
        """Send an ACK message based on the 200 OK response."""
        contact = self.extract_contact(response)
        to_tag = self.extract_to_tag(response)
        route = self.extract_record_route(response)
        self.branch = self.generate_branch()

        routes_headers = "\r\n".join([f"Route: <{route[i]}>" for i in range(len(route)-1, -1, -1)])

        sip_ack = (
            f"ACK {contact} SIP/2.0\r\n"
            f"Via: SIP/2.0/WS {self.uri};branch={self.branch}\r\n"
            f'To: <sip:{self.callee}@{self.uri}>;tag={to_tag}\r\n'
            f'From: <sip:{self.caller}@{self.uri}>;tag={self.tag}\r\n'
            f"Call-ID: {self.call_id}\r\n"
            "CSeq: 1 ACK\r\n"
            f"{routes_headers}\r\n"
            "Content-Length: 0\r\n\r\n"
        )

        await self.send_message(sip_ack)
    def extract_request_line(self, response):
        regex = r"sip:(.*?) SIP/2.0"
        sip_req_line = findall(regex, response)[0]
        print(sip_req_line)
        return sip_req_line

    def extract_caller(self, response):
        regex = r"From:.*sip:(\d+)@"
        caller = findall(regex, response)[0]
        print("Caller: ", caller)
        return caller
    
    def extract_call_id(self, response):
        regex = r"Call-ID:\s*([^\r\n]+)"
        call_id = search(regex, response)
        if call_id:
            call_id = call_id.group(1)
            print("Extracted Call-ID: ", call_id)
            return call_id
        else:
            print("Call-ID not found.")
            return None
    


    
    def extract_to_tag(self, response):
        """Extract the To tag from the 200 OK response."""
        regex = r'To:.*?tag=([^;\r\n]+)'
        to_tag = search(regex, response)
        if to_tag:
            to_tag = to_tag.group(1)
            print(f"Extracted To tag: {to_tag}")
            return to_tag
        else:
            print("To tag not found.")
            return None
    
    def extract_from_tag(self, response):
        """Extract the FROM tag from the 200 OK response."""
        regex = r'From:.*?tag=([^;\r\n]+)'
        from_tag = search(regex, response)
        if from_tag:
            from_tag = from_tag.group(1)
            print(f"Extracted GROM tag: {from_tag}")
            return from_tag
        else:
            print("FROM tag not found.")
            return None

    def extract_record_route(self, response):
        """Extract the Record-Route headers from the response."""
        regex = r'Record-Route:.*<(sip:[^>]+)>'
        routes = findall(regex, response)
        print(f"Extracted routes: {routes}")
        return routes

    def extract_contact(self, response):
        """Extract the Contact header from the 200 OK response."""
        # Improved regex to handle potential variations in whitespace and ensure proper extraction of SIP URI
        regex = r'Contact:\s*".*?"\s*<([^>]+)>'
        contact_match = findall(regex, response)[0]
        print("Extracted Contact: ", contact_match) # Use search to find the first match
        if contact_match:
            # contact = contact_match.group(1)  # Extract the actual contact URI
            contact = contact_match
            print("Extracted Contact: ", contact)
            return contact
        else:
            print("Contact not found.")
            return None
    



    async def run(self):
        await self.create_socket()
        await self.register()
        await asyncio.sleep(1)  # Adding sleep for server response time
        response = await self.receive_message()

        if self.invite:
            await self.invite_call()
            while True:
                response = await self.receive_message()
                if response and "200 OK" in response and "Contact" in response:
                    await self.send_ack(response)
                    # await asyncio.sleep(15) # test-call timer
                    # await self.send_bye(response) 
                if response and "BYE sip:" in response:
                    await self.handle_bye()
                    print("Call is finished")
                    break
        else:
            while True:
                response = await self.receive_message()
                if response and "INVITE" in response:
                    print("Received INVITE, sending RINGING and 200 OK")
                    self.caller = self.extract_caller(response)
                    self.call_id = self.extract_call_id(response)
                    await self.send_ringing(response)
                    await self.send_200ok(response)
                elif response and "BYE sip:" in response:
                    await self.handle_bye()
                    break

if __name__ == "__main__":
    uri = "192.168.21.45"  # Kamailio WebSocket URI
    port = "80"
    invite_mode = False
    me = "1200"

    if invite_mode:
        caller = me # client account
        callee = input("Enter callee ID (e.g., 1200): ").strip()
        client = SIPClient(uri, me=me, caller=caller, port=port, callee=callee, invite=True)
    else:
        callee = me
        # Reciving mode is not Working
        client = SIPClient(uri, me=me, callee=callee, port=port)

    asyncio.run(client.run())