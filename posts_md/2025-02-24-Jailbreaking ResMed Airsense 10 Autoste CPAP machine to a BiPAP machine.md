---
layout: post
title: "Jailbreaking ResMed Airsense 10 Autoste CPAP machine to a BiPAP machine"
date: 2025-02-24 04:47:00 +0300
categories: [hardware]
tags: [hardware hacking]
author: ma1ware
slug: cpap-jailbreak
---


## Background

So around 4 years ago, I stumbled across a video from Hak5 that mentioned that someone had jailbroken a cpap machine in order to turn it into a ventilator for COVID-19 patients. Naturally, I wanted to try out this attack for myself since I knew someone that also used this specific machine. 

The target machine looks like this:

!["CPAP machine"](https://encrypted-tbn2.gstatic.com/shopping?q=tbn:ANd9GcSgDNtsyXxOxDZkY7WYHFX2xulqKzHqW1wJB3QRweXWXGwczwi-vBN7bbda9fKr2TRibIV-XeZ3ooEKeeqEE5GjpCUx60dBHDgu2SUo7MgXHOjtsBrXcTtrdw)

3.8ish years later, I finally stopped procastinating and did the hack. The hack itself is pretty easy thanks to the researcher that published their research for everyone to see. **I did not find this vulnerability, all credits go to this researcher**.

Here is the website that explains how do the hack: https://airbreak.dev/
And the GitHub repo that contains the software you will need for the hack: https://github.com/osresearch/airbreak

Note: **You should be reading this alongside the appropriate section on the airbreak.dev website.**. But if you need help feel free to contact me. 


## Prerequisites
- Torx T10 (to unscrew the machine in order to gain access to the circuit board)
- ST-LINK/V2 (this is needed in order to flash the chip)
- TC2050-IDC-NL (a programming cable, this is the one I used, I don't recommend it since I needed a second person to hold it while flashing) or alternatively TC2050-IDC (which seems to be the better choice)
- male-female 0.1" jumpers (I used dupont wires from ELEGOO on amazon)
- Some understanding of linux. You also need to install OpenOCD

# Diassembly

Read this all the way before the 'Wiring' section : https://airbreak.dev/disassembly/

Personally for me the instructions provided on the airbreak.dev website did not suffice and I struggled to get the machine opened. 

Some videos that I found helpful are: (you do not need to follow them till the end just till we get access to the circuit board)

https://www.youtube.com/watch?v=g9ipWYxl6pY
https://www.youtube.com/watch?v=vXoSxPP7shw

Make sure that you are very careful with the plastic hinges at the end. They can break if not popped very carefully. Leave the circuit board as is, do not de-attach it.

# Wiring

There is not much to write about in this section. Keep in mind that if you are using **TC2050-IDC-NL** like I did someone will need it to hold it in place when we get to the flashing part.

Use the pinout provided on the airbreak website. Also it is recommened to disconnected the humidifier. You can keep the cellular daughterboard as it is.

# Flashing

Now we get to the fun part!

First we need to install airbreak as well as openocd.

```bash
/opt ❯ git clone https://github.com/osresearch/airbreak                                       
Cloning into 'airbreak'...
remote: Enumerating objects: 780, done.
remote: Total 780 (delta 0), reused 0 (delta 0), pack-reused 780 (from 1)
Receiving objects: 100% (780/780), 23.47 MiB | 5.92 MiB/s, done.
Resolving deltas: 100% (415/415), done.
```

After this plug in your ST-LINK into your linux machine. You can check if it's properly plugged in using `st-info --probe` (you will need to install `stlink-tools` package for this which you can do by using `sudo apt install stlink-tools`)

Now you need to run the following in order to start up openocd.

```bash
/opt ❯ cd airbreak 
/opt/airbreak ❯ sudo openocd -f interface/stlink-v2.cfg -f 'tcl/airsense.cfg'
```

Wait till you recieve the line that says `hardware has 6 breakpoints, 4 watchpoints`

Now we simply need to dump the old firmware, modify it, and then flash this modified firmware.

The following command will connect you to the stlink device using the openocd interface.
```bash
telnet localhost 4444
```

To dump the firmware run:
```bash
dump
```

The file `stm32.bin` will be created. It will be around 1MB.

Note: I recommened storing this file somewhere safe where it would not be deleted, just in case you need it (you will if you fail in flashing).

Now you need to create a new window. Make sure that you are in the airbreak directory before running the following:

```bash
/opt ❯ ./patch-airsense stm32.bin stm32-unlocked.bin
```

If the above command returns a lot of output congratulations, please skip the next heading. If the command fails or when you flash this firmware no change appears / or only the HACKED text appears  then please read the next section.

# What to do if the above fails

I was stuck here too, despite the fact that the CPAP that I had was the same version as the author of the airbreak repo. The script kept on failing for me. You can from here take two paths:

1) Simply comment out the check and try again. This involves putting a comment `#` before lines 23,24, and 25 of the script. After this save the file and try again.

2) I do not condone doing this. But you can also try finding an alternate source of your machines firmware by searching on forums / boards / youtube comments. You can then modify that firmware. 

# Flashing the firmware

```bash
flash_new stm32-unlocked.bin
```

Congratulations. 

To check open up the clinician menu and see if you have different modes unlocked now.

If you want to revert back to the old firmware simply get a copy of your old firmware and run the following
```bash
flash_new stm32.bin
```
