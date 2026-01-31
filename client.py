import socket
import threading
import random
import time
import os
import sys
import shutil
import json
import hashlib
import datetime
from colorama import Fore, Style, init
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.fernet import Fernet

init(autoreset=True)

# ==================== CONFIGURATION ====================
CREDENTIALS_FILE = 'agents_credentials.json'
LOG_FILE = 'system_logs.json'
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5555

# ==================== GLOBAL VARIABLES ====================
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
pem_public = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode('utf-8')

target_public_key_cache = None
current_agent_id = None
messages_history = []

# ==================== UTILITY FUNCTIONS ====================
def get_width():
    try: return shutil.get_terminal_size().columns
    except: return 80

def clear_screen(): 
    os.system('cls' if os.name == 'nt' else 'clear')

def play_sound(): 
    sys.stdout.write('\a'); sys.stdout.flush()

def print_centered(text, color=Fore.WHITE, style=Style.NORMAL):
    width = get_width()
    padding = max(0, (width - len(text)) // 2)
    print(" " * padding + color + style + text)

def input_centered(prompt_text, color=Fore.YELLOW):
    width = get_width()
    padding = max(0, (width - len(prompt_text) - 10) // 2) 
    sys.stdout.write(" " * padding + color + prompt_text)
    sys.stdout.flush()
    return input(Fore.WHITE)

# ==================== LOGGING SYSTEM ====================
def log_event(agent_id, event_type, details):
    """تسجيل جميع الأحداث في ملف السجل"""
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        
        log_entry = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'agent_id': agent_id,
            'event_type': event_type,
            'details': details
        }
        logs.append(log_entry)
        
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
    except:
        pass

# ==================== CREDENTIALS SYSTEM ====================
def load_credentials():
    """تحميل بيانات المستخدمين المسجلين"""
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_credentials(data):
    """حفظ بيانات المستخدمين"""
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()

def agent_exists(agent_id, credentials):
    """التحقق من وجود المستخدم"""
    return agent_id in credentials

def verify_password(agent_id, password, credentials):
    """التحقق من صحة كلمة المرور"""
    if agent_id not in credentials:
        return False
    return credentials[agent_id]['password'] == hash_password(password)

def register_new_agent(agent_id, password, credentials):
    """تسجيل مستخدم جديد"""
    credentials[agent_id] = {
        'password': hash_password(password),
        'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_login': None,
        'failed_attempts': 0
    }
    save_credentials(credentials)
    log_event(agent_id, 'REGISTRATION', 'New agent registered')

def update_last_login(agent_id, credentials):
    """تحديث وقت آخر تسجيل دخول"""
    credentials[agent_id]['last_login'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    credentials[agent_id]['failed_attempts'] = 0
    save_credentials(credentials)

def increment_failed_attempts(agent_id, credentials):
    """زيادة محاولات الفشل"""
    credentials[agent_id]['failed_attempts'] = credentials[agent_id].get('failed_attempts', 0) + 1
    save_credentials(credentials)

# ==================== ENCRYPTION & DECRYPTION ====================
def encrypt_message(message, target_pub_pem):
    """تشفير الرسالة"""
    session_key = Fernet.generate_key()
    cipher_suite = Fernet(session_key)
    encrypted_text = cipher_suite.encrypt(message.encode('utf-8'))
    
    target_pub = serialization.load_pem_public_key(target_pub_pem.encode('utf-8'))
    encrypted_session_key = target_pub.encrypt(
        session_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    blob = encrypted_session_key.hex() + "||" + encrypted_text.decode('utf-8')
    return blob

def decrypt_message(blob):
    """فك تشفير الرسالة"""
    try:
        enc_sess_key_hex, enc_text_str = blob.split("||")
        enc_sess_key = bytes.fromhex(enc_sess_key_hex)
        session_key = private_key.decrypt(
            enc_sess_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        cipher_suite = Fernet(session_key)
        return cipher_suite.decrypt(enc_text_str.encode('utf-8')).decode('utf-8')
    except:
        return "[ENCRYPTED DATA - CANNOT DECRYPT]"

# ==================== SECURITY PROTOCOLS ====================
def binary_matrix_hack():
    """بروتوكول التحقق من الأمان - حل مصفوفة الأرقام الثنائية"""
    print("\n")
    print_centered("[!] SECURITY VERIFICATION PROTOCOL (LEVEL 5)", Fore.RED, Style.BRIGHT)
    print_centered("-" * 50, Fore.RED)
    time.sleep(1)
    
    rows, cols = 8, 8
    matrix = [[random.choice([0, 1]) for _ in range(cols)] for _ in range(rows)]
    
    row_visual_width = 8 + (cols * 5)
    width = get_width()
    global_padding = max(0, (width - row_visual_width) // 2)

    header_str = "  ".join([f"C{i+1}" for i in range(cols)])
    print(" " * (global_padding + 9) + Fore.WHITE + header_str) 
    print(" " * (global_padding + 9) + Fore.WHITE + "-" * len(header_str))

    for i in range(rows):
        prefix = f"ROW {i+1} |"
        row_content = ""
        for val in matrix[i]:
            color = Fore.GREEN if val == 1 else Fore.RED
            row_content += color + f" {val}  " 
            
        print(" " * global_padding + Fore.WHITE + prefix + row_content)
        time.sleep(0.03)
    print("\n")

    correct_password = ""
    for c in range(cols):
        ones_count = sum(matrix[r][c] for r in range(rows))
        correct_password += "1" if ones_count % 2 != 0 else "0"

    print_centered("DECRYPTION KEY REQUIRED FOR DATABASE ACCESS.", Fore.YELLOW)
    user_input = input_centered("ENTER 8-BIT BINARY CODE >> ", Fore.YELLOW)
    
    print_centered("ANALYZING PATTERN MATCH...", Fore.BLUE)
    time.sleep(1.5)
    return user_input.strip() == correct_password

# ==================== COMMAND INTERFACE ====================
def show_help():
    """عرض قائمة الأوامر"""
    print("\n")
    print_centered("=" * 70, Fore.CYAN)
    print_centered("[COMMAND HELP MENU - قائمة الأوامر]", Fore.CYAN, Style.BRIGHT)
    print_centered("=" * 70, Fore.CYAN)
    print("\n")
    
    commands = [
        ("help", "عرض هذه القائمة (Show this help menu)"),
        ("exit", "قطع الاتصال والخروج (Disconnect and exit)"),
        ("status", "عرض حالتك الحالية (Show your status)"),
        ("info", "معلومات الاتصال (Connection information)"),
        ("clear", "مسح الشاشة (Clear screen)"),
        ("history", "عرض سجل الرسائل (Show message history)"),
        ("profile", "عرض ملفك الشخصي (Show your profile)"),
        ("settings", "إعدادات النظام (System settings)"),
    ]
    
    for cmd, desc in commands:
        print_centered(f"{Fore.GREEN}{cmd:<12} {Fore.YELLOW}→ {Fore.WHITE}{desc}", Fore.WHITE)
    
    print("\n")
    print_centered("=" * 70, Fore.CYAN)
    print("\n")

def show_status():
    """عرض حالة الاتصال"""
    print("\n")
    print_centered("[AGENT STATUS - حالة الجهاز]", Fore.GREEN, Style.BRIGHT)
    print_centered("-" * 50, Fore.GREEN)
    print_centered(f"Status: {Fore.GREEN}ONLINE", Fore.CYAN)
    print_centered(f"Connection: {Fore.GREEN}ESTABLISHED", Fore.CYAN)
    print_centered(f"Encryption: {Fore.GREEN}ACTIVE", Fore.CYAN)
    print_centered(f"Messages Sent: {len(messages_history)}", Fore.CYAN)
    print("\n")

def show_info(my_code, target_code):
    """عرض معلومات الاتصال"""
    print("\n")
    print_centered("[CONNECTION INFO - معلومات الاتصال]", Fore.BLUE, Style.BRIGHT)
    print_centered("-" * 50, Fore.BLUE)
    print_centered(f"Your Agent ID: {Fore.YELLOW}{my_code}", Fore.CYAN)
    print_centered(f"Target Agent ID: {Fore.YELLOW}{target_code}", Fore.CYAN)
    print_centered(f"Encryption Type: {Fore.GREEN}RSA-2048 + Fernet", Fore.CYAN)
    print_centered(f"Server: {Fore.GREEN}{SERVER_IP}:{SERVER_PORT}", Fore.CYAN)
    print_centered(f"Status: {Fore.GREEN}CONNECTED (E2EE)", Fore.CYAN)
    print("\n")

def show_history():
    """عرض سجل الرسائل"""
    if not messages_history:
        print_centered("No messages in history", Fore.YELLOW)
        return
    
    print("\n")
    print_centered("[MESSAGE HISTORY - سجل الرسائل]", Fore.MAGENTA, Style.BRIGHT)
    print_centered("-" * 50, Fore.MAGENTA)
    print("\n")
    
    for i, msg in enumerate(messages_history[-10:], 1):
        print_centered(f"{i}. {msg[:60]}...", Fore.WHITE)
    
    print("\n")

def show_profile(agent_id, credentials):
    """عرض ملف المستخدم الشخصي"""
    print("\n")
    print_centered("[USER PROFILE - ملفك الشخصي]", Fore.CYAN, Style.BRIGHT)
    print_centered("-" * 50, Fore.CYAN)
    
    if agent_id in credentials:
        user_data = credentials[agent_id]
        print_centered(f"Agent ID: {Fore.YELLOW}{agent_id}", Fore.CYAN)
        print_centered(f"Registered: {user_data.get('created_at', 'N/A')}", Fore.CYAN)
        print_centered(f"Last Login: {user_data.get('last_login', 'Never')}", Fore.CYAN)
        print_centered(f"Total Messages: {len(messages_history)}", Fore.CYAN)
    
    print("\n")

def show_settings():
    """عرض الإعدادات"""
    print("\n")
    print_centered("[SYSTEM SETTINGS - إعدادات النظام]", Fore.YELLOW, Style.BRIGHT)
    print_centered("-" * 50, Fore.YELLOW)
    print_centered("Server Configuration:", Fore.YELLOW)
    print_centered(f"  IP: {SERVER_IP}", Fore.WHITE)
    print_centered(f"  Port: {SERVER_PORT}", Fore.WHITE)
    print_centered("Encryption Settings:", Fore.YELLOW)
    print_centered(f"  RSA Key Size: 2048 bits", Fore.WHITE)
    print_centered(f"  Session Cipher: Fernet (AES-128)", Fore.WHITE)
    print("\n")

# ==================== NETWORK COMMUNICATION ====================
def receive_messages(target_code):
    """استقبال الرسائل من الخادم"""
    global target_public_key_cache
    while True:
        try:
            data = client.recv(10240)
            if not data: break
            packet = data.decode('utf-8')
            
            if packet.startswith("[KEY_FOUND]"):
                target_public_key_cache = packet.split("]")[1]
                continue
            
            if packet.startswith("[KEY_NOT_FOUND]"):
                target_public_key_cache = "ERROR"
                continue

            if packet.startswith("[INCOMING]"):
                _, content = packet.split("]", 1)
                sender, blob = content.split("|", 1)
                
                play_sound()
                msg_text = decrypt_message(blob)
                messages_history.append(f"[FROM {sender}] {msg_text}")
                
                print("\n")
                print_centered(f"[MSG] FROM {sender} (E2EE)", Fore.CYAN)
                print_centered(f">> {msg_text}", Fore.GREEN, Style.BRIGHT)
                print_centered(f"[TIME] {datetime.datetime.now().strftime('%H:%M:%S')}", Fore.GRAY)
                print("\n")
                
                prompt = "[SECURE INPUT] >> "
                padding = max(0, (get_width() - len(prompt) - 10) // 2)
                sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
                sys.stdout.flush()

        except: 
            break

def send_messages(my_code, target_code):
    """إرسال الرسائل"""
    global target_public_key_cache
    while True:
        msg = input("")
        
        # معالجة الأوامر
        if msg.lower() == 'help':
            show_help()
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
            continue
        
        if msg.lower() == 'exit':
            print_centered("[*] DISCONNECTING...", Fore.YELLOW)
            log_event(my_code, 'LOGOUT', 'User disconnected')
            time.sleep(1)
            break
        
        if msg.lower() == 'status':
            show_status()
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
            continue
        
        if msg.lower() == 'info':
            show_info(my_code, target_code)
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
            continue
        
        if msg.lower() == 'history':
            show_history()
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
            continue
        
        if msg.lower() == 'clear':
            clear_screen()
            print_centered(f"CONNECTED TO: {target_code}", Fore.GREEN)
            print_centered("-" * 50)
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
            continue
        
        if msg.lower() == 'profile':
            credentials = load_credentials()
            show_profile(my_code, credentials)
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
            continue
        
        if msg.lower() == 'settings':
            show_settings()
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
            continue
        
        # تحقق من الرسالة الفارغة
        if not msg.strip():
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
            continue
        
        # إرسال الرسالة الفعلية
        target_public_key_cache = None
        client.send(f"[GET_KEY]{target_code}".encode('utf-8'))
        
        wait_timer = 0
        while target_public_key_cache is None and wait_timer < 20:
            time.sleep(0.1)
            wait_timer += 1
            
        if target_public_key_cache == "ERROR" or target_public_key_cache is None:
             print_centered("[!] ERROR: TARGET AGENT NOT AVAILABLE.", Fore.RED)
             log_event(my_code, 'ERROR', f'Failed to reach {target_code}')
             prompt = "[SECURE INPUT] >> "
             padding = max(0, (get_width() - len(prompt) - 10) // 2)
             sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
             sys.stdout.flush()
             continue

        try:
            encrypted_blob = encrypt_message(msg, target_public_key_cache)
            packet = f"[MSG]{target_code}|{encrypted_blob}"
            client.send(packet.encode('utf-8'))
            
            messages_history.append(f"[TO {target_code}] {msg}")
            print_centered("[SENT] 2048-BIT ENCRYPTED PACKET.", Fore.GREEN)
            log_event(my_code, 'SEND_MSG', f'Message sent to {target_code}')
            
            prompt = "[SECURE INPUT] >> "
            padding = max(0, (get_width() - len(prompt) - 10) // 2)
            sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
            sys.stdout.flush()
        except Exception as e:
            print_centered(f"[ERROR] SEND FAILED: {e}", Fore.RED)
            log_event(my_code, 'ERROR', f'Send failed: {str(e)}')

# ==================== MAIN AUTHENTICATION SYSTEM ====================
def start_system():
    """نظام بدء التطبيق والمصادقة الرئيسي"""
    global target_public_key_cache, current_agent_id
    clear_screen()
    print("\n"*2)
    print_centered("INITIALIZING RSA-2048 CRYPTO ENGINE...", Fore.CYAN)
    time.sleep(1)
    
    credentials = load_credentials()
    
    my_agent_code = input_centered("ENTER YOUR AGENT ID: ", Fore.GREEN)
    current_agent_id = my_agent_code
    
    # التحقق من وجود المستخدم
    if agent_exists(my_agent_code, credentials):
        print("\n")
        print_centered("[*] AGENT FOUND IN SYSTEM DATABASE...", Fore.YELLOW)
        time.sleep(0.5)
        
        # طلب كلمة المرور بدلاً من المصفوفة
        attempts = 0
        while attempts < 3:
            password = input_centered("ENTER YOUR PASSWORD: ", Fore.YELLOW)
            
            if verify_password(my_agent_code, password, credentials):
                print_centered("PASSWORD VERIFIED. GRANTING ACCESS...", Fore.GREEN)
                update_last_login(my_agent_code, credentials)
                log_event(my_agent_code, 'LOGIN', 'Successful login')
                time.sleep(1)
                break
            else:
                attempts += 1
                increment_failed_attempts(my_agent_code, credentials)
                if attempts < 3:
                    print_centered(f"[!] INCORRECT PASSWORD. ATTEMPTS REMAINING: {3 - attempts}", Fore.RED)
                    time.sleep(1)
                else:
                    print_centered("ACCESS DENIED. MAX ATTEMPTS EXCEEDED.", Fore.RED)
                    log_event(my_agent_code, 'LOGIN_FAILED', 'Max attempts exceeded')
                    time.sleep(1)
                    return
    else:
        # مستخدم جديد - حل المصفوفة وإعداد كلمة المرور
        print("\n")
        print_centered("[*] NEW AGENT REGISTRATION REQUIRED...", Fore.YELLOW)
        time.sleep(0.5)
        
        if not binary_matrix_hack():
            print_centered("ACCESS DENIED.", Fore.RED)
            log_event(my_agent_code, 'REGISTRATION_FAILED', 'Incorrect security code')
            return
        
        # طلب كلمة المرور الجديدة
        print("\n")
        while True:
            new_password = input_centered("CREATE YOUR PASSWORD: ", Fore.YELLOW)
            confirm_password = input_centered("CONFIRM PASSWORD: ", Fore.YELLOW)
            
            if new_password != confirm_password:
                print_centered("[!] PASSWORDS DO NOT MATCH. TRY AGAIN.", Fore.RED)
                time.sleep(0.5)
                continue
            
            if len(new_password) < 6:
                print_centered("[!] PASSWORD MUST BE AT LEAST 6 CHARACTERS.", Fore.RED)
                time.sleep(0.5)
                continue
            
            break
        
        register_new_agent(my_agent_code, new_password, credentials)
        print_centered("AGENT REGISTERED SUCCESSFULLY.", Fore.GREEN)
        time.sleep(1)

    # الاتصال بالخادم
    try:
        client.connect((SERVER_IP, SERVER_PORT))
        client.send(f"[REGISTER]{my_agent_code}|{pem_public}".encode('utf-8'))
    except:
        print_centered("SERVER UNREACHABLE.", Fore.RED)
        return

    clear_screen()
    print("\n"*2)
    print_centered(f"IDENTITY VERIFIED: {my_agent_code}", Fore.GREEN)
    print_centered(f"PUBLIC KEY FINGERPRINT: {pem_public[50:80]}...", Fore.BLUE)
    print_centered("-" * 50)
    
    # بدء خيط استقبال الرسائل
    threading.Thread(target=receive_messages, args=(None,), daemon=True).start()

    # اختيار المستقبل
    while True:
        target_agent_code = input_centered("ENTER TARGET AGENT ID: ", Fore.MAGENTA)
        
        print_centered(f"[*] FETCHING KEY FOR {target_agent_code}...", Fore.YELLOW)
        target_public_key_cache = None
        client.send(f"[GET_KEY]{target_agent_code}".encode('utf-8'))
        
        waits = 0
        while target_public_key_cache is None and waits < 15:
            time.sleep(0.2)
            waits += 1
            
        if target_public_key_cache == "ERROR":
            print("\n")
            print_centered(f"[!] AGENT '{target_agent_code}' NOT REGISTERED.", Fore.RED)
            print_centered("    TARGET MUST LOGIN AT LEAST ONCE TO GENERATE KEYS.", Fore.RED)
            print_centered("-" * 30, Fore.RED)
        elif target_public_key_cache:
            print_centered("[+] SECURE CHANNEL ESTABLISHED.", Fore.GREEN)
            log_event(my_agent_code, 'CONNECT_SUCCESS', f'Connected to {target_agent_code}')
            break 
        else:
            print_centered("[!] SERVER TIMEOUT.", Fore.RED)

    prompt = "[SECURE INPUT] >> "
    padding = max(0, (get_width() - len(prompt) - 10) // 2)
    sys.stdout.write(" " * padding + Fore.YELLOW + prompt)
    sys.stdout.flush()
    
    send_messages(my_agent_code, target_agent_code)

# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    try:
        start_system()
    except KeyboardInterrupt:
        print("\n")
        print_centered("CONNECTION TERMINATED.", Fore.RED)
        log_event(current_agent_id or 'UNKNOWN', 'INTERRUPT', 'User interrupted connection')
    except Exception as e:
        print_centered(f"FATAL ERROR: {e}", Fore.RED)
        log_event(current_agent_id or 'UNKNOWN', 'FATAL_ERROR', str(e))
