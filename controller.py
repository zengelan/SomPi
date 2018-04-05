#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pigpio
import traceback

TXGPIO=4 # 433.42 MHz emitter on GPIO 4

#Button values
btnDown = 0x1
btnUp = 0x2
btnStop = 0x4
btnProg = 0x8

frame = bytearray(7)

def envoi_commande(room, action): #Sending a frame
   checksum = 0
   #Printing Room name
   print "Room    :      " + room
   
   #Defining button action
   if action == "open":
      bouton = btnUp
   elif action == "close":
      bouton = btnDown
   elif action == "stop":
      bouton = btnStop
   elif action == "register":
      bouton = btnProg
   else:
      print "Unknown button"
   print "Action  :      " + action
   
   #Reading remote
   with open("remotes/" + room + ".txt", 'r') as file:# the files are un a subfolder "somfy"
      data = file.readlines()

   remote = int(data[0], 16)
   code = int(data[1])
   data[1] = str(code + 1)

   with open("remotes/" + room + ".txt", 'w') as file:
      file.writelines(data)

   pi = pigpio.pi() # connect to Pi

   if not pi.connected:
      exit()

   pi.wave_add_new()
   pi.set_mode(TXGPIO, pigpio.OUTPUT)

   print "Remote  :      " + "0x%0.2X" % remote
   print "Button  :      " + "0x%0.2X" % bouton
   print "Rolling code : " + str(code)
   print ""

   frame[0] = 0xA7;       # Encryption key. Doesn't matter much
   frame[1] = bouton << 4 # Which button did  you press? The 4 LSB will be the checksum
   frame[2] = code >> 8               # Rolling code (big endian)
   frame[3] = (code & 0xFF)           # Rolling code
   frame[4] = remote >> 16            # Remote address
   frame[5] = ((remote >>  8) & 0xFF) # Remote address
   frame[6] = (remote & 0xFF)         # Remote address

   print "Frame  :    ",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

   for i in range(0, 7):
      checksum = checksum ^ frame[i] ^ (frame[i] >> 4)

   checksum &= 0b1111; # We keep the last 4 bits only

   frame[1] |= checksum;

   print "With cks  : ",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

   for i in range(1, 7):
      frame[i] ^= frame[i-1];

   print "Obfuscated :",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

   
#Telling what you want to send
   wf=[]
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 9415))
   wf.append(pigpio.pulse(0, 1<<TXGPIO, 89565))
   for i in range(2):
      wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
      wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550))
   wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

   for i in range (0, 56):
      if ((frame[i/8] >> (7 - (i%8))) & 1):
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
      else:
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

   wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415))

   #1
   for i in range(7):
      wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
      wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550))
   wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

   for i in range (0, 56):
      if ((frame[i/8] >> (7 - (i%8))) & 1):
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
      else:
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

   wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415))

   #2
   for i in range(7):
      wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
      wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550))
   wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

   for i in range (0, 56):
      if ((frame[i/8] >> (7 - (i%8))) & 1):
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
      else:
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

   wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415))

   pi.wave_add_generic(wf)
   wid = pi.wave_create()
   pi.wave_send_once(wid)
   while pi.wave_tx_busy():
      pass
   pi.wave_delete(wid)

   pi.stop()
   
envoi_commande(sys.argv[1], sys.argv[2])
