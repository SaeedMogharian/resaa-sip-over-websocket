# SIP over WebSocket (with testing client)

## Kamailio WebSocket Setup

### Calls Over WebSocket

The SIP client can make and receive sip-calls over WebSocket, allowing for seamless communication over modern web protocols.

### Configuring kamailio.cfg

The Kamailio configuration file needs to be modified to enable WebSocket support based on the Kamailio [WebSocket Module documentation](https://www.kamailio.org/docs/modules/stable/modules/websocket.html).

[kamailio.cfg](kamailio.cfg)

- Server IP: 192.168.21.45
- WebSocket Port (TCP): 80
- SIP Ports (TCP/UDP): 5060 (for standard SIP connections)

Ensure that the Kamailio server is properly configured for WebSocket connections on the specified port.

## Sip Client Implementations
- [ws_client.py](ws_client.py): WebSocket-based SIP client that can be used to test the configuration of Kamailio with WebSocket support.
- [sip_client.py](sip_client.py): A similar SIP client that communicates using standard socket connections instead of WebSocket.

## How to Use the SIP Client

### Command-Line Options

- `--username`: SIP username to register and initiate calls. (Optional, default: "1100")
- `--send_bye`: Flag to determine whether to send a BYE message after the call. (Optional, default: "True")
- `--invite_mode`: Flag to enable INVITE mode for making calls. (Optional, default: "False")
- `--callee_number`: The number of the callee for the INVITE message. (Optional, default: None)

### Example Usage

To run the WebSocket SIP client, you can use the following examples:
`python3 ws_client.py --send_bye True --username 1200 --invite_mode True --callee_number 1100`
or simply run with default values:
`python3 ws_client.py`

### TODO

- NAT Support: The current implementation has issues when operating behind a NAT. This needs to be addressed for proper communication in such environments.
- SIP Message Structure: The SIP messages need to be restructured for better compatibility. It 

This version focuses on improving readability, fixing grammar, and organizing the sections in a logical flow. Let me know if further refinements are needed!