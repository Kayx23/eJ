# Idle Scan

Idle scan is a TCP port scan method that consists of sending spoofed packets to the target to find out what services are available, with the use of an idle host, called "zombie". This is a stealthy approach as the victim would think the port scan request came from the zombie. 

## How it works
The method will require: 
* a zombie, which is an idle host that does not have active communication (as extraneous traffic will bump up its IP ID sequence)
  > The latest versions of Linux, Solaris, OpenBSD, and Windows Vista are not suitable as zombie, since the IPID has been implemented with patches that randomized the IPID  (Wikipedia)
* the zomebie needs to increment the IPID by 1 each time on a global basis, rather than on a per-host basis

The following diagram describes the cases where a port is open on the target host: 
<img src="https://user-images.githubusercontent.com/39619599/120536079-b9470880-c3b1-11eb-9e6c-147d17b673ed.png" width=50%>

If the port is closed, in step 4, a RST is sent. As the result the attacker should see IPID to be incremented by 1. If the port is filtered, [the attacker also sees the IPID is incremented by 1](https://nmap.org/book/idlescan.html). 

**Important Notes:** this diagram is based on nmap `-sI` implementation. In the first step, SYN-ACK is sent. If there is a stateful firewall between the attacker and zombie, SYN-ACK would be blocked as there wasn't a previously initalized SYN request from zombie. We can check if zombie responses to SYN-ACK by using `-SA` option in `hping`. It that is indeeed dropped by the firewall, proceed with idle scan with `hping`. 

## Idle Scan with `hping`

### Step 1, find a zombie
To find a zombie, we use `hping` to make sure the IPID is incremental and increments exactly by 1 each time (meaning no other traffic): 
```
$ sudo hping3 -S -r -p <open-port-number> <ip-address>
```
* -S : send SYN flag
  ```diff
  ! tbh shouldn't we send SA here?
  ```
* -r : display ID increments relatively
* Although nmap has a similar functionality to check incremental IPID, it does not tell us if the host has other traffic by showing how much the IPID increments each time.  

For example, this is a good zombie candidate:
```
$ sudo hping3 -S -r -p 135 10.50.97.25
HPING 10.50.97.25 (tap0 10.50.97.25): S set, 40 headers + 0 data bytes
len=44 ip=10.50.97.25 ttl=127 id=956 sport=135 flags=SA seq=0 win=64240 rtt=59.8 ms
len=44 ip=10.50.97.25 ttl=127 id=+1 sport=135 flags=SA seq=1 win=64240 rtt=59.6 ms
len=44 ip=10.50.97.25 ttl=127 id=+1 sport=135 flags=SA seq=2 win=64240 rtt=207.4 ms
len=44 ip=10.50.97.25 ttl=127 id=+1 sport=135 flags=SA seq=3 win=64240 rtt=55.1 ms
```

and this is not: 
```
$ sudo hping3 -S -r -p 80 google.ca                                                                                                1 ⨯
HPING google.ca (wlan0 172.217.1.3): S set, 40 headers + 0 data bytes
len=44 ip=172.217.1.3 ttl=54 id=39766 sport=80 flags=SA seq=0 win=65535 rtt=15.6 ms
len=44 ip=172.217.1.3 ttl=55 id=+57677 sport=80 flags=SA seq=1 win=65535 rtt=15.4 ms
len=44 ip=172.217.1.3 ttl=54 id=+62566 sport=80 flags=SA seq=2 win=65535 rtt=15.2 ms
len=44 ip=172.217.1.3 ttl=55 id=+27485 sport=80 flags=SA seq=3 win=65535 rtt=14.7 ms
```

### Step 2, idle scan
Suppose we want to check if port 135 on the target host is open. We know port 139 on zombie is open. 

Open two terminals. 
* Terminal 1: `$ sudo hping3 -a <zombie-ip> -S -p 135 <target-ip>`
* Terminal 2: `$ sudo hping3 -S -r -p 139 <zombie-ip>`

This shows port 135 on the target host is open.
```
$ sudo hping3 -S -r -p 139 10.50.97.10
HPING 10.50.97.10 (tap0 10.50.97.10): S set, 40 headers + 0 data bytes
len=44 ip=10.50.97.10 ttl=127 DF id=2426 sport=139 flags=SA seq=0 win=64240 rtt=59.5 ms
len=44 ip=10.50.97.10 ttl=127 DF id=+2 sport=139 flags=SA seq=1 win=64240 rtt=59.3 ms
len=44 ip=10.50.97.10 ttl=127 DF id=+2 sport=139 flags=SA seq=2 win=64240 rtt=59.0 ms
len=44 ip=10.50.97.10 ttl=127 DF id=+2 sport=139 flags=SA seq=3 win=64240 rtt=58.6 ms
len=44 ip=10.50.97.10 ttl=127 DF id=+1 sport=139 flags=SA seq=5 win=64240 rtt=57.8 ms
len=44 ip=10.50.97.10 ttl=127 DF id=+2 sport=139 flags=SA seq=6 win=64240 rtt=57.5 ms
```

## Idle Scan with `nmap`

This is a more automated process, especially when you need to check more than one port on the target. The nmap option for idle scan is `-sI`. However, the initial SYN-ACK check might fail if there's a stateful firewall

```
$ sudo nmap -Pn -sI <zombie-ip>:<open-port> <target-ip> -p- 
```
