import sys
import subprocess
import importlib

def ensure_package(module_name, pip_name=None):

    """
    module_name = как импортируется
    pip_name = как ставится через pip
    """

    if pip_name is None:
        pip_name = module_name

    try:
        importlib.import_module(module_name)

    except ImportError:

        print(f"Installing missing package: {pip_name}")

        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            pip_name
        ])

        print(f"{pip_name} installed")
        
REQUIRED_PACKAGES = [

    ("pdfplumber", "pdfplumber"),
    ("keyboard", "keyboard"),
    ("dymo_sdk", "dymo-sdk"),
    ("rich", "rich"),
    ("watchdog", "watchdog"),
    ("rapidfuzz", "rapidfuzz"),
    ("serial", "pyserial"),
    ("cv2", "opencv-python"),
    ("pygame", "pygame"),
    ("requests", "requests"),
    ("send2trash", "send2trash"),
    ("win32event", "pywin32")

]

for module_name, pip_name in REQUIRED_PACKAGES:
    ensure_package(module_name, pip_name)


import os
import re
import math
import pdfplumber
import shutil
import keyboard
from pathlib import Path
import time
import pdfplumber
import re
import dymo_sdk as dsdk
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import threading
from rapidfuzz import fuzz
import serial
from pathlib import Path
import cv2
import pygame
import requests
from send2trash import send2trash
import win32event
import win32api
import winerror
import ctypes
import json
import signal

ser = None
cap = None






CURRENT_VERSION = "1.2"

VERSION_URL = "https://raw.githubusercontent.com/GreenPo-cloud/DOG/main/version.txt"

PYTHON_URL = "https://raw.githubusercontent.com/GreenPo-cloud/DOG/main/DOG.py"

win32api.SetConsoleCtrlHandler(lambda x: shutdown_handler(), True)


mutex = win32event.CreateMutex(None, False, "RepackSystemMutex")

if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    ctypes.windll.user32.MessageBoxW(
        0,
        "Программа уже запущена",
        "Ошибка",
        0x10
    )
    os._exit(0)


def check_for_updates():

    try:
        response = requests.get(VERSION_URL, timeout=5)

        if response.status_code != 200:
            return

        latest_version = response.text.strip()

        if latest_version == CURRENT_VERSION:
            print("* Latest version")
            return

        print(f"* New version found: {latest_version}")

        update_program()

    except Exception as e:
        print(f"XXX Update check failed: {e}")


def update_program():

    try:
        response = requests.get(PYTHON_URL, timeout=10)

        if response.status_code != 200:
            print("XXX Cannot download update")
            return

        current_file = os.path.abspath(__file__)

        temp_file = current_file + ".new"

        # сохраняем новую версию
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(response.text)

        # BAT файл для замены
        bat_path = current_file + ".bat"

        with open(bat_path, "w", encoding="utf-8") as bat:

            bat.write(f"""
@echo off
timeout /t 2 >nul
move /Y "{temp_file}" "{current_file}"
start "" python "{current_file}"
del "%~f0"
""")

        print("* Updating program...")

        os.startfile(bat_path)

        sys.exit()

    except Exception as e:
        print(f"XXX Update failed: {e}")
        

        
        

check_for_updates()















pygame.mixer.init()

desktop = Path.home() / "Desktop"
photo_folder = desktop / "RepackFoto"
photo_folder.mkdir(exist_ok=True)
logs_folder = photo_folder / "Logs"
logs_folder.mkdir(exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent

workers_json_path = BASE_DIR / "workers.json"
with open(workers_json_path, "r", encoding="utf-8") as f:
    workers_dict = json.load(f)

GOOD_SOUND = desktop / "good.mp3"
BAD_SOUND = desktop / "bad.mp3"
ERROR_SOUND = desktop / "error.mp3"
UPS_ACCESS_POINT_SOUND = desktop / "ups.mp3"

GOOD_SOUND_OBJ = pygame.mixer.Sound(str(GOOD_SOUND))
BAD_SOUND_OBJ = pygame.mixer.Sound(str(BAD_SOUND))
ERROR_SOUND_OBJ = pygame.mixer.Sound(str(ERROR_SOUND))
UPS = pygame.mixer.Sound(str(UPS_ACCESS_POINT_SOUND))

all_good_event = threading.Event()
camera_ready_event = threading.Event()
current_key = None  # глобально
current_worker = None

comPort = "COM3"
CAMERA_ID = 1
FOCUS = 360  # подставь своё значение

# ⚠️ ВАЖНО — лучше использовать .dymo
LABEL_PATH = r"C:\Users\fastb\Desktop\order_barcode.dymo"
STEALTH_LABEL_PATH = r"C:\Users\fastb\Desktop\stealth_barcode.dymo"
PRINTER_NAME = "DYMO LabelWriter 450 Twin Turbo"



orders_dict = {
    "FB1": "blackberry",
    "FB2": "c4",
    "FB3": "californian-snow",
    "FB4": "crystal-meth",
    "FB5": "fastberry",
    "FB6": "g14",
    "FB7": "girl-scout-cookies",
    "FB8": ["gorilla", "gorilla-glue"],
    "FB9": "grapefruit",
    "FB10": "green-crack",
    "FB11": "lsd-25",
    "FB12": "mexican-airlines",
    "FB14": "pineapple-express",
    "FB15": "rhino-ryder",
    "FB16": "six-shooter",
    "FB17": "stardawg",
    "FB18": "tangiematic",
    "FB19": "west-coast-og",
    "FB20": "cream-cookies",
    "FB21": "cbd-crack",
    "FB22": "blue-dreammatic",
    "FB23": ["z-auto", "zkittlez-auto"],
    "FB24": "lemon-ak",
    "FB25": "smoothie",
    "FB26": "cbd-20-1",
    "FB27": "gelato-auto",
    "FB28": "purple-lemonade",
    "FB30": "wedding-cheesecake-auto",
    "FB31": "strawberry-pie-auto",
    "FB32": "lemon-pie-auto",
    "FB33": "orange-sherbet-auto",
    "FB34": "purple-punch-auto",
    "FB35": "gorilla-cookies-auto",
    "FB38": "bruce-banner-auto",
    "FB39": "mimosa-cake-auto",
    "FB40": "forbidden-runtz-auto",
    "FB41": "strawberry-banana-auto",
    "FB42": "wedding-glue-auto",
    "FB43": "kosher-cake-auto",
    "FB44": "gorilla-punch-auto",
    "FB45": "banana-purple-punch-auto",
    "FB46": "strawberry-gorilla-auto",
    "FB47": "cherry-cola-auto",
    "FB48": ["amnesia-z-auto", "amnesia-zkittlez-auto"],
    "FB49": ["gorilla-z-auto", "gorilla-zkittlez-auto"],
    "FB50": "tropicana-cookies-auto",
    "FB51": "apricot-auto",
    "FB52": "ztrawberriez-auto",
    "FB53": "apple-strudel-auto",
    "FB54": "guava-auto",
    "FB55": "lemon-cherry-cookies-auto",
    "FB56": "papaya-cookies-auto",
    "FB57": "pound-cake-auto",
    "FB58": "sour-jealousy-auto",
    "FB59": "kamala-og-auto",
    "FB60": "orange-president-auto",
    "FB61": "frostbanger-auto",
    "FB62": "purple-haze-auto",
    "FB63": "z-up-auto",
    "FB64": "super-boof-auto",

    # --- RF3 форматы ---
    "FB65": "banana-purple-punch-auto-rf3",
    "FB66": "cherry-cola-auto-rf3",
    "FB67": "guava-auto-rf3",
    "FB68": "apple-strudel-auto-rf3",
    "FB69": "strawberry-gorilla-auto-rf3",
    "FB70": "guava-runtz-auto",
    "FB71": "mendo-frost-auto",
    "FB72": "guava-sundae-auto",
    "FB73": "banana-guava-auto",
    "FB74": "mendo-guava-auto",
    "FB75": "purple-lemonade-auto-rf3",
    "FB76": "lemon-cherry-sundae-auto",
    "FB77": "mango-frost-auto",
    "FB78": "banana-frost-auto",
    "FB79": "banana-cherry-cookies-auto",
    "FB80": "sundae-frost-auto",
    "FB81": "mango-cherry-runtz-auto",
    "FB82": "mendo-cherry-cookies-auto",

    "FEM1": "gorilla-melon",
    "FEM2": "lemon-mandarin",
    "FEM3": "lemonpaya",
    "FEM4": "papaya-sherbet",
    "FEM5": "rainbow-melon",
    "FEM6": "lemon-cherry-runtz",
    "FEM7": "papayton",
    "FEM8": "biscotti-gelato",
    "FEM9": "gg4",
    "FEM10": "z42",
    "FEM11": "thin-mint-sherbet",
    "FEM12": "gary-sherbet",
    "FEM13": "garlic-mint-sherbet",

    "FFNA1": "gorilla-cookies-fast-flowering",
    "FFNA2": "gg4-sherbet-fast-flowering",
    "FFNA3": "orange-sherbet-fast-flowering",
    "FFNA4": "purple-lemonade-fast-flowering",
    "FFNA5": "tropicana-cookies-fast-flowering",
    "FFNA6": "wedding-cheesecake-fast-flowering",

    "OR1": "original-auto-ak",
    "OR2": "original-auto-amnesia-haze",
    "OR3": "original-auto-bubblegum",
    "OR4": "original-auto-cheese",
    "OR5": "original-auto-chemdawg",
    "OR6": "original-auto-critical",
    "OR7": "original-auto-jack-herer",
    "OR8": "original-auto-skunk",
    "OR9": "original-auto-sour-diesel",
    "OR10": "original-auto-og-kush",
    "OR11": "original-auto-northern-lights",
    "OR12": "original-russian-auto",
    "OR13": "original-auto-white-widow",
    "OR14": "original-afghan-kush-auto",
    "OR15": "original-big-bud-auto",
    "OR16": "original-blueberry-auto",
    "OR17": "original-cinderella-auto",
    "OR18": "original-trainwreck-auto",
    "OR19": "original-moby-dick-auto",

    # --- Mix Packs ---
    "MIX PACK": "mix-pack-auto",
    "MIX FEM": "mix-pack",
    "MIX PACK FF": "mix-pack-fast-flowering",
    "MIX PACK RF3": "mix-pack-auto-rf3",
    "MIX PACK CHAMPIONS": "unreleased-champions-mix-auto",
    
     # сюда можно добавлять любые новые позиции
}


# ================= PDF =================


def copy_pdf_with_retry(file_path):
    network_folder = r"\\GREENPO\Downloads"

    while True:
        try:
            destination = os.path.join(network_folder, os.path.basename(file_path))
            shutil.copy(file_path, destination)

            print(f"🌐 Копия отправлена на второй ПК: {destination}")
            break  # ✅ УСПЕХ → выходим

        except Exception as e:
            print(f"❌ Ошибка копирования: {e}")
            print("⏳ Повтор через 15 секунд...")
            time.sleep(15)


def copy_photo_from_network():

    number = input("Введите номер: #").strip()

    order_id = f"#{number}"

    # сетевая папка
    network_folder = r"\\GREENPO\Foto"

    # рабочий стол
    desktop = Path.home() / "Desktop"

    copied = 0

    try:

        for filename in os.listdir(network_folder):

            lower = filename.lower()

            # проверяем:
            # начинается ли файл с номера заказа
            # и является ли изображением
            if (
                filename.startswith(order_id)
                and lower.endswith((".jpg", ".jpeg", ".png"))
            ):

                source = os.path.join(network_folder, filename)

                destination = desktop / filename

                shutil.copy(source, destination)

                copied += 1

        if copied == 0:
            print("❌ Фото не найдено")
        else:
            print(f"✅ Скопировано файлов: {copied}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def extract_order_numbers(pdf_path):
    ups_orders = []
    zasilkovna_orders = []
    postal_orders = []
    access_point_found = False

    seen_orders = set()  # ← запоминаем уже обработанные номера

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                if not text:
                    continue

                pattern = re.findall(
                    r"(?m)^(#\d+)(?=[^#]*☐)"       # ← ФИЛЬТР
                    r".*?type( STEALTH)?"
                    r"\s*\n(.*?)\s*☐"
                    r".*?(UPS|Zasilkovna|Postal)"
                    r"(.*?)"
                    r"(?=#\d+|$)",
                    text,
                    re.DOTALL
                )

                for match in pattern:
                    order_number = match[0]

                    # 🚫 ПРОПУСК ДУБЛИКАТОВ
                    if order_number in seen_orders:
                        continue

                    seen_orders.add(order_number)  # ← запоминаем

                    stealth_flag = bool(match[1])
                    name = match[2].strip()
                    delivery = match[3]
                    tail_block = match[4]

                    score = fuzz.partial_ratio("ups access point", tail_block.lower())

                    if score >= 90:
                        print(f"⚠️⚠️ ОБНАРУЖЕН UPS Access Point: {order_number}")
                        access_point_found = True
                        play_sound(UPS)

                    order_data = [order_number, name, stealth_flag]

                    if delivery == "UPS":
                        ups_orders.append(order_data)
                    elif delivery == "Zasilkovna":
                        zasilkovna_orders.append(order_data)
                    elif delivery == "Postal":
                        postal_orders.append(order_data)

    except Exception as e:
        print(f"❌ Ошибка при обработке PDF: {e}")
        return [], False

    return ups_orders + zasilkovna_orders + postal_orders, access_point_found


# ================= DYMO =================

def get_connected_printer():
    # print("🔍 Поиск DYMO принтеров...")

    printers = dsdk.get_printers()

    if not printers:
        raise RuntimeError("❌ DYMO принтеры не найдены")

    for p in printers:
        # print(f"Найден: {p.name} | connected={p.is_connected}")
        if p.is_connected and (PRINTER_NAME in p.name):
            # print(f"✅ Выбран принтер: {p.name}")
            return p

    raise RuntimeError("❌ Подключённый DYMO принтер не найден")


def print_orders_chunks(order_numbers):
    reversed_orders = order_numbers[::-1]
    total = len(reversed_orders)

    if total == 0:
        print("Нет заказов для печати")
        return

    try:
        printer = get_connected_printer()

        # === если <= 100 ===
        if total <= 100:
            # print(f"🖨 Печатаем {total} заказов...")
            _print_batch(reversed_orders, printer)
            print("✅ Отправка на печать завершена")
            return

        # === если > 100 ===
        # print(f"📦 Заказов {total}")
        n = int(input("Введите на сколько частей разделить: "))
        chunk_size = math.ceil(total / n)

        for i in range(n):
            start = i * chunk_size
            end = start + chunk_size
            chunk = reversed_orders[start:end]

            if not chunk:
                break

            print(f"\n=== Печать части {i+1} из {n} ===")
            _print_batch(chunk, printer)

            if i < n - 1:
                input("Нажмите Enter для следующей части...")

        print("✅ Печать полностью завершена")

    except Exception as e:
        print("❌ Ошибка печати:", e)


def _print_batch(order_list, printer):
    console = Console()

    with Progress(
        TextColumn("[bold green]Печать этикеток"),
        BarColumn(bar_width = console.width // 4, complete_style="green"),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console
    ) as progress:

        task = progress.add_task("print", total=len(order_list))

        for order in order_list:
            try:
                order_number, name, stealth_flag = order
                label_path = STEALTH_LABEL_PATH if stealth_flag else LABEL_PATH

                label = dsdk.DymoLabel(filepath=label_path)

                barcode_obj = label.get_label_object("BARCODE")
                if barcode_obj:
                    barcode_obj.update_data(order_number)

                name_obj = label.get_label_object("NAME")
                if name_obj:
                    name_obj.update_data(name)

                printer.print_label(
                    label,
                    roll_selected=2,
                    barcode_graphics_quality=True
                )

                time.sleep(1)

            except Exception as e:
                console.print(f"[red]❌ Ошибка на {order_number}: {e}")

            progress.update(task, advance=1)


def rename_mpdf(downloads_path, file_path):
    today = datetime.now().strftime("%d.%m.%Y")

    existing_parts = []

    for file in Path(downloads_path).glob(f"{today} Part *.pdf"):
        match = re.search(r"Part (\d+)", file.name)
        if match:
            existing_parts.append(int(match.group(1)))

    next_part = max(existing_parts) + 1 if existing_parts else 1

    new_name = f"{today} Part {next_part}.pdf"
    new_path = Path(downloads_path) / new_name

    # Переименование
    os.rename(file_path, new_path)

    print(f"📄 Файл переименован: {new_name}")
    
    threading.Thread(
        target=copy_pdf_with_retry,
        args=(new_path,),
        daemon=True
    ).start()

    return new_path



class PDFHandler(FileSystemEventHandler):
    def __init__(self, downloads_path):
        self.downloads_path = downloads_path
        self.processing_now = False

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.name.lower() == "mpdf.pdf":

            # 🔒 если уже обрабатываем — игнор
            if self.processing_now:
                return

            self.processing_now = True

            print("🆕 Обнаружен mpdf.pdf")
            time.sleep(2)

            try:
                new_file = rename_mpdf(self.downloads_path, file_path)
                process_pdf(new_file)

            except Exception as e:
                print(f"❌ Ошибка: {e}")

            finally:
                self.processing_now = False

# ================= MAIN =================

def process_pdf(pdf_path):
    print(f"📄 Обрабатываем файл: {pdf_path}")

    orders, access_point_found = extract_order_numbers(pdf_path)

    if not orders:
        print("❌ Номеров заказов не найдено")
        return

    print(f"📦 Найдено заказов: {len(orders)}")

    print_orders_chunks(orders)

    if access_point_found:
        input("Нажмите Enter для выхода...")


def start_watchdog():
    downloads = str(Path.home() / "Downloads")

    event_handler = PDFHandler(downloads)
    observer = Observer()
    observer.schedule(event_handler, downloads, recursive=False)
    observer.start()

    print("👀 Ожидание mpdf.pdf в папке Загрузки...")

    # 🔥 горячая клавиша
    keyboard.add_hotkey('F1', copy_photo_from_network)
    keyboard.add_hotkey('F2', check_for_updates)

    try:
        keyboard.wait()  # просто ждём события
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    


def normalize_scan(data: str):
    return data.strip().replace("\r", "").replace("\n", "")


def resolve_code(code, mapping):
    code = code.lower()

    best_match = None
    best_length = 0

    for key, values in mapping.items():

        if isinstance(values, str):
            values = [values]

        # 1. прямое совпадение ключа
        if code == key.lower():
            return key, "key"

        # 2. ищем лучшее совпадение
        for v in values:
            v_low = v.lower()

            if v_low in code:
                if len(v_low) > best_length:
                    best_length = len(v_low)
                    best_match = key

    if best_match:
        return best_match, "value"

    return None, None


def resolve_worker(code, workers):
    code = code.lower()

    for worker_name, worker_value in workers.items():
        if worker_value.lower() in code:
            return worker_name

    return None
 
    
def com_listener(port=comPort, baudrate=9600):
    global ser
    global current_key
    global current_worker

    ser = serial.Serial(port, baudrate, timeout=0.1)

    print(f"📡 Слушаю {port}...")

    first_pair = None
    worker_name = None

    while True:
        try:
            raw = ser.readline()

            if not raw:
                continue

            scanned = normalize_scan(raw.decode(errors="ignore"))

            if not scanned:
                continue

            # --- проверка сотрудника ---
            resolved_worker = resolve_worker(scanned, workers_dict)

            if resolved_worker:
                worker_name = resolved_worker
                print(f"👤 Сотрудник: {worker_name}")
                continue

            # --- проверка продукта ---
            resolved_key, resolved_type = resolve_code(scanned, orders_dict)

            if not resolved_key:
                print("❌ Хуйня какая-то")
                play_sound(ERROR_SOUND_OBJ)
                continue

            # --- первый продукт ---
            if first_pair is None:
                first_pair = (resolved_key, resolved_type)
                continue

            # --- второй продукт ---
            second_pair = (resolved_key, resolved_type)

            first_key, first_type = first_pair
            second_key, second_type = second_pair

            # --- проверка продукта ---
            product_ok = (
                first_key == second_key and
                first_type != second_type
            )

            # --- итоговая проверка ---
            if product_ok and worker_name:

                print(f"✅ ALL GOOD ({worker_name})")
                play_sound(GOOD_SOUND_OBJ)

                current_key = first_key
                current_worker = worker_name

                all_good_event.set()

            else:
                print("❌ NOT GOOD")
                play_sound(BAD_SOUND_OBJ)

            # --- сброс ---
            first_pair = None
            worker_name = None

        except Exception as e:
            print(f"❌ Ошибка COM: {e}")
            
def write_worker_log(worker_name, product_key):
    log_file = logs_folder / f"{worker_name}.txt"

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    lines = []

    # читаем старый файл
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # убираем первую строку count
    entries = lines[1:] if lines else []

    # добавляем новую запись
    entries.append(f"{product_key}   {now}\n")

    # обновляем count
    count = len(entries)

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"========== Count: {count} ==========\n")

        for line in entries:
            f.write(line)
            
            


def init_camera():
    cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 4656)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 3496)
    cap.set(cv2.CAP_PROP_FOCUS, FOCUS)
    time.sleep(2)  # прогрев
    print("📷 Камера включена")
    return cap


def camera_worker():
    global cap
    global current_key

    cap = None
    last_event_time = None

    while True:
        # ждём сигнал (но не бесконечно)
        triggered = all_good_event.wait(timeout=1)

        # --- если пришёл сигнал ---
        if triggered:
            all_good_event.clear()
            last_event_time = time.time()

            # включаем камеру, если выключена
            if cap is None:
                cap = init_camera()

            print("⏱ Ждём 2 секунды перед фото...")
            time.sleep(2)

            frames = []

            for _ in range(5):
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                time.sleep(0.1)

            if len(frames) >= 3:
                frame = frames[2]

                now = datetime.now()
                filename = f"{current_key}_{now.strftime('%d.%m_%H-%M-%S')}.jpg"
                filepath = photo_folder / filename

                cv2.imwrite(str(filepath), frame)
                print(f"📸 Фото сохранено: {filename}")
                write_worker_log(current_worker, current_key)
                play_sound(GOOD_SOUND_OBJ)

        # --- проверка простоя ---
        if cap is not None and last_event_time is not None:
            if time.time() - last_event_time > 10:
                print("💤 Камера выключена (10 сек без активности)")
                cap.release()
                cap = None
                last_event_time = None

def play_sound(sound):
    try:
        pygame.mixer.stop()
        sound.play()
    except Exception as e:
        print(f"❌ Ошибка звука: {e}")
        
        
        
        
        
        
def cleanup_old_photos(folder, older_days):

    if not os.path.isdir(folder):
        return

    now = time.time()
    max_age = older_days * 30 * 24 * 60 * 60

    removed = 0

    try:
        with os.scandir(folder) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue

                try:
                    age = now - entry.stat().st_mtime
                except FileNotFoundError:
                    continue

                if age > max_age:
                    send2trash(entry.path)
                    removed += 1

    except Exception as e:
        print(f"Cleanup error: {e}")

    if removed:
        print(f"* Old photos moved to trash: {removed}")
        
        
        
        
        
def shutdown_handler(sig=None, frame=None):
    global ser
    global cap

    print("🛑 Завершение программы...")

    try:
        if ser and ser.is_open:
            ser.close()
            print("🔌 COM порт закрыт")
    except Exception as e:
        print(f"Ошибка закрытия COM: {e}")

    try:
        if cap is not None:
            cap.release()
            print("📷 Камера освобождена")
    except Exception as e:
        print(f"Ошибка закрытия камеры: {e}")

    try:
        pygame.mixer.quit()
    except:
        pass

    os._exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)






if __name__ == "__main__":
    FOTO = os.path.join(desktop, "RepackFoto")
    today = datetime.now().day

    if today == 5:
        cleanup_old_photos(FOTO, 12)
            
    threading.Thread(target=com_listener, daemon=True).start()
    threading.Thread(target=camera_worker, daemon=True).start()
    start_watchdog()