import cv2
import numpy as np
import pydirectinput
import pygetwindow as gw
import time
from PIL import ImageGrab
import tkinter as tk
from threading import Thread
import discord
import io
import pyautogui
from key import token, channel_id, target_window

program_running = False
detected_templates = {}
gray_screen = None  # Declare gray_screen as a global variable
automatic_mode = False  # Add a global variable for automatic mode

# Your Discord bot token (replace 'YOUR_BOT_TOKEN' with your actual token)
TOKEN = token
CHANNEL_ID = channel_id

# Define the necessary intents with messages enabled
intents = discord.Intents.default()
intents.messages = True  # Allow reading and sending messages

# Initialize the Discord client with the defined intents
client = discord.Client(intents=intents)


# Define a class to represent a program step with key presses
class ProgramStep:
    def __init__(self, key, presses, delay):
        self.key = key
        self.presses = presses
        self.delay = delay

# Define a class to represent a program with multiple steps
class Program:
    def __init__(self):
        self.steps = []

    def add_step(self, key, presses, delay):
        step = ProgramStep(key, presses, delay)
        self.steps.append(step)

    def add_steps(self, steps_list):
        for key, presses, delay in steps_list:
            step = ProgramStep(key, presses, delay)
            self.steps.append(step)

    def clear_steps(self):
        self.steps = []

    def run(self):
        for step in self.steps:
            for _ in range(step.presses):
                time.sleep(step.delay)
                pydirectinput.press(step.key)

# Function to check if a given template image is present on the screen
def is_template_present(template_path, gray_screen, threshold=0.7738):
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if gray_screen is not None and template is not None:
        result = cv2.matchTemplate(gray_screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            top_left = max_loc
            bottom_right = (top_left[0] + template.shape[1], top_left[1] + template.shape[0])
            return True, top_left, bottom_right
    return False, None, None


# Specify the target window title
target_window_title = target_window

# Find the window by title
game_window = gw.getWindowsWithTitle(target_window_title)[0]



@client.event
async def on_ready():
    channel = client.get_channel(CHANNEL_ID)  # Replace YOUR_CHANNEL_ID with the channel ID where you want the bot to send the message
    image_bytes = take_window_screenshot()  # Capture the window screenshot and get it as bytes
    mention = "@everyone"  # Mention @everyone in the message content
    await channel.send(content=mention, file=discord.File(io.BytesIO(image_bytes), filename="Alert.png"))  # Send the screenshot to the channel
    

def take_window_screenshot():
    try:
        # Get the window by its title
        window = gw.getWindowsWithTitle(target_window_title)[0]
        # Activate the window (optional)
        window.activate()
        # Capture the screenshot of the window using pyautogui
        screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))

        # Convert the PIL Image to bytes
        image_bytes = io.BytesIO()
        screenshot.save(image_bytes, format='PNG')
        image_bytes.seek(0)  # Reset the buffer's position to the start
        return image_bytes.getvalue()

    except IndexError:
        print(f"Window with title '{target_window_title}' not found.")
        return None

# Function to look for specific images and perform corresponding actions
def detect_and_act():
    global detected_templates, gray_screen  # Add gray_screen to global variables

    # Capture the screen within the target window
    screen = np.array(ImageGrab.grab(bbox=(game_window.left, game_window.top, game_window.right, game_window.bottom)))
    gray_screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

    # Clear detected_templates to restart the loop after shiny is detected or selection screen is detected
    if 'ShinyImage.png' in detected_templates or 'SelectionScreen.png' in detected_templates:
        detected_templates = {}

    # List of templates to detect and corresponding actions
    templates_actions = [
        ('StartingImage.png', starting_image_action),
        ('Intro.png', intro_action),
        ('Battle1.png', battle1_action),
        ('Battle2.png', battle2_action),
        ('Battle3.png', battle3_action),
        ('Battle4.png', battle4_action),
        ('SelectionScreen.png', selection_screen_action)
        
        # Add other templates and corresponding actions here
    ]

    # Check for specific templates and perform corresponding actions
    for template_name, action in templates_actions:
        if template_name not in detected_templates:
            template_detected, _, _ = is_template_present(template_name, gray_screen)
            if template_detected:
                detected_templates[template_name] = True
                action()

# Function to handle the action for 'StartingImage.png' template
def starting_image_action():
    global program_running, detected_templates
    print('Starting Image Detected')
    program = Program()
    program.add_step("c", 15, 3)
    program.add_step("s", 1, 4)
    program.add_step("c", 1, 4)
    program.add_step("s", 1, 4)
    program.add_step("c", 2, 4)
    program.add_step("c", 1, 11)
    program.run()

    screen = np.array(ImageGrab.grab(bbox=(game_window.left, game_window.top, game_window.right, game_window.bottom)))
    gray_screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

    ZeroFps, _, _ = is_template_present('FPS0.png', gray_screen)

    if ZeroFps:
        pydirectinput.press('f6')  # Press F6 to restart the program
        program_running = False
        time.sleep(3)  # Wait for the game to restart
        program_running = True  # Restart the program
        time.sleep(10)
        detected_templates = {}


# Function to handle the action for 'Intro.png' template
def intro_action():
    print('Intro Detected')
    time.sleep(3)
    pydirectinput.press('c')

def battle1_action():
    global gray_screen

    print('Battle1 Detected')
    program = Program()
    program.add_step("c", 1, 9)
    program.add_step("w", 2, 2)
    program.run()

    while True:
        start_time = time.time()  # Start time of the 7-second window
        end_time = start_time + 7  # End time of the 7-second window

        while time.time() < end_time:
            screen = np.array(ImageGrab.grab(bbox=(game_window.left, game_window.top, game_window.right, game_window.bottom)))
            gray_screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

            dynamax_detected, _, _ = is_template_present('Dynamax.png', gray_screen)
            catch_detected, _, _ = is_template_present('Catch2.png', gray_screen)
            selection_detected, _, _ = is_template_present('SelectionScreen.png', gray_screen)

    
            if dynamax_detected:
                print('Dynamax Detected')
                time.sleep(3)
                pydirectinput.press('a')
                time.sleep(3)
                pydirectinput.press('c')
                break

            if catch_detected:
                time.sleep(3)
                print('Catch Detected')
                time.sleep(3)
                pydirectinput.press('c')

                program.clear_steps()
                program.add_steps([
                    ('x', 1, 18),
                    ('d', 1, 5),
                    ('c', 1, 1),
                ])
                program.run()
                return  # Exit the function once Catch is detected
            
            if selection_detected:
                print('Selection Screen Detected, breaking out of battle loop')
                return  # Exit the function to go back to searching for images

            time.sleep(0.5)

        # If Catch or Dynamax not detected, press 'c' and continue searching
        pydirectinput.press('c')

def battle2_action():
    global gray_screen

    print('Battle2 Detected')
    program = Program()
    program.add_step("c", 1, 9)
    program.add_step("w", 1, 2)
    program.run()

    while True:
        start_time = time.time()  # Start time of the 7-second window
        end_time = start_time + 7  # End time of the 7-second window

        while time.time() < end_time:
            screen = np.array(ImageGrab.grab(bbox=(game_window.left, game_window.top, game_window.right, game_window.bottom)))
            gray_screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

            dynamax_detected, _, _ = is_template_present('Dynamax.png', gray_screen)
            catch_detected, _, _ = is_template_present('Catch2.png', gray_screen)
            selection_detected, _, _ = is_template_present('SelectionScreen.png', gray_screen)
            
    
            if dynamax_detected:
                print('Dynamax Detected')
                time.sleep(3)
                pydirectinput.press('a')
                time.sleep(3)
                pydirectinput.press('c')
                break

            if catch_detected:
                time.sleep(3)
                print('Catch Detected')
                time.sleep(3)
                pydirectinput.press('c')

                program.clear_steps()
                program.add_steps([
                    ('c', 1, 15),
                    ('c', 1, 5),
                    ('x', 1, 11),
                ])
                program.run()
                return  # Exit the function once Catch is detected

            if selection_detected:
                print('Selection Screen Detected, breaking out of battle loop')
                return  # Exit the function to go back to searching for images
            
            time.sleep(0.5)

        # If Catch or Dynamax not detected, press 'c' and continue searching
        pydirectinput.press('c')

def battle3_action():
    global gray_screen

    print('Battle3 Detected')
    program = Program()
    program.add_step("c", 1, 9)
    program.run()

    while True:
        start_time = time.time()  # Start time of the 7-second window
        end_time = start_time + 7  # End time of the 7-second window

        while time.time() < end_time:
            screen = np.array(ImageGrab.grab(bbox=(game_window.left, game_window.top, game_window.right, game_window.bottom)))
            gray_screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

            dynamax_detected, _, _ = is_template_present('Dynamax.png', gray_screen)
            catch_detected, _, _ = is_template_present('Catch2.png', gray_screen)
            selection_detected, _, _ = is_template_present('SelectionScreen.png', gray_screen)

    
            if dynamax_detected:
                print('Dynamax Detected')
                time.sleep(3)
                pydirectinput.press('a')
                time.sleep(3)
                pydirectinput.press('c')
                break

            if catch_detected:
                time.sleep(3)
                print('Catch Detected')
                time.sleep(3)
                pydirectinput.press('c')

                program.clear_steps()
                program.add_steps([
                        ('x', 1, 15),
                    ])
                program.run()

                return  # Exit the function once Catch is detected
            
            if selection_detected:
                print('Selection Screen Detected, breaking out of battle loop')
                return  # Exit the function to go back to searching for images

            time.sleep(0.5)


        # If Catch or Dynamax not detected, press 'c' and continue searching
        pydirectinput.press('c')

# Function to handle the action for 'Battle1.png' template
def battle4_action():
    global gray_screen

    ppactivated = False

    print('Battle4 Detected')
    program = Program()
    program.add_step("c", 1, 12)
    program.add_step("s", 1, 2)
    program.run()

    while True:
        start_time = time.time()  # Start time of the 7-second window
        end_time = start_time + 7  # End time of the 7-second window

        while time.time() < end_time:

            screen = np.array(ImageGrab.grab(bbox=(game_window.left, game_window.top, game_window.right, game_window.bottom)))
            gray_screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

            dynamax_detected, _, _ = is_template_present('Dynamax.png', gray_screen)
            catch_detected, _, _ = is_template_present('Catch2.png', gray_screen)
            selection_detected, _, _ = is_template_present('SelectionScreen.png', gray_screen)
            nopp2, _, _ = is_template_present('NoPP2.png', gray_screen, threshold = .97)
            

            if nopp2 and not ppactivated:
                ppactivated = True
                program.clear_steps()
                program.add_steps([
                        ('s', 2, 3),
                    ])
                program.run()
    
            if dynamax_detected:
                print('Dynamax Detected')
                time.sleep(3)
                pydirectinput.press('a')
                time.sleep(3)
                pydirectinput.press('c')
                break

            if catch_detected:
                time.sleep(3)
                print('Catch Detected')
                time.sleep(3)
                pydirectinput.press('c')
                return  # Exit the function once Catch is detected
            
            if selection_detected:
                print('Selection Screen Detected, breaking out of battle loop')
                return  # Exit the function to go back to searching for images

            time.sleep(0.5)

        # If Catch or Dynamax not detected, press 'c' and continue searching
        pydirectinput.press('c')


def selection_screen_action(attempts=3):
    global program_running, automatic_mode

    print('Selection Screen Detected')

    program = Program()
    program.add_step('c', 1, 4)
    program.add_step('s', 1, 2)
    program.add_step('c', 1, 3)
    program.run()

    # Constant attacking phase until shiny Pokemon appears
    shiny_detected = False

    for _ in range(attempts):
        start_time = time.time()  # Start time for the current pokemon
        end_time = start_time + 7  # End time for the current pokemon

        while time.time() < end_time:
            screen = np.array(ImageGrab.grab(bbox=(game_window.left, game_window.top, game_window.right, game_window.bottom)))
            gray_screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

            # Check if shiny Pokemon is detected
            shiny_detected, _, _ = is_template_present('ShinyImage.png', gray_screen)

            if shiny_detected:
                break  # Exit the loop if shiny is detected

            time.sleep(0.5)

        if shiny_detected:
            break  # Exit the loop if shiny is detected

        pydirectinput.press('s')
        time.sleep(3)  # Wait for the next pokemon to appear

    if shiny_detected:
        # Execute the catch phase
        print('SHINY DETECTED!')
        client.run(TOKEN)
        program_running = False

    if automatic_mode and not shiny_detected:
        print('Restarting...')
        pydirectinput.press('f6')  # Press F6 to restart the program
        program_running = False
        time.sleep(3)  # Wait for the game to restart
        program_running = True  # Restart the program

    if not shiny_detected:
        print('No shiny detected')
        program_running = False

'''def zerofps_action():
    global program_running

    print('0 FPS Crash... Restarting...')
    pydirectinput.press('f6')  # Press F6 to restart the program
    program_running = False
    time.sleep(3)  # Wait for the game to restart
    program_running = True  # Restart the program
    
    ('FPS0.png', zerofps_action)'''


# Function to start the program
def start_program():
    global program_running
    program_running = True

    # Create and start the main program loop in a separate thread
    program_thread = Thread(target=run_program)
    program_thread.start()

# Function to stop the program
def stop_program():
    global program_running
    program_running = False

def run_program():
    global program_running, automatic_mode

    while program_running:
        detect_and_act()
        time.sleep(0.5)

        if automatic_mode and not program_running:
            program_running = True

def create_gui():
    global automatic_mode
    root = tk.Tk()
    root.title("Program Control")

    def toggle_automatic():
        global automatic_mode
        automatic_mode = automatic_var.get()

    automatic_var = tk.BooleanVar()
    automatic_var.set(automatic_mode)

    automatic_checkbutton = tk.Checkbutton(root, text="Automatic", variable=automatic_var, command=toggle_automatic)
    automatic_checkbutton.pack(pady=10)

    start_button = tk.Button(root, text="Start Program", command=start_program)
    start_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop Program", command=stop_program)
    stop_button.pack(pady=10)

    root.mainloop()


# Start the GUI
create_gui()