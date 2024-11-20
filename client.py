import asyncio
import websockets
from random import choices, randint
from string import ascii_letters, digits
from re import findall, search, DOTALL
import socket
import argparse


def get_local_ip():
    """Get the local IP address of the machine (may not be necessary for WebSocket)."""
    try:
        # Create a temporary socket and connect to a public IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google's public DNS, just to get the local IP used
        local_ip = s.getsockname()[0]
    except Exception as e:
        print(f"Error getting local IP: {e}")
        local_ip = "127.0.0.1"  # Default to localhost if there's an issue
    finally:
        s.close()

    return local_ip


def generate_call_id():
    """Generate a random Call-ID for the SIP session."""
    return ''.join(choices(ascii_letters + digits, k=20))


def generate_branch():
    """Generate a unique branch parameter for the Via header."""
    return "z9hG4bK" + ''.join(choices(ascii_letters + digits, k=10))


def generate_cseq():
    """Generate a random tag for the From/To headers."""
    return str(randint(1, 9999))



# Headers
class SIPHeaders:
    @staticmethod
    def sip_uri(host, number=None, port=None) -> str:
        if port is None and number is None:
            return f"sip:{host}"
        elif port is None:
            return f"sip:{number}@{host}"
        else:
            return f"sip:{number}@{host}:{port}"

    @staticmethod
    def contact_header(uri, transport=None) -> str:
        return f"Contact: <{uri};transport:{transport}>\r\n"

    @staticmethod
    def cseq_header(sequence, method) -> str:
        return f"CSeq: {sequence} {method}\r\n"

    @staticmethod
    def call_id_header(call_id) -> str:
        return f"Call-ID: {call_id}\r\n"

    @staticmethod
    def to_header(uri, to_tag=None) -> str:
        header = f"To: <{uri}>"
        if to_tag is None:
            return f"{header}\r\n"
        return f"{header};tag={to_tag}\r\n"

    @staticmethod
    def from_header(uri, from_tag) -> str:
        return f"From: <{uri}>;tag={from_tag}\r\n"

    @staticmethod
    def via_header(address, branch, protocol) -> str:
        return f'Via: SIP/2.0/{protocol.upper()} {address};rport;branch={branch}\r\n'


class SIPClient:
    def __init__(self, uri, port="80", me="1100", connection_type="ws"):
        self.uri = uri
        self.port = int(port)  # Port should be an integer for socket
        self.me = me
        self.connection_type = connection_type.lower()

        self.websocket = None
        self.socket = None

        self.call_id = generate_call_id()
        self.branch = generate_branch()
        self.tag = ''.join(choices(ascii_letters + digits, k=10))

        self.local_ip = get_local_ip()  # Get the local IP address
        self.local_port = None  # Set the local port (could be dynamically assigned)

    def get_address(self):
        if self.local_port is None:
            return f"{self.local_ip}"
        return f"{self.local_ip}:{self.local_port}"

    async def create_socket(self):
        """Establish connection based on the connection type."""
        if self.connection_type == "ws":
            self.websocket = await websockets.connect(f"ws://{self.uri}", subprotocols=["sip"])
        else:
            loop = asyncio.get_running_loop()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            await loop.run_in_executor(None, self.socket.connect, (self.uri, self.port))
            self.local_port = self.socket.getsockname()[1]
            print(f"Connected to {self.uri}:{self.port} from local port {self.local_port}\n")

    async def send_message(self, message):
        """Send a SIP message based on the connection type."""
        if self.connection_type == "ws":
            await self.websocket.send(message)
        else:
            self.socket.sendall(message.encode('utf-8'))
        print(f"Sent:\n{message}")

    async def receive_message(self):
        """Receive a SIP message based on the connection type."""
        try:
            if self.connection_type == "ws":
                response = await asyncio.wait_for(self.websocket.recv(), timeout=30)
                print(f"Received:\n{response}")
            else:
                response = await asyncio.get_running_loop().run_in_executor(None, self.socket.recv, 4096)
                response = response.decode('utf-8')
                print(f"Received:\n{response}")
            return response
        except asyncio.TimeoutError:
            print("No response received within the timeout period.")
            return None

    async def register(self):
        cseq = generate_cseq()

        """Send SIP REGISTER message over WebSocket."""
        sip_register = (
            f'REGISTER {SIPHeaders.sip_uri(self.uri)};transport:{self.connection_type} SIP/2.0\r\n'
            f'{SIPHeaders.via_header(self.get_address(), self.branch, self.connection_type)}'
            'Max-Forwards: 70\r\n'
            f'{SIPHeaders.from_header(SIPHeaders.sip_uri(self.uri, number=self.me), self.tag)}'
            f'{SIPHeaders.to_header(SIPHeaders.sip_uri(self.uri, number=self.me))}'
            f'{SIPHeaders.call_id_header(self.call_id)}'
            f'{SIPHeaders.cseq_header(cseq, "REGISTER")}'
            f'{SIPHeaders.contact_header(SIPHeaders.sip_uri(self.local_ip, self.me, self.local_port), self.connection_type)}'
            'Expires: 3600\r\n'
            'Content-Length: 0\r\n\r\n'
        )
        await self.send_message(sip_register)

    async def invite_call(self, callee):
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

        cseq = generate_cseq()

        sip_invite = (
            f'INVITE {SIPHeaders.sip_uri(self.uri, number=callee)} SIP/2.0\r\n'
            f'{SIPHeaders.via_header(self.get_address(), self.branch, self.connection_type)}'
            'Max-Forwards: 70\r\n'
            f'{SIPHeaders.from_header(SIPHeaders.sip_uri(self.uri, number=self.me), self.tag)}'
            f'{SIPHeaders.to_header(SIPHeaders.sip_uri(self.uri, number=callee))}'
            f'{SIPHeaders.call_id_header(self.call_id)}'
            f'{SIPHeaders.cseq_header(cseq, "INVITE")}'
            f'{SIPHeaders.contact_header(SIPHeaders.sip_uri(self.local_ip, self.me, self.local_port), self.connection_type)}'
            "Content-Type: application/sdp\r\n"
            f"Content-Length: {content_length}\r\n\r\n"
            f"{sdp_body}"
        )
        await self.send_message(sip_invite)

    async def send_ringing(self, response, caller):
        """Send 180 Ringing response."""
        route = self.extract_record_route(response)
        req_line = self.extract_request_line(response)
        from_tag = self.extract_from_tag(response)

        # Extract all Via headers from the INVITE
        via_headers = self.extract_via_headers(response)
        via_headers_str = "\r\n".join(via_headers)  # Convert list of headers into string

        routes_headers = "\r\n".join([f"Record-Route: <{route[i]}>" for i in range(len(route))])

        cseq = self.extract_cseq(response)

        sip_ringing = (
            f"SIP/2.0 180 Ringing\r\n"
            f"{via_headers_str}\r\n"  # Include all Via headers
            f"{routes_headers}\r\n"
            f'{SIPHeaders.to_header(SIPHeaders.sip_uri(self.uri, number=self.me), self.tag)}'
            f'{SIPHeaders.from_header(SIPHeaders.sip_uri(self.uri, number=caller), from_tag)}'
            f'{SIPHeaders.call_id_header(self.call_id)}'
            f'{SIPHeaders.cseq_header(cseq, "INVITE")}'
            f"Contact: <sip:{req_line};ob> \r\n"
            "Content-Length: 0\r\n\r\n"
        )
        await self.send_message(sip_ringing)

    @staticmethod
    def generate_sdp_response(sdp_body):
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

    async def send_200ok(self, response, caller):
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

        cseq = self.extract_cseq(response)

        sip_200_ok = (
            f"SIP/2.0 200 OK\r\n"
            f"{via_headers_str}\r\n"  # Include all Via headers
            f"{routes_headers}\r\n"
            f'{SIPHeaders.to_header(SIPHeaders.sip_uri(self.uri, number=self.me), self.tag)}'
            f'{SIPHeaders.from_header(SIPHeaders.sip_uri(self.uri, number=caller), from_tag)}'
            f'{SIPHeaders.call_id_header(self.call_id)}'
            f'{SIPHeaders.cseq_header(cseq, "INVITE")}'
            f"Contact: <sip:{req_line};ob> \r\n"
            "Content-Type: application/sdp\r\n"
            f"Content-Length: {content_length}\r\n\r\n"
            f"{sdp_response}"
        )
        await self.send_message(sip_200_ok)

    async def send_ack(self, response, callee):
        """Send an ACK message based on the 200 OK response."""
        contact = self.extract_contact(response)
        to_tag = self.extract_to_tag(response)
        route = self.extract_record_route(response)

        routes_headers = "\r\n".join([f"Route: <{route[i]}>" for i in range(len(route) - 1, -1, -1)])

        cseq = self.extract_cseq(response)

        sip_ack = (
            f"ACK {contact} SIP/2.0\r\n"
            f'{SIPHeaders.via_header(self.get_address(), self.branch, self.connection_type)}'
            f'{SIPHeaders.to_header(SIPHeaders.sip_uri(self.uri, number=callee), to_tag)}'
            f'{SIPHeaders.from_header(SIPHeaders.sip_uri(self.uri, number=self.me), self.tag)}'
            f'{SIPHeaders.call_id_header(self.call_id)}'
            f'{SIPHeaders.cseq_header(cseq, "ACK")}'
            f"{routes_headers}\r\n"
            "Content-Length: 0\r\n\r\n"
        )

        await self.send_message(sip_ack)

    async def send_bye(self, response, other):
        contact = self.extract_contact(response)
        route = self.extract_record_route(response)

        ok_from_tag = self.extract_from_tag(response)
        ok_to_tag = self.extract_to_tag(response)
        if self.tag == ok_from_tag:
            other_tag = ok_to_tag
        else:
            other_tag = ok_from_tag

        self.branch = generate_branch()

        routes_headers = "\r\n".join([f"Route: <{route[i]}>" for i in range(len(route) - 1, -1, -1)])

        cseq = self.extract_cseq(response)
        cseq = str(int(cseq) + 1)

        """Send SIP BYE message."""
        sip_bye = (
            f"BYE {contact} SIP/2.0\r\n"
            f'{SIPHeaders.via_header(self.get_address(), self.branch, self.connection_type)}'
            f'{SIPHeaders.to_header(SIPHeaders.sip_uri(self.uri, number=other), other_tag)}'
            f'{SIPHeaders.from_header(SIPHeaders.sip_uri(self.uri, number=self.me), self.tag)}'
            f'{SIPHeaders.call_id_header(self.call_id)}'
            f'{SIPHeaders.cseq_header(cseq, "BYE")}'
            f"{routes_headers}\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        await self.send_message(sip_bye)

    async def handle_bye(self, response, other):
        """Handle receiving SIP BYE message and send 200 OK for it."""
        from_tag = self.extract_from_tag(response)
        to_tag = self.extract_to_tag(response)

        # Extract all Via headers from the INVITE
        via_headers = self.extract_via_headers(response)
        via_headers_str = "\r\n".join(via_headers)  # Convert list of headers into string

        if self.tag == from_tag:
            from_number = self.me
            to_number = other
        else:
            to_number = self.me
            from_number = other

        cseq = self.extract_cseq(response)

        sip_200_ok_bye = (
            f"SIP/2.0 200 OK\r\n"
            f"{via_headers_str}\r\n"  # Include all Via headers
            f'{SIPHeaders.to_header(SIPHeaders.sip_uri(self.uri, number=to_number), to_tag)}'
            f'{SIPHeaders.from_header(SIPHeaders.sip_uri(self.uri, number=from_number), from_tag)}'
            f'{SIPHeaders.call_id_header(self.call_id)}'
            f'{SIPHeaders.cseq_header(cseq, "BYE")}'
            "Content-Type: application/sdp\r\n"
            f"Content-Length: 0\r\n\r\n"

        )
        await self.send_message(sip_200_ok_bye)

    # Extract From SIP Message
    @staticmethod
    def extract_sdp(response):
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

    @staticmethod
    def extract_via_headers(response):
        """Extract all Via headers from the INVITE response."""
        regex = r"(Via:.*?)(?:\r\n|\n)"
        via_headers = findall(regex, response)
        print(f"Extracted Via headers: {via_headers}")
        return via_headers

    @staticmethod
    def extract_cseq(response):
        """Extract CSeq from response."""
        regex = r"CSeq: (\d+)"
        cs = findall(regex, response)[0]
        print(f"Extracted Via headers: {cs}")
        return cs

    @staticmethod
    def extract_request_line(response):
        regex = r"sip:(.*?) SIP/2.0"
        sip_req_line = findall(regex, response)[0]
        print(sip_req_line)
        return sip_req_line

    @staticmethod
    def extract_caller(response):
        regex = r"From:.*sip:(\d+)@"
        caller = findall(regex, response)[0]
        print("Caller: ", caller)
        return caller

    @staticmethod
    def extract_call_id(response):
        regex = r"Call-ID:\s*([^\r\n]+)"
        call_id = search(regex, response)
        if call_id:
            call_id = call_id.group(1)
            print("Extracted Call-ID: ", call_id)
            return call_id
        else:
            print("Call-ID not found.")
            return None

    @staticmethod
    def extract_to_tag(response):
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

    @staticmethod
    def extract_from_tag(response):
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

    @staticmethod
    def extract_record_route(response):
        """Extract the Record-Route headers from the response."""
        regex = r'Record-Route:.*<(sip:[^>]+)>'
        routes = findall(regex, response)
        print(f"Extracted routes: {routes}")
        return routes

    @staticmethod
    def extract_contact(response):
        """Extract the Contact header from the 200 OK response."""
        # Improved regex to handle potential variations in whitespace and ensure proper extraction of SIP URI

        regex = r'Contact:\s*(?:"[^"]*"\s*)?<([^>]+)>'
        match = search(regex, response)
        print("Extracted Contact: ", match)  # Use search to find the first match
        if match:
            # contact = contact_match.group(1)  # Extract the actual contact URI
            contact = match.group(1)
            print("Extracted Contact: ", contact)
            return contact
        else:
            print("Contact not found.")
            return None


async def call(client: SIPClient, callee, invite_mode, send_bye):
    await client.create_socket()
    await client.register()
    await asyncio.sleep(1)  # Adding sleep for server response time
    response = await client.receive_message()
    if "200 OK" not in response:
        return

    isCall = True
    if invite_mode:
        await client.invite_call(callee)
        while isCall:
            response = await client.receive_message()
            if response and "200 OK" in response and "Contact" in response:
                await client.send_ack(response, callee)
                print("Call is Connected")
                await asyncio.sleep(3)  # call time
                if send_bye:
                    await client.send_bye(response, callee)
                    await asyncio.sleep(3)
                    print("Call is Finished")
                    isCall = False
            elif response and "BYE sip:" in response:
                await client.handle_bye(response, callee)
                print("Call is Finished")
                isCall = False
    else:
        r_invite = None
        while isCall:
            response = await client.receive_message()
            caller = True
            if response and "INVITE sip:" in response:
                r_invite = response
                print("Received INVITE, sending RINGING and 200 OK")
                caller = client.extract_caller(response)
                client.call_id = client.extract_call_id(response)
                await client.send_ringing(response, caller)
                await client.send_200ok(response, caller)
            elif response and "ACK sip:" in response:
                print("Call is Connected")
                await asyncio.sleep(3)  # call time
                if send_bye:
                    await client.send_bye(r_invite, callee)
                    await asyncio.sleep(3)
                    print("Call is Finished")
                    isCall = False
            elif response and "BYE sip:" in response:
                await client.handle_bye(response, caller)
                print("Call is finished")
                isCall = False




if __name__ == "__main__":
    URI = "192.168.21.45"  # Kamailio URI

    parser = argparse.ArgumentParser(description="Process command-line arguments.")
    parser.add_argument('--username', type=str, required=False, default="1100", help='Username')
    parser.add_argument('--send_bye', type=str, required=False, default="True", help='Send Bye (True/False)')
    parser.add_argument('--invite_mode', type=str, default="False", required=False, help='Invite Mode (True/False)')
    parser.add_argument('--callee_number', type=str, required=False, default=None, help='Callee Number')
    parser.add_argument('--connection_type', type=str, default="tcp", help="Connection type: 'tcp', 'udp' or 'ws'")

    args = parser.parse_args()

    # Convert string inputs to boolean values
    INVITE_MODE = args.invite_mode.lower() == "true"
    SEND_BYE = args.send_bye.lower() == "true"

    ME = args.username

    callee_number = args.callee_number if INVITE_MODE else None

    CONN = args.connection_type.lower()
    if CONN != 'udp' and CONN != 'tcp' and CONN != 'ws':
        raise ValueError

    PORT = "80" if CONN == "ws" else "5060"

    print(f"invite_mode: {args.invite_mode}")
    print(f"send_bye: {args.send_bye}")
    print(f"username: {args.username}")
    print(f"callee_number: {args.callee_number}")
    print(f"connection_type: {args.connection_type}")

    CLIENT = SIPClient(URI, port=PORT, me=ME, connection_type=CONN)
    asyncio.run(call(client=CLIENT, callee=callee_number, invite_mode=INVITE_MODE, send_bye=SEND_BYE))

