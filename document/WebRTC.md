Official WebRTC doc:
https://webrtc.org/getting-started/overview
https://console.firebase.google.com/u/1/project/webrtc-test-366b5/firestore
https://webrtc.org/getting-started/firebase-rtc-codelab

Good Explanation of the whole flow:
https://arpanghoshal3.medium.com/webrtc-basic-concepts-and-creating-a-simple-video-call-app-1460fc9ef17

P1 - P2
P1: Sends offer in SDP to server
SDP saved in Signaling server
P2 answer the call by SDP answer
then P2P connection is connected for media

NAT Problem
Interactive Connectivity Establishment: ICE
ice candidate is saved in server: IP/Port
stun server

# WebSocket
WebSockets are a protocol for bi-directional, real-time communication between a client and a server over a single, long-lived connection.

The WebSocket protocol consists of two parts: an initial HTTP handshake and the Web Socket protocol itself.
- The initial HTTP handshake is used to establish the WebSocket connection (specifying the WebSocket protocol in the Upgrade header.)
- Client and server can communicate using the WebSocket protocol: Messages are sent in frames, which consist of a header(message type, length) and a payload(actual message).
![[webrtc-flow.gif]]



**SDP** — object containing information about the session connection such as the codec, address, media type, audio and video and so on. Both peers will exchange SDP’s so they can understand how to connect to each other. One in the form of an SDP Offer and another as an SDP Answer

SDP: _Session description_
```
`
    v=  (protocol version number, currently only 0)
    o=  (originator and session identifier : username, id, version number, network address)
    s=  (session name : mandatory with at least one UTF-8-encoded character)
    i=* (session title or short information)
    u=* (URI of description)
    e=* (zero or more email address with optional name of contacts)
    p=* (zero or more phone number with optional name of contacts)
    c=* (connection information—not required if included in all media)
    b=* (zero or more bandwidth information lines)
    _One or more **time descriptions** ("t=" and "r=" lines; see [below](https://en.wikipedia.org/wiki/Session_Description_Protocol#Time_description))_
    z=* (time zone adjustments)
    k=* (encryption key)
    a=* (zero or more session attribute lines)
    _Zero or more **Media descriptions** (each one starting by an "m=" line; see [below](https://en.wikipedia.org/wiki/Session_Description_Protocol#Media_description))_
```

- _Time description_ (mandatory)
```
	t=  (time the session is active)
    r=* (zero or more repeat times)
```
- _Media description_ (optional)
```
    m=  (media name and transport address)
    i=* (media title or information field)
    c=* (connection information — optional if included at session level)
    b=* (zero or more bandwidth information lines)
    k=* (encryption key)
    a=* (zero or more media attribute lines — overriding the Session attribute lines)
```


**So here is the order in which things will play out.**

First the two peers will exchange SDP’s using some sort of signaling method. Once the two SDP’s are exchanged the peers are now connected, but still CANNOT transmit data yet.

In order to exchange data between two peers we still need to transmit the data.The problem here is that nowadays most devices sit behind firewalls and NAT devices, so to coordinate the discovery of our public IP addresses we use a method called ICE, which stands for Interactive Connectivity Establishment.

So in the background once SDP offers are exchanged each peer will then make a series of requests to a STUN server which will generate a list of ICE candidates to use. STUN servers are cheap and easy to maintain and because of that there are tons of free services you can use so you won’t have to worry about setting one up.

Once peer 1 gets these ICE candidates back from the STUN they will send them over to peer 2 and will let the network determine the best candidate to use. Peer 2 will do the same by requesting their ICE candidates and then sending them to peer 1.

When these candidates are exchanged and an optimal path is discovered data can begin to flow between the two peers.

webrtc handshake demo
[https://divanov11.github.io/WebRTC-Simple-SDP-Handshake-Demo/](https://divanov11.github.io/WebRTC-Simple-SDP-Handshake-Demo/)


imiplementation with socket and JS:
https://medium.com/@gbenleseun2016/creating-a-video-call-app-using-webrtc-ab75052f71ac

Good explanantion:
https://www.100ms.live/blog/webrtc-video-call
![[Pasted image 20240909114511.png]]
https://bearcoda.com/7-webrtc-setup-a-one-to-one-video-call/


### Kamailio
sip over websocket: https://www.kamailio.org/docs/modules/stable/modules/websocket.html


webrtc articles on kamailio.org
4: 
![[14-Anton.Roman.Portabales-WebRTC-Signaling.pdf]]
14: 

![[04-Victor.Pascual-WebRTC-and-VoIP.pdf]]

24:
![[24-Jose.Luis.Millan-Building-WebRTC-Apps-With-JsSIP.pdf]]

### WebRTC on Kamailio
https://www.videosdk.live/developer-hub/media-server/kamailio-webrtc
package:
```bash
    sudo apt-get install -y gcc make autoconf libtool libssl-dev libpcre3-dev libxml2-dev libsqlite3-dev
```
![[Pasted image 20240911102049.png]]
1. **Kamailio SIP Server**: The core component responsible for handling SIP signaling, routing, and managing SIP sessions.
2. **WebRTC Gateway**: Interacts with Kamailio to handle WebRTC-specific protocols like ICE, DTLS, and SRTP.
3. **Media Server**: Optional component for handling media processing tasks such as mixing, transcoding, and recording.
4. **PBX Integration**: Kamailio can interconnect with PBX systems to extend communication capabilities to traditional telephony networks.



سمینار درباره ارتباط دادن kamailio با webrtc
https://www.youtube.com/watch?v=nOHwrmuLLL0
https://webrtc.ventures/2022/09/webrtclive-kamailio/
![[posner_webrtc_2022_kamailio.pdf]]


پروژه اتصال داده شده kamailio با webrtc
https://github.com/havfo/WEBRTC-to-SIP
sip caller: https://github.com/havfo/SipCaller
![[Pasted image 20240911155723.png]]




https://github.com/sipwise/rtpengine#on-a-debian-system



SIP.js
https://github.com/onsip/SIP.js
jsSIP
https://github.com/versatica/JsSIP



https://techdocs.audiocodes.com/session-border-controller-sbc/mediant-software-sbc/user-manual/version-740/content/um/SIP%20over%20WebSocket.htm


https://www.videosdk.live/developer-hub/webrtc/webrtc-sip-integration


https://www.kamailio.org/docs/modules/stable/modules/websocket.html


kamailio outbound module
https://www.kamailio.org/docs/modules/stable/modules/outbound.html


python webrtc client & server:
https://github.com/aljanabim/simple_webrtc_python_client?tab=readme-ov-file#terminal-chat-app

https://github.com/aiortc/aiortc
desc: https://dev.to/whitphx/python-webrtc-basics-with-aiortc-48id

sip call on webrtc: 
https://github.com/InnovateAsterisk/Browser-Phone?tab=readme-ov-file

https://github.com/aljanabim/simple_webrtc_python_client?tab=readme-ov-file#terminal-chat-app





https://www.videosdk.live/developer-hub/webrtc/webrtc-sip-integration

https://github.com/havfo/WEBRTC-to-SIP

https://github.com/collecttix/ctxSip



ctxSip: sip client on webrtc
generate sip call on websocket to 192.168.21.45:8566 

python server.py
listen on 192.168.21.45:8566 ws
create connection to 192.168.21.45:80 ws

kamailio
websocket module active
listen on 192.168.21.45:80 tcp ws


file:///Users/saeedmogharian/Documents/Work/Resaa/Webrtc/ctxSip/phone/index.html