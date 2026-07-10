# Tetris Python

![Python Version](https://img.shields.io/badge/Python-3.13-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **A classic Tetris clone built in Python using Pygame and PyQt6.**

<img width="3839" height="2159" alt="image" src="https://github.com/user-attachments/assets/a7dd40a4-064c-4a44-aa74-84a1f5dc7a3e" />

---

## How to Run

### 1. Running the source code
  Make sure you have Python installed. You will also need the required libraries.
  ```bash
  pip install pygame PyQt6
  ```
In the working directory run
  ```bash
  python main.py
  ```
> If you have a controller, run:
```bash
  python joy_config.py
```

---

## How to use the joy config
> Only for controllers

<img width="1209" height="1097" alt="image" src="https://github.com/user-attachments/assets/05f242fb-cbb8-491c-a3a5-f0884683260a" />

### 1. run `joy_config.py`
* Click on the action and press `assign selected`
* Press a button, d-pad or move a axis to assign
  > Note: You can assign combo keys by pressing multiple keys in key assigning (e.g. `key 10` and `key 11` have to be press together to trigger rotation)
* Select the action and press clear to delete keys

---

### 2. Running the release
  Go to [release](https://github.com/henryzcode/Tetris/releases) and download the latest release of Tetris
  
  Unzip the `.zip` file and run the executeble inside it

  > For mac, you may come across a problem where your system is preventing you from running the program, to bypass it

  If macOS explicitly blocks the app from running in the background:
  
  1. Attempt to open the app (you will likely get a "Developer cannot be verified" or "Malware" warning).
  2. Go to the Apple menu in the top-left corner and click System Settings.
  3. Scroll down the left sidebar and click on Privacy & Security.
  4. Scroll to the very bottom of the right window to find a security section.
  5. Click the Open Anyway button next to the name of the app you are trying to launch.
<<<<<<< HEAD
  6. Enter your Mac’s administrator password to confirm.
=======
  6. Enter your Mac’s administrator password to confirm.
>>>>>>> a7b10f93c4e345f3b7ade4d26e19e80a861b6e24
