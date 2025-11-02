import os
import datetime
import webbrowser
import platform
import re
import google.generativeai as genai
import speech_recognition as sr
import struct
import sqlite3
from datetime import datetime as dt
import threading
import time
import requests
import psutil

# Optional: Wake word detection
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    print("⚠️  pvporcupine not installed. Install with: pip install pvporcupine")

# 🔑 API Keys — REPLACE THESE IF NEEDED
GEMINI_API_KEY = #"paste you api key"
OPENWEATHER_API_KEY = #"paste your api key"

if "YOUR_KEY_HERE" in GEMINI_API_KEY or not GEMINI_API_KEY.strip():
    raise RuntimeError("❌ Set your Gemini API key.")
if "YOUR_OPENWEATHER_API_KEY" in OPENWEATHER_API_KEY:
    print("⚠️  Set your OpenWeatherMap API key for weather features.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# 🧠 Memory
last_generated_code = None

# 🎙️ Global recognizer
recognizer = sr.Recognizer()
microphone = sr.Microphone()

print("🎙️ Calibrating microphone... Please stay silent for 2 seconds.")
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=2.0)

# ========================
# 🔷 DATABASE FUNCTIONS
# ========================
def init_db():
    conn = sqlite3.connect('jarvis_history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            command TEXT,
            response TEXT,
            action_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_to_history(command, response="", action_type="ai"):
    try:
        conn = sqlite3.connect('jarvis_history.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO history (timestamp, command, response, action_type)
            VALUES (?, ?, ?, ?)
        ''', (dt.now().strftime("%Y-%m-%d %H:%M:%S"), command, response, action_type))
        conn.commit()
        conn.close()
    except:
        pass

def show_history():
    try:
        conn = sqlite3.connect('jarvis_history.db')
        c = conn.cursor()
        c.execute("""
            SELECT command, response FROM history 
            WHERE datetime(timestamp) >= datetime('now', '-1 day')
            ORDER BY id DESC LIMIT 10
        """)
        rows = c.fetchall()
        conn.close()

        if rows:
            print("📜 Command History (Last 24 Hours):")
            for i, (cmd, resp) in enumerate(reversed(rows), 1):
                short_resp = (resp[:60] + "...") if len(resp) > 60 else resp
                print(f"{i}. '{cmd}' → {short_resp}")
            say("I've displayed your commands from the last 24 hours.")
        else:
            say("No commands found in the last 24 hours.")
    except:
        say("Unable to retrieve history.")

# ========================
# 🌤️ WEATHER FUNCTION
# ========================
def get_weather(city="Hyderabad"):
    if OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":
        return "Weather service not configured. Please add your OpenWeatherMap API key."
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("cod") == 200:
                desc = data['weather'][0]['description'].title()
                temp = int(data['main']['temp'])
                humidity = data['main']['humidity']
                wind = data.get('wind', {}).get('speed', 0)
                return f"In {city}, it's currently {desc}. Temperature is {temp}°C, humidity is {humidity}%, and wind speed is {wind} meters per second."
            else:
                return "Sorry, I couldn't find that city."
        else:
            return "Weather service is temporarily unavailable."
    except Exception as e:
        return "Weather service failed. Please check your internet."

# ========================
# ⏱️ TIMER FUNCTION
# ========================
def start_timer(seconds, message="Your timer has ended!"):
    def countdown():
        time.sleep(seconds)
        say(message)
        if platform.system() == "Windows":
            try:
                import winsound
                winsound.Beep(1000, 500)
            except:
                pass
    threading.Thread(target=countdown, daemon=True).start()

# ========================
# 💻 SYSTEM MONITOR
# ========================
def get_system_info():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent if platform.system() != "Windows" else psutil.disk_usage('C:\\').percent
    
    info = f"CPU usage: {cpu}%. RAM usage: {ram}%. Disk usage: {disk}%."
    
    try:
        battery = psutil.sensors_battery()
        if battery:
            info += f" Battery: {battery.percent}% {'(charging)' if battery.power_plugged else '(discharging)'}"
    except:
        pass
    
    return info

# ========================
# 📍 LOCATION FUNCTION (BROWSER-BASED PRECISE LOCATION)
# ========================
def open_my_location():
    try:
        webbrowser.open("https://www.google.com/maps/@?api=1&map_action=map")
        say("Opening Google Maps. Please allow location access in your browser for your exact position.")
        log_to_history("where am i", "Opened Google Maps with location prompt", "system")
    except Exception as e:
        webbrowser.open("https://www.google.com/maps")
        say("Opening Google Maps. Click the location button to see your exact position.")
        log_to_history("where am i", "Opened Google Maps (fallback)", "system")

# ========================
# 🔊 Core Functions
# ========================
def say(text):
    print(f"🤖 J.A.R.V.I.S.: {text}")
    system = platform.system()
    try:
        if system == "Darwin":
            os.system(f'say "{text}"')
        elif system == "Windows":
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        else:
            os.system(f'espeak -v en "{text}" 2>/dev/null')
    except:
        pass

def takeCommand(timeout=8, phrase_time_limit=10):
    try:
        with microphone as source:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            query = recognizer.recognize_google(audio, language="en-in")
            print(f"👤 You said: {query}")
            return query
    except:
        return ""

def chat(query):
    global last_generated_code
    try:
        response = model.generate_content(query)
        reply = response.text.strip()
        last_generated_code = None

        code_match = re.search(r"```python\s*(.*?)\s*```", reply, re.DOTALL | re.IGNORECASE)
        if code_match:
            last_generated_code = code_match.group(1).strip()
        else:
            generic_match = re.search(r"```\s*(.*?)\s*```", reply, re.DOTALL)
            if generic_match:
                extracted = generic_match.group(1).strip()
                if any(kw in extracted for kw in ['def ', 'print(', 'import ', 'if ', 'for ', 'while ', 'return ', 'class ']):
                    last_generated_code = extracted

        log_to_history(query, reply, "ai")
        say(reply)
        return reply
    except Exception as e:
        say("I can't answer that right now.")
        return ""

def save_text_as_file(content, filename):
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.expanduser("~")

        safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
        safe_name = safe_name.strip()
        if not safe_name:
            say("Invalid filename.")
            return

        if "." not in safe_name:
            safe_name += ".txt"

        full_path = os.path.join(desktop, safe_name)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        log_to_history(f"save text as {filename}", f"Saved text as {safe_name}", "save")
        say(f"Text saved as '{safe_name}' on your Desktop.")

        system = platform.system()
        if system == "Darwin":
            os.system(f'open "{desktop}"')
        elif system == "Windows":
            os.system(f'explorer "{desktop}"')
        else:
            os.system(f'xdg-open "{desktop}"')

    except:
        say("Sorry, I couldn't save the text file.")

def save_last_generated_code_as(filename):
    global last_generated_code

    if last_generated_code is None:
        say("I don't have any generated code to save.")
        return

    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.expanduser("~")

        filename = filename.strip("\"'")
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
        safe_name = safe_name.strip()
        if not safe_name:
            say("Invalid filename.")
            return

        if "." not in safe_name:
            safe_name += ".py"

        full_path = os.path.join(desktop, safe_name)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(last_generated_code)

        log_to_history(f"save code as {filename}", f"Saved code as {safe_name}", "save")
        say(f"Code saved as '{safe_name}' on your Desktop.")

        system = platform.system()
        if system == "Darwin":
            os.system(f'open "{desktop}"')
        elif system == "Windows":
            os.system(f'explorer "{desktop}"')
        else:
            os.system(f'xdg-open "{desktop}"')

    except:
        say("Sorry, I couldn't save the code file.")

def wait_for_wake_word():
    if not PORCUPINE_AVAILABLE:
        say("Wake word not available. Press Enter to resume.")
        input("Press Enter to wake J.A.R.V.I.S....")
        return

    say("In standby. Say 'Jarvis' to wake me.")
    porcupine = None
    pa = None
    audio_stream = None

    try:
        import pyaudio
        porcupine = pvporcupine.create(keywords=["jarvis"])
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                say("Yes, sir?")
                break
    finally:
        if audio_stream:
            audio_stream.close()
        if pa:
            pa.terminate()
        if porcupine:
            porcupine.delete()

# ========================
# 🔁 Main Loop
# ========================
def main():
    global last_generated_code
    init_db()
    say("J.A.R.V.I.S. online. Awaiting your command, sir.")

    while True:
        query = takeCommand()
        if not query:
            continue

        q = query.lower().strip()

        # 🔴 Standby
        if any(phrase in q for phrase in [
            "wait for my command", "don't do anything just wait",
            "pause listening", "go to sleep"
        ]):
            say("Entering standby mode.")
            wait_for_wake_word()
            continue

        # 📜 Show history
        if "show history" in q or "command history" in q or "what did i say" in q:
            show_history()
            continue

        # 📍 Where am I?
        if "where am i" in q:
            open_my_location()
            continue

        # 🎥 Play any movie on Disney+ Hotstar
        if ("play " in q or "open " in q) and " on hotstar" in q:
            # Extract movie name: e.g., "play avatar on hotstar" → "avatar"
            if "play " in q:
                movie_part = q.split("play ", 1)[1]
            else:
                movie_part = q.split("open ", 1)[1]
            movie_name = movie_part.split(" on hotstar")[0].strip()
            if movie_name:
                search_url = f"https://www.hotstar.com/in/search?q={movie_name}"
                webbrowser.open(search_url)
                say(f"Searching for {movie_name} on Disney+ Hotstar.")
                log_to_history(query, f"Searched '{movie_name}' on Hotstar", "system")
            else:
                webbrowser.open("https://www.hotstar.com/in")
                say("Opening Disney+ Hotstar.")
            continue

        # 🌤️ Weather
        if "weather" in q:
            city = "Hyderabad"
            if "in " in q:
                city = q.split("in ", 1)[1].strip().title()
            elif "weather of " in q:
                city = q.split("weather of ", 1)[1].strip().title()
            response = get_weather(city)
            log_to_history(query, response, "system")
            say(response)
            continue

        # ⏱️ Timer
        if "timer" in q and ("set" in q or "start" in q):
            num_match = re.search(r'(\d+)\s*(second|minute|hour)', q)
            if num_match:
                num = int(num_match.group(1))
                unit = num_match.group(2)
                if "minute" in unit:
                    seconds = num * 60
                    msg = f"Timer for {num} minute{'s' if num>1 else ''} is set."
                elif "hour" in unit:
                    seconds = num * 3600
                    msg = f"Timer for {num} hour{'s' if num>1 else ''} is set."
                else:
                    seconds = num
                    msg = f"Timer for {num} second{'s' if num>1 else ''} is set."
                start_timer(seconds, "Your timer has ended!")
                say(msg)
                log_to_history(query, msg, "system")
            else:
                say("Please say: set a timer for 5 minutes.")
            continue

        # 💻 System Info
        if any(kw in q for kw in ["system info", "cpu usage", "ram usage", "battery", "how much ram", "system monitor"]):
            info = get_system_info()
            log_to_history(query, info, "system")
            say(info)
            continue

        # 💤 Sleep PC
        if ("sleep" in q) and ("pc" in q or "computer" in q):
            log_to_history(query, "System: Sleep initiated", "system")
            say("Putting the system to sleep, sir.")
            s = platform.system()
            try:
                if s == "Windows":
                    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                elif s == "Darwin":
                    os.system("pmset sleepnow")
                else:
                    os.system("systemctl suspend")
            except:
                say("Sleep command failed.")
            continue

        # 🔌 Shutdown PC
        if ("shutdown" in q or "shut down" in q) and ("pc" in q or "computer" in q):
            log_to_history(query, "System: Shutdown initiated", "system")
            say("Shutting down the system, sir.")
            s = platform.system()
            try:
                if s == "Windows":
                    os.system("shutdown /s /t 5")
                elif s == "Darwin":
                    os.system(
                        'osascript -e \'display dialog "Shut down the Mac?" '
                        'buttons {"Cancel", "Shut Down"} default button "Shut Down"\' '
                        '-e \'if button returned of result is "Shut Down" then tell app "System Events" to shut down\''
                    )
                else:
                    os.system("systemctl poweroff")
            except:
                say("Shutdown command failed.")
            continue

        # 💾 SAVE CODE
        if "code" in q and "as" in q:
            parts = q.split("as", 1)
            if len(parts) > 1:
                filename = parts[1].strip()
                filename = filename.replace("dot py", ".py").replace(" ", "")
                if ".py" in filename or not any(ext in filename for ext in [".txt", ".md", ".log"]):
                    save_last_generated_code_as(filename)
                    continue

        # 💾 SAVE TEXT (inline)
        if "text" in q and "as" in q and ":" in q:
            after_as = q.split("as", 1)[1]
            if ":" in after_as:
                fname, content = after_as.split(":", 1)
                fname = fname.strip().replace("dot txt", ".txt").replace(" ", "")
                save_text_as_file(content.strip(), fname)
                continue

        # 💾 SAVE TEXT (interactive)
        if "text" in q and "as" in q:
            fname = q.split("as", 1)[1].strip().replace("dot txt", ".txt").replace(" ", "")
            say("Speak the text to save.")
            content = takeCommand(timeout=10, phrase_time_limit=15)
            if content:
                save_text_as_file(content, fname)
            else:
                say("No text received.")
            continue

        # 🔗 Websites
        if "open " in q:
            site = q.split("open ", 1)[1].strip()
            log_to_history(query, f"Opened {site}", "system")
            if "youtube" in site:
                webbrowser.open("https://www.youtube.com")
                say("Opening YouTube.")
            elif "wikipedia" in site:
                webbrowser.open("https://www.wikipedia.org")
                say("Opening Wikipedia.")
            elif "google" in site:
                webbrowser.open("https://www.google.com")
                say("Opening Google.")
            else:
                url = f"https://www.{site}.com" if "." not in site else f"https://{site}"
                webbrowser.open(url)
                say(f"Opening {site}.")
            continue

        # ⏰ Time
        if "the time" in q:
            now = datetime.datetime.now().strftime("%I:%M %p")
            log_to_history(query, f"Time: {now}", "system")
            say(f"Sir, the time is {now}")
            continue

        # 🎵 Music
        if "open music" in q:
            log_to_history(query, "Opened music", "system")
            music_path = "/Users/harry/Downloads/downfall-21371.mp3"
            if os.path.exists(music_path):
                cmd = f'open "{music_path}"' if platform.system() == "Darwin" else f'start "" "{music_path}"'
                os.system(cmd)
                say("Playing music.")
            else:
                say("Music file not found.")
            continue

        # 📱 Apps
        if "open facetime" in q:
            log_to_history(query, "Opened FaceTime", "system")
            os.system("open /System/Applications/FaceTime.app")
            say("Opening FaceTime.")
            continue
        if "open pass" in q:
            log_to_history(query, "Opened Passky", "system")
            os.system("open -a Passky")
            say("Opening Passky.")
            continue

        # 🚪 Quit
        if "jarvis quit" in q:
            log_to_history(query, "J.A.R.V.I.S. shutdown", "system")
            say("Shutting down. Goodbye, sir.")
            break

        # 💬 AI
        chat(query)

if __name__ == '__main__':
    if PORCUPINE_AVAILABLE:
        try:
            import pyaudio
        except ImportError:
            os.system("pip install pyaudio")

    main()

