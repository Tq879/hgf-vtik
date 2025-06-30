from flask import Flask, request, jsonify, session
import datetime
import random
import requests
import re
import threading
import time
from hashlib import md5
from time import time as T
import secrets
import string
import pytz

# Cấu hình
ADMIN_SECRET_CODE = 'ADMINTQ99899'
MAX_KEY_USAGE_SECONDS = 400
KEY_COOLDOWN_SECONDS = 3600
MAX_INPUT_SECONDS = 1000

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

VN_TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')

# Lớp Signature
class Signature:
    def __init__(self, params: str, data: str, cookies: str) -> None:
        self.params = params
        self.data = data
        self.cookies = cookies

    def hash(self, data: str) -> str:
        return str(md5(data.encode()).hexdigest())

    def calc_gorgon(self) -> str:
        gorgon = self.hash(self.params) + (self.hash(self.data) if self.data else "0"*32) + \
                 (self.hash(self.cookies) if self.cookies else "0"*32) + "0"*32
        return gorgon

    def get_value(self):
        gorgon = self.calc_gorgon()
        return self.encrypt(gorgon)

    def encrypt(self, data: str):
        unix = int(T())
        len_val = 0x14
        key = [0xDF, 0x77, 0xB9, 0x40, 0xB9, 0x9B, 0x84, 0x83, 0xD1, 0xB9, 0xCB, 0xD1, 0xF7, 0xC2, 0xB9, 0x85, 0xC3, 0xD0, 0xFB, 0xC3]
        param_list = []
        for i in range(0, 12, 4):
            temp = data[8 * i : 8 * (i + 1)]
            for j in range(4):
                param_list.append(int(temp[j * 2 : (j + 1) * 2], 16))
        param_list.extend([0x0, 0x6, 0xB, 0x1C])
        H = int(hex(unix), 16)
        param_list.extend([(H >> 24) & 0xFF, (H >> 16) & 0xFF, (H >> 8) & 0xFF, H & 0xFF])
        eor_result_list = [A ^ B for A, B in zip(param_list, key)]
        for i in range(len_val):
            C = self.reverse(eor_result_list[i])
            D = eor_result_list[(i + 1) % len_val]
            E = C ^ D
            F = self.rbit(E)
            eor_result_list[i] = ((F ^ 0xFFFFFFFF) ^ len_val) & 0xFF
        result = "".join(self.hex_string(param) for param in eor_result_list)
        return {"X-Gorgon": "840280416000" + result, "X-Khronos": str(unix)}

    def rbit(self, num):
        result = ""
        tmp_string = bin(num)[2:].zfill(8)
        for i in range(8):
            result += tmp_string[7 - i]
        return int(result, 2)

    def hex_string(self, num):
        tmp_string = hex(num)[2:]
        return "0" + tmp_string if len(tmp_string) < 2 else tmp_string

    def reverse(self, num):
        tmp_string = self.hex_string(num)
        return int(tmp_string[1:] + tmp_string[:1], 16)

# Biến toàn cục
current_stop_flag = threading.Event()

# Hàm gửi view
def send_view_thread(video_id: str):
    url_view = 'https://api16-core-c-alisg.tiktokv.com/aweme/v1/aweme/stats/?ac=WIFI&op_region=VN'
    sig = Signature(params='', data='', cookies='').get_value()
    while not current_stop_flag.is_set():
        random_hex = secrets.token_hex(16)
        headers_view = {
            'Host': 'api16-core-c-alisg.tiktokv.com',
            'Content-Length': '138',
            'Sdk-Version': '2',
            'Passport-Sdk-Version': '5.12.1',
            'X-Tt-Token': f'01{random_hex}0263ef2c096122cc1a97dec9cd12a6c75d81d3994668adfbb3ffca278855dd15c8056ad18161b26379bbf95d25d1f065abd5dd3a812f149ca11cf57e4b85ebac39d - 1.0.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'TikTok 37.0.4 rv:174014 (iPhone; iOS 14.2; ar_SA@calendar=gregorian) Cronet',
            'X-Ss-Stub': '727D102356930EE8C1F61B112F038D96',
            'X-Tt-Store-Idc': 'alisg',
            'X-Tt-Store-Region': 'sa',
            'X-Ss-Dp': '1233',
            'X-Tt-Trace-Id': '00-33c8a619105fd09f13b65546057d04d1-33c8a619105fd09f-01',
            'Accept-Encoding': 'gzip, deflate',
            'X-Khronos': sig['X-Khronos'],
            'X-Gorgon': sig['X-Gorgon'],
            'X-Common-Params-V2': (
                "pass-region=1&pass-route=1&language=ar&version_code=17.4.0&app_name=musical_ly"
                "&vid=0F62BF08-8AD6-4A4D-A870-C098F5538A97&app_version=17.4.0&carrier_region=VN"
                "&channel=App%20Store&mcc_mnc=45201&device_id=6904193135771207173&tz_offset=25200"
                "&account_region=VN&sys_region=VN&aid=1233&residence=VN&screen_width=1125&uoo=1"
                "&openudid=c0c519b4e8148dec69410df9354e6035aa155095&os_api=18&os_version=14.2"
                "&app_language=ar&tz_name=Asia%2FHo_Chi_Minh¤t_region=VN&device_platform=iphone"
                "&build_number=174014&device_type=iPhone14,6&iid=6958149070179878658"
                "&idfa=00000000-0000-0000-0000-000000000000&locale=ar&cdid=D1D404AE-ABDF-4973-983C-CC723EA69906"
            ),
        }
        cookie_view = {'sessionid': random_hex}
        start = datetime.datetime(2020, 1, 1)
        end = datetime.datetime(2024, 12, 31)
        random_dt = start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
        data = {
            'action_time': int(time.time()),
            'aweme_type': 0,
            'first_install_time': int(random_dt.timestamp()),
            'item_id': video_id,
            'play_delta': 1,
            'tab_type': 4
        }
        try:
            requests.post(url_view, data=data, headers=headers_view, cookies=cookie_view, timeout=1)
            sig = Signature(params='ac=WIFI&op_region=VN', data=str(data), cookies=str(cookie_view)).get_value()
        except Exception:
            continue

# Hàm chạy logic tăng view
def run_tiktok_booster_logic(link: str, target_seconds: int):
    global current_stop_flag
    current_stop_flag.clear()
    headers_id = {
        'Connection': 'close',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
        'Accept': 'text/html'
    }
    try:
        page = requests.get(link, headers=headers_id, timeout=10).text
        match = re.search(r'"video":\{"id":"(\d+)"', page)
        if match:
            video_id = match.group(1)
            print(f'[+] Lấy ID Video thành công: {video_id}')
            print(f'[+] Script sẽ chạy trong {target_seconds} giây')
        else:
            print('[-] Không tìm thấy ID Video')
            return {"status": "error", "message": "Không tìm thấy ID Video"}
    except Exception as e:
        print(f'[-] Lỗi khi lấy ID Video: {e}')
        return {"status": "error", "message": f"Lỗi khi lấy ID Video: {e}"}

    threads = []
    timer_thread = threading.Thread(target=lambda: (time.sleep(target_seconds), current_stop_flag.set()))
    timer_thread.daemon = True
    timer_thread.start()
    threads.append(timer_thread)

    for _ in range(450):
        t = threading.Thread(target=send_view_thread, args=(video_id,))
        t.daemon = True
        t.start()
        threads.append(t)

    timer_thread.join()
    print(f'[+] Đã chạy đủ {target_seconds} giây, dừng chạy!')
    time.sleep(1)
    print(f'[+] Đã chờ 1 giây, sẵn sàng cho lần buff tiếp theo.')
    return {"status": "success", "message": "Hoàn thành", "final_message": "Bạn có thể buff view tiếp"}

# Quản lý Key
valid_keys = {}
key_usage_data = {}

def generate_key(key_type: str = "normal"):
    prefix = "BotV2_" if key_type == "normal" else "BotV2_VIP_"
    if key_type not in ["normal", "vip"]:
        raise ValueError("Invalid key_type. Must be 'normal' or 'vip'.")
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=16))

def shorten_url(url: str) -> str:
    api_url = f"https://yeumoney.com/QL_api.php?token=c9fe97c0dd99427393beee2c785f274cb2a79041502456c78f1e7f03a18b0f58&format=json&url={url}"
    print(f"Đang cố gắng rút gọn URL: {url}")
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            try:
                json_data = response.json()
                if "shortenedUrl" in json_data and json_data["shortenedUrl"].startswith("http"):
                    print(f"Rút gọn thành công (JSON): {json_data['shortenedUrl']}")
                    return json_data['shortenedUrl']
                elif "url" in json_data and json_data["url"].startswith("http"):
                    print(f"Rút gọn thành công (JSON - trường 'url'): {json_data['url']}")
                    return json_data['url']
            except json.JSONDecodeError:
                response_text = response.text.strip()
                if response_text.startswith("http"):
                    print(f"Rút gọn thành công (Text): {response_text}")
                    return response_text
        else:
            print(f"API rút gọn link trả về lỗi HTTP: Status Code={response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối khi rút gọn URL: {e}")
    print(f"Không thể rút gọn URL. Trả về URL gốc: {url}")
    return url

# Flask Routes
@app.route('/')
def index():
    redeem_code = session.get('redeem_code', '')
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok View Booster</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #007bff;
            --secondary-color: #28a745;
            --accent-color: #dc3545;
            --bg-color: #f8f9fa;
            --card-bg-color: #ffffff;
            --text-color: #343a40;
            --border-color: #e9ecef;
            --shadow-color: rgba(0, 0, 0, 0.08);
        }}
        body {{
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
        }}
        .container {{
            background-color: var(--card-bg-color);
            padding: 35px;
            border-radius: 12px;
            box-shadow: 0 8px 20px var(--shadow-color);
            width: 100%;
            max-width: 550px;
            text-align: center;
            border: 1px solid var(--border-color);
        }}
        h1 {{
            color: var(--primary-color);
            margin-bottom: 30px;
            font-size: 2.2em;
            font-weight: 700;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 700;
            text-align: left;
            color: var(--text-color);
            font-size: 1.05em;
        }}
        input[type="text"], input[type="number"] {{
            width: calc(100% - 24px);
            padding: 12px;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
            box-sizing: border-box;
        }}
        input[type="text"]:focus, input[type="number"]:focus {{
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
            outline: none;
        }}
        .button-group {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }}
        button {{
            background-color: var(--secondary-color);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 700;
            transition: background-color 0.3s ease, transform 0.2s ease;
            flex-grow: 1;
            min-width: 150px;
        }}
        button:hover {{
            background-color: #218838;
            transform: translateY(-2px);
        }}
        button:active {{
            transform: translateY(0);
        }}
        .button-group button:nth-child(2) {{
            background-color: var(--primary-color);
        }}
        .button-group button:nth-child(2):hover {{
            background-color: #0056b3;
        }}
        .button-group button:nth-child(3) {{
            background-color: #6c757d;
        }}
        .button-group button:nth-child(3):hover {{
            background-color: #5a6268;
        }}
        .button-group button:nth-child(4) {{
            background-color: var(--accent-color);
        }}
        .button-group button:nth-child(4):hover {{
            background-color: #c82333;
        }}
        #statusMessage {{
            margin-top: 30px;
            padding: 15px;
            border-radius: 8px;
            font-weight: 700;
            display: none;
            text-align: left;
        }}
        .status-success {{
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status-error {{
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .status-info {{
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }}
        #generatedKeyLink {{
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-size: 1.1em;
            word-wrap: break-word;
            text-align: left;
            background-color: var(--bg-color);
            border: 1px dashed var(--border-color);
            display: none;
        }}
        #generatedKeyLink a {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 700;
        }}
        #generatedKeyLink a:hover {{
            text-decoration: underline;
        }}
        .admin-panel {{
            margin-top: 35px;
            padding-top: 25px;
            border-top: 1px solid var(--border-color);
            text-align: left;
            display: none;
        }}
        .admin-panel h2 {{
            color: var(--primary-color);
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        .key-count {{
            font-size: 1.1em;
            font-weight: 700;
            margin-bottom: 15px;
            color: var(--primary-color);
            line-height: 1.6;
            display: none;
        }}
        .admin-buttons {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
        }}
        .admin-buttons label {{
            margin-bottom: 0;
            margin-right: 5px;
            white-space: nowrap;
        }}
        .admin-buttons input[type="number"] {{
            width: 70px;
            margin-bottom: 0;
        }}
        .admin-buttons button {{
            background-color: var(--primary-color);
            flex-grow: 0;
            min-width: unset;
        }}
        .admin-buttons button:hover {{
            background-color: #0056b3;
        }}
        #adminGeneratedKeyLink {{
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-size: 1.1em;
            word-wrap: break-word;
            text-align: left;
            background-color: var(--bg-color);
            border: 1px dashed var(--border-color);
            display: none;
        }}
        #adminGeneratedKeyLink a {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 700;
        }}
        #adminGeneratedKeyLink a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 600px) {{
            .container {{
                padding: 25px;
                margin: 10px;
            }}
            h1 {{
                font-size: 1.8em;
            }}
            button {{
                font-size: 1em;
                padding: 10px 20px;
                min-width: unset;
                flex-basis: calc(50% - 5px);
            }}
            .button-group {{
                flex-direction: row;
            }}
            .admin-buttons {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .admin-buttons input[type="number"] {{
                width: calc(100% - 24px);
                margin-bottom: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>TikTok View Booster</h1>
        <label for="videoLink">Link Video TIKTOK:</label>
        <input type="text" id="videoLink" placeholder="Dán link video TikTok vào đây" required>
        <label for="targetSeconds">Số giây muốn chạy:</label>
        <input type="number" id="targetSeconds" value="60" min="1" max="{MAX_INPUT_SECONDS}" required>
        <label for="redeemCode">Mã Redeem:</label>
        <input type="text" id="redeemCode" placeholder="Nhập mã redeem của bạn" value="{redeem_code}">
        <div class="button-group">
            <button onclick="startBoost()">Bắt đầu Tăng View</button>
            <button onclick="handleRedeemOrAdmin()">Redeem</button>
            <button onclick="getNewKey('normal')">Lấy Key Thường</button>
            <button onclick="window.open('https://zalo.me/0775815616', '_blank')">Mua VIP</button>
        </div>
        <div id="statusMessage"></div>
        <div id="generatedKeyLink"></div>
        <div id="adminPanel" class="admin-panel">
            <h2>Bảng điều khiển Admin</h2>
            <div class="key-count">
                Tổng số Key Thường: <span id="totalNormalKeys">0</span><br>
                Tổng số Key VIP: <span id="totalVipKeys">0</span>
            </div>
            <div class="admin-buttons">
                <label for="vipExpiryDays">Hết hạn sau (ngày):</label>
                <input type="number" id="vipExpiryDays" value="30" min="1">
                <button onclick="createVipKey('self')">Tạo Key VIP cho mình</button>
                <button onclick="createVipKey('other')">Tạo Key VIP cho người khác</button>
                <button onclick="createVipKey('all')">Tạo Key VIP cho tất cả</button>
                <button onclick="createNormalKey()">Tạo Key Thường Mới</button>
            </div>
            <div id="adminGeneratedKeyLink"></div>
        </div>
    </div>
    <script>
        let isAdminSession = false;
        const MAX_INPUT_SECONDS_JS = {MAX_INPUT_SECONDS};
        function showStatusMessage(message, type, redirectUrl = null) {{
            const statusMessageDiv = document.getElementById('statusMessage');
            statusMessageDiv.style.display = 'block';
            statusMessageDiv.className = `status-${{type}}`;
            statusMessageDiv.innerHTML = message;
            if (redirectUrl) {{
                setTimeout(() => {{
                    window.open(redirectUrl, '_blank');
                }}, 1000);
            }}
        }}
        async function handleRedeemOrAdmin() {{
            const code = document.getElementById('redeemCode').value;
            showStatusMessage('Đang xử lý...', 'info');
            if (!code) {{
                showStatusMessage('Vui lòng nhập mã redeem.', 'error');
                return;
            }}
            try {{
                const response = await fetch('/process_code', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ code }})
                }});
                const data = await response.json();
                if (response.ok) {{
                    showStatusMessage(data.message, 'success');
                    if (data.is_admin) {{
                        isAdminSession = true;
                        document.getElementById('adminPanel').style.display = 'block';
                    }} else {{
                        isAdminSession = false;
                        document.getElementById('adminPanel').style.display = 'none';
                    }}
                }} else {{
                    showStatusMessage(`Lỗi: ${{data.message || 'Không xác định'}}`, 'error');
                    isAdminSession = false;
                    document.getElementById('adminPanel').style.display = 'none';
                }}
            }} catch (error) {{
                console.error('Lỗi khi gửi yêu cầu xử lý mã:', error);
                showStatusMessage('Đã xảy ra lỗi khi kết nối đến máy chủ để xử lý mã.', 'error');
                isAdminSession = false;
            }}
        }}
        async function startBoost() {{
            const videoLink = document.getElementById('videoLink').value;
            let targetSeconds = parseInt(document.getElementById('targetSeconds').value);
            const redeemCode = document.getElementById('redeemCode').value;
            showStatusMessage('Đang gửi yêu cầu...', 'info');
            if (!videoLink || isNaN(targetSeconds) || targetSeconds <= 0) {{
                showStatusMessage('Vui lòng nhập đầy đủ Link Video và Số giây muốn chạy hợp lệ.', 'error');
                return;
            }}
            if (targetSeconds > MAX_INPUT_SECONDS_JS) {{
                showStatusMessage(`Số giây tối đa cho phép là ${{MAX_INPUT_SECONDS_JS}} giây.`, 'error');
                return;
            }}
            if (!redeemCode) {{
                showStatusMessage('Vui lòng nhập mã Redeem vào ô "Mã Redeem / Mã Admin" để sử dụng chức năng này.', 'error');
                return;
            }}
            try {{
                const sessionResponse = await fetch('/set_redeem_code', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ code: redeemCode }})
                }});
                const sessionData = await sessionResponse.json();
                if (!sessionResponse.ok) {{
                    console.error('Lỗi khi lưu mã vào session:', sessionData.message);
                }}
            }} catch (error) {{
                console.error('Lỗi khi gửi yêu cầu lưu mã:', error);
            }}
            try {{
                const response = await fetch('/start_boost', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ link: videoLink, seconds: targetSeconds, redeem_key: redeemCode }})
                }});
                const data = await response.json();
                if (response.ok) {{
                    let remainingTime = data.seconds_to_run;
                    const countdownInterval = setInterval(() => {{
                        if (remainingTime > 0) {{
                            showStatusMessage(`Còn ${{remainingTime}} giây nữa sẽ xong...`, 'info');
                            remainingTime--;
                        }} else {{
                            clearInterval(countdownInterval);
                            showStatusMessage('Đợi 1 giây nữa...', 'info');
                            setTimeout(() => {{
                                showStatusMessage(data.final_message || 'Bạn có thể buff view tiếp', 'success');
                            }}, 1000);
                        }}
                    }}, 1000);
                }} else {{
                    showStatusMessage(`Lỗi: ${{data.message || 'Không xác định'}}`, 'error');
                }}
            }} catch (error) {{
                console.error('Lỗi khi gửi yêu cầu:', error);
                showStatusMessage('Đã xảy ra lỗi khi kết nối đến máy chủ.', 'error');
            }}
        }}
        async function generateKeyRequest(keyType, expiryDays, fromAdmin = false) {{
            showStatusMessage('Đang tạo key...', 'info');
            const displayDiv = fromAdmin ? document.getElementById('adminGeneratedKeyLink') : document.getElementById('generatedKeyLink');
            displayDiv.style.display = 'none';
            try {{
                const response = await fetch('/getkey', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key_type: keyType, expiry_days: expiryDays, from_admin: fromAdmin }})
                }});
                const data = await response.json();
                if (response.ok) {{
                    let keyOutput = '';
                    if (keyType === 'vip') {{
                        keyOutput = `<strong>Key VIP của bạn:</strong> <span style="color: var(--accent-color);">${{data.raw_key}}</span>`;
                        showStatusMessage(data.message, 'success');
                    }} else {{
                        keyOutput = `<strong>Key Thường của bạn:</strong> <a href="${{data.display_key}}" target="_blank" style="color: var(--text-color);">${{data.display_key}}</a>`;
                        showStatusMessage(data.message, 'success', data.redirect_url);
                    }}
                    displayDiv.innerHTML = keyOutput;
                    displayDiv.style.display = fromAdmin ? 'block' : 'none';
                    return data;
                }} else {{
                    showStatusMessage(`Lỗi khi tạo key: ${{data.message || 'Không xác định'}}`, 'error');
                    return null;
                }}
            }} catch (error) {{
                console.error('Lỗi khi gửi yêu cầu lấy key:', error);
                showStatusMessage('Đã xảy ra lỗi khi kết nối đến máy chủ để lấy key.', 'error');
                return null;
            }}
        }}
        async function getNewKey(keyType) {{
            showStatusMessage('Đang tạo key...', 'info');
            const displayDiv = document.getElementById('generatedKeyLink');
            displayDiv.style.display = 'none';
            try {{
                const response = await fetch('/getkey', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key_type: keyType, expiry_days: 0, from_admin: false }})
                }});
                const data = await response.json();
                if (response.ok) {{
                    showStatusMessage(data.message, 'success', data.redirect_url);
                    displayDiv.innerHTML = `<strong>Key Thường của bạn:</strong> <a href="${{data.display_key}}" target="_blank" style="color: var(--text-color);">${{data.display_key}}</a>`;
                    displayDiv.style.display = 'none';
                }} else {{
                    showStatusMessage(`Lỗi khi tạo key: ${{data.message || 'Không xác định'}}`, 'error');
                }}
            }} catch (error) {{
                console.error('Lỗi khi gửi yêu cầu lấy key:', error);
                showStatusMessage('Đã xảy ra lỗi khi kết nối đến máy chủ để lấy key.', 'error');
            }}
        }}
        async function createNormalKey() {{
            if (!isAdminSession) {{
                showStatusMessage('Bạn không có quyền thực hiện chức năng này.', 'error');
                return;
            }}
            await generateKeyRequest('normal', 0, true);
        }}
        async function createVipKey(target) {{
            if (!isAdminSession) {{
                showStatusMessage('Bạn không có quyền thực hiện chức năng này.', 'error');
                return;
            }}
            let expiryDays = parseInt(document.getElementById('vipExpiryDays').value);
            if (isNaN(expiryDays) || expiryDays <= 0) {{
                showStatusMessage('Vui lòng nhập số ngày hết hạn hợp lệ cho Key VIP.', 'error');
                return;
            }}
            const data = await generateKeyRequest('vip', expiryDays, true);
            if (data) {{
                const adminGeneratedKeyLinkDiv = document.getElementById('adminGeneratedKeyLink');
                let message = '';
                if (target === 'self') {{
                    message = `Key VIP của bạn: <span style="color: var(--accent-color);">${{data.raw_key}}</span>`;
                    showStatusMessage('Đã tạo Key VIP cho bạn.', 'success');
                }} else if (target === 'other') {{
                    message = `Key VIP cho người khác: <span style="color: var(--accent-color);">${{data.raw_key}}</span>`;
                    showStatusMessage('Đã tạo Key VIP cho người khác.', 'success');
                }} else if (target === 'all') {{
                    message = `Key VIP cho tất cả: <span style="color: var(--accent-color);">${{data.raw_key}}</span>`;
                    showStatusMessage('Đã tạo Key VIP cho tất cả.', 'success');
                }}
                adminGeneratedKeyLinkDiv.innerHTML = message;
                adminGeneratedKeyLinkDiv.style.display = 'block';
            }}
        }}
    </script>
</body>
</html>"""
    return html_content

@app.route('/process_code', methods=['POST'])
def process_code_endpoint():
    data = request.get_json()
    code = data.get('code')
    if not code:
        return jsonify({"status": "error", "message": "Vui lòng cung cấp mã."}), 400
    if code == ADMIN_SECRET_CODE:
        session['is_admin'] = True
        return jsonify({
            "status": "success",
            "message": "Mã admin chính xác! Đã mở khóa bảng điều khiển admin.",
            "is_admin": True,
            "total_normal_keys": 0,
            "total_vip_keys": 0
        })
    if code not in valid_keys:
        return jsonify({"status": "error", "message": "Mã không hợp lệ hoặc không tồn tại."}), 400
    key_data_from_valid = valid_keys[code]
    if key_data_from_valid["is_redeemed"]:
        return jsonify({"status": "error", "message": "Mã này đã được redeem rồi."}), 400
    key_data_from_valid["is_redeemed"] = True
    if key_data_from_valid["type"] == "normal":
        key_usage_data[code] = {
            "type": "normal",
            "used_seconds": 0,
            "locked_until_timestamp": 0,
            "max_usage_seconds": MAX_KEY_USAGE_SECONDS,
            "expiry_date": None
        }
        message = f"Mã thường đã được kích hoạt thành công! Bạn có {MAX_KEY_USAGE_SECONDS} giây sử dụng."
    else:
        key_usage_data[code] = {
            "type": "vip",
            "used_seconds": 0,
            "locked_until_timestamp": 0,
            "max_usage_seconds": -1,
            "expiry_date": key_data_from_valid["expiry_date"]
        }
        message = "Mã VIP đã được kích hoạt thành công! Bạn có thể sử dụng không giới hạn."
        if key_data_from_valid["expiry_date"]:
            expiry_dt_utc = datetime.datetime.fromtimestamp(key_data_from_valid["expiry_date"], tz=pytz.utc)
            expiry_dt_vn = expiry_dt_utc.astimezone(VN_TIMEZONE)
            message += f" (Hết hạn vào {expiry_dt_vn.strftime('%Y-%m-%d %H:%M:%S %Z%z')})"
    session['redeem_code'] = code
    session['is_admin'] = False
    return jsonify({"status": "success", "message": message, "is_admin": False})

@app.route('/check_admin_status', methods=['POST'])
def check_admin_status_endpoint():
    if session.get('is_admin'):
        return jsonify({"status": "success", "is_admin": True, "total_normal_keys": 0, "total_vip_keys": 0})
    return jsonify({"status": "error", "message": "Không có quyền admin."}), 403

@app.route('/set_redeem_code', methods=['POST'])
def set_redeem_code():
    data = request.get_json()
    code = data.get('code')
    if code:
        session['redeem_code'] = code
        return jsonify({"status": "success", "message": "Mã đã được lưu vào session."})
    return jsonify({"status": "error", "message": "Vui lòng cung cấp mã."}), 400

@app.route('/start_boost', methods=['POST'])
def start_boost_endpoint():
    data = request.get_json()
    link = data.get('link')
    seconds = data.get('seconds')
    redeem_key = data.get('redeem_key')
    if not link or not seconds or not redeem_key:
        return jsonify({"status": "error", "message": "Vui lòng cung cấp đầy đủ link, số giây và mã redeem."}), 400
    try:
        seconds = int(seconds)
        if seconds <= 0:
            return jsonify({"status": "error", "message": "Số giây phải lớn hơn 0."}), 400
        if seconds > MAX_INPUT_SECONDS:
            return jsonify({"status": "error", "message": f"Số giây tối đa cho phép là {MAX_INPUT_SECONDS} giây."}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Số giây không hợp lệ."}), 400
    if redeem_key not in key_usage_data:
        return jsonify({"status": "error", "message": "Mã Redeem chưa được kích hoạt hoặc không hợp lệ."}), 400
    key_info = key_usage_data[redeem_key]
    current_time = int(time.time())
    if key_info["type"] == "vip":
        if key_info["expiry_date"] and key_info["expiry_date"] <= current_time:
            return jsonify({"status": "error", "message": "Key VIP này đã hết hạn sử dụng."}), 400
        key_info["used_seconds"] += seconds
        print(f"Key VIP {redeem_key} đã sử dụng thêm {seconds}s. Tổng: {key_info['used_seconds']}s")
    else:
        if key_info["locked_until_timestamp"] > current_time:
            remaining_cooldown = key_info["locked_until_timestamp"] - current_time
            minutes = int(remaining_cooldown / 60)
            return jsonify({"status": "error", "message": f"Chờ {minutes} phút để chạy tiếp."}), 400
        remaining_usage_seconds = MAX_KEY_USAGE_SECONDS - key_info["used_seconds"]
        if seconds > remaining_usage_seconds:
            if remaining_usage_seconds <= 0:
                del key_usage_data[redeem_key]
                if redeem_key in valid_keys:
                    del valid_keys[redeem_key]
                return jsonify({"status": "error", "message": "Key đã hết thời gian sử dụng. Vui lòng lấy key mới."}), 400
            return jsonify({"status": "error", "message": f"Bạn chỉ còn {remaining_usage_seconds} giây sử dụng."}), 400
        key_info["used_seconds"] += seconds
    thread = threading.Thread(target=run_tiktok_booster_logic, args=(link, seconds))
    thread.daemon = True
    thread.start()
    return jsonify({"status": "success", "message": "Đã bắt đầu quá trình tăng view.", "seconds_to_run": seconds, "final_message": "Bạn có thể buff view tiếp"})

@app.route('/redeem', methods=['POST'])
def redeem_endpoint():
    return jsonify({"status": "error", "message": "Endpoint này không còn được sử dụng trực tiếp."}), 400

@app.route('/getkey', methods=['POST'])
def getkey_endpoint():
    data = request.get_json()
    key_type = data.get('key_type', 'normal')
    expiry_days = data.get('expiry_days', 0)
    from_admin = data.get('from_admin', False)
    if not session.get('is_admin') and key_type == "vip":
        return jsonify({"status": "error", "message": "Bạn không có quyền tạo Key VIP."}), 403
    try:
        new_key_string = generate_key(key_type)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    expiry_timestamp = None
    if key_type == "vip" and expiry_days > 0:
        current_datetime_vn = datetime.datetime.now(VN_TIMEZONE)
        expiry_datetime_vn = current_datetime_vn + datetime.timedelta(days=expiry_days)
        expiry_timestamp = int(expiry_datetime_vn.timestamp())
    valid_keys[new_key_string] = {
        "type": key_type,
        "expiry_date": expiry_timestamp,
        "is_redeemed": False
    }
    if key_type == "vip":
        return jsonify({
            "status": "success",
            "raw_key": new_key_string,
            "display_key": new_key_string,
            "message": f"Key VIP của bạn: {new_key_string}"
        })
    else:
        destination_url_with_key = f"https://tqweb.x10.mx/key.html?key={new_key_string}"
        display_key = shorten_url(destination_url_with_key) if not from_admin else new_key_string
        message = "Đã get key thành công đang chuyển trang .." if not from_admin else f"Key Thường của bạn: {new_key_string}"
        return jsonify({
            "status": "success",
            "raw_key": new_key_string,
            "display_key": display_key,
            "message": message,
            "redirect_url": display_key if not from_admin else None
        })

@app.route('/shorten_key_url', methods=['POST'])
def shorten_key_url_endpoint():
    data = request.get_json()
    key = data.get('key')
    if not key:
        return jsonify({"status": "error", "message": "Vui lòng cung cấp key."}), 400
    if key not in valid_keys:
        return jsonify({"status": "error", "message": "Key không hợp lệ hoặc không tồn tại."}), 400
    destination_url_with_key = f"https://tqweb.x10.mx/key.html?key={key}"
    short_url = shorten_url(destination_url_with_key)
    return jsonify({"status": "success", "short_url": short_url})

if __name__ == '__main__':
    print("Tạo 3 key thường mẫu ban đầu...")
    for _ in range(3):
        key = generate_key("normal")
        valid_keys[key] = {"type": "normal", "expiry_date": None, "is_redeemed": False}
        print(f"Key thường mẫu: {key}")
    print("Tạo 1 key VIP mẫu ban đầu (30 ngày)...")
    key_vip = generate_key("vip")
    current_datetime_vn_init = datetime.datetime.now(VN_TIMEZONE)
    expiry_datetime_vn_init = current_datetime_vn_init + datetime.timedelta(days=30)
    expiry_timestamp_vip_init = int(expiry_datetime_vn_init.timestamp())
    valid_keys[key_vip] = {"type": "vip", "expiry_date": expiry_timestamp_vip_init, "is_redeemed": False}
    print(f"Key VIP mẫu: {key_vip} (Hết hạn: {expiry_datetime_vn_init.strftime('%Y-%m-%d %H:%M:%S %Z%z')})")
    app.run(debug=True, host='0.0.0.0', port=5000)
