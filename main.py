import base64
import hashlib
import json
import os
import random
import struct
import threading
import time
import uuid

import requests
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# ==========================================
# ⚙️ الإعدادات الأساسية
# ==========================================
BOT_TOKEN = "6393211947:AAHgM_qZE3GbyLRNLiPpJtvQqaJeQZDF2aE" 
ADMIN_ID = 5952132218  # أيدي المطور الأساسي
PRIVATE_MODE = False

# ملفات الحفظ على الاستضافة
LANG_FILE = "users_lang.json"
STATS_FILE = "users_stats.json"
CHANNELS_FILE = "channels.json"
SETTINGS_FILE = "bot_settings.json"


def load_json(file_path, default=None):
    if default is None:
        default = {}
    if os.path.isfile(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


USER_LANGS = load_json(LANG_FILE, {})
USERS_LIST = load_json(STATS_FILE, {})
REQUIRED_CHANNELS = load_json(CHANNELS_FILE, [])

DEFAULT_SETTINGS = {
    "normal_cooldown": 60,
    "video_cooldown": 300,
    "msg_ar": "⚠️ يجب ان تنتظر للمدة {mins} دقائق للاستخدام مره ثانيه وبشكل مجاني ليتم توزيع الاستخدام علئ المستخدمين البقيه بشكل صح ✅",
    "msg_en": "⚠️ You must wait for {mins} minutes to use it again for free to distribute usage to other users properly ✅",
    "total_messages": 0,
}
BOT_SETTINGS = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
for k, v in DEFAULT_SETTINGS.items():
    if k not in BOT_SETTINGS:
        BOT_SETTINGS[k] = v
save_json(SETTINGS_FILE, BOT_SETTINGS)

LAST_USED_NORMAL = {}
LAST_USED_VIDEO = {}
admin_states = {}


def register_user(user_id):
    uid_str = str(user_id)
    if uid_str not in USERS_LIST:
        USERS_LIST[uid_str] = time.time()
        save_json(STATS_FILE, USERS_LIST)


TEXTS = {
    "ar": {
        "welcome": (
            "👋 أهلاً بك في بوت Remini الذكي للذكاء الاصطناعي!\n\n"
            "📸 **طريقة الاستخدام:**\n"
            "• أرسل أي صورة مباشرة هنا، وستظهر لك أزرار لاختيار نوع المعالجة:\n"
            "  1️⃣ **Enhance:** رفع دقة الصورة وتوضيح الوجه والخلفية.\n"
            "  2️⃣ **Multitool:** تحسين شامل (عزل خلفية + إضاءة + دقة عالية).\n"
            "  3️⃣ **Colorize:** تلوين الصور القديمة والأبيض والأسود 🎨.\n"
            "  4️⃣ **Stylize:** تحويل الصورة إلى رسم كرتوني.\n"
            "  5️⃣ **Magic Video:** تحريك الوجه في فيديو قصير (انتظار 5 دقائق).\n"
            "  6️⃣ **AI Sticker:** صناعة ملصق من ملامح الوجه.\n\n"
            "⭐ **دعم البوت وتطويره:**\n"
            "• اضغط على زر دعم المطور للمساهمة في استمرارية التشغيل للجميع."
        ),
        "force_sub": "⚠️ **عذراً، يجب عليك الاشتراك في قنوات البوت أولاً لتتمكن من استخدامه!**\n\nاشترك في القنوات أدناه ثم اضغط على زر (تحقق من الاشتراك).",
        "sub_btn": "📢 اشترك في القناة: {ch}",
        "check_sub_btn": "🔄 تحقق من الاشتراك",
        "sub_success": "✅ شكراً لاشتراكك في جميع القنوات! يمكنك استخدام البوت الآن.",
        "sub_failed": "❌ لم تقم بالاشتراك في كافة القنوات المطلوبة بعد!",
        "choose_lang": "🌐 **الرجاء اختيار لغتك المفضلة / Please choose your preferred language:**",
        "lang_saved": "✅ تمت بنجاح! لغتك الحالية هي: **العربية**.\nأرسل /start للبدء.",
        "avatar_start": (
            "👤 **وضع صناعة الأفاتار مفعّل!**\n\n"
            "أرسل الآن من **4 إلى 10 صور** واضحة للوجه، وبعد الانتهاء اضغط على زر **بدء التدريب**."
        ),
        "avatar_btn_run": "✅ بدء التدريب ({count} صور)",
        "avatar_btn_cancel": "❌ إلغاء",
        "avatar_saved_img": "📥 تم حفظ الصورة رقم {count} للأفاتار.",
        "choose_mode": "⚙️ **اختر نوع المعالجة المطلوبة لهذه الصورة:**",
        "mode_enhance": "✨ تحسين الدقة (Enhance)",
        "mode_multitool": "🔥 تحسين شامل (Multitool)",
        "mode_colorize": "🎨 تلوين صورة قديمة (Colorize)",
        "mode_stylize": "🎨 تحويل كرتون (Stylize)",
        "mode_magicvideo": "🎬 فيديو سحري (Magic Video - 5د)",
        "mode_sticker": "😎 ملصق ذكي (AI Sticker)",
        "support_btn": "⭐ تبرع ودعم المطور ($5 أو نجوم)",
        "support_text": (
            "⭐ **لماذا ندعم البوت؟**\n\n"
            "التبرع بالنجوم (Telegram Stars) أو تحويل مبلغ 5$ للمطور يساعد بشكل مباشر في:\n"
            "• تقوية خوادم التشغيل وزيادة السرعة.\n"
            "• ضمان استمرارية البوت مجاناً للجميع بدون توقف.\n\n"
            "💳 **للتبرع والتواصل مع المطور:**\n"
            "معرف المطور: `@c2ccm`"
        ),
        "processing": "⏳ جاري ضغط الصورة ومعالجتها بوضع ({mode})... يرجى الانتظار.",
        "uploading": "📤 اكتملت المعالجة! جاري إرسال النتيجة...",
        "success_caption": "✅ تمت المعالجة بنجاح ({mode})",
        "error_msg": "❌ حدث خطأ أثناء المعالجة:\n{err}",
        "avatar_progress": "⏳ جاري تدريب الذكاء الاصطناعي على {count} صور...\nقد تستغرق العملية عدة دقائق، يرجى الانتظار.",
        "avatar_success": "👤 تم توليد الأفاتار بنجاح!",
        "avatar_failed": "❌ فشل إنشاء الأفاتار:\n{err}",
        "cancel_avatar": "✅ تم إلغاء وضع الأفاتار وحذف الصور المؤقتة.",
        "no_photo": "⚠️ لم يتم العثور على الصورة الأصلية، أرسلها مرة أخرى.",
        "need_more_photos": "⚠️ أرسل صورتين على الأقل أولاً!",
        "not_allowed": "⛔ هذا الأمر مخصص للمطور فقط.",
    },
    "en": {
        "welcome": (
            "👋 Welcome to Remini AI Smart Bot!\n\n"
            "📸 **How to use:**\n"
            "• Send any image directly here, and buttons will appear to choose the processing type:\n"
            "  1️⃣ **Enhance:** Upscale image resolution & clarify face/background.\n"
            "  2️⃣ **Multitool:** Comprehensive enhancement (Bokeh + lighting + HD).\n"
            "  3️⃣ **Colorize:** Colorize old B&W photos 🎨.\n"
            "  4️⃣ **Stylize:** Convert image to cartoon style.\n"
            "  5️⃣ **Magic Video:** Animate face into video (5 min wait).\n"
            "  6️⃣ **AI Sticker:** Create custom AI stickers from the face.\n\n"
            "⭐ **Support & Donate:**\n"
            "• Click the support button to help keep the bot running for everyone."
        ),
        "force_sub": "⚠️ **Sorry, you must subscribe to the bot's channels first to use it!**\n\nSubscribe below then click (Check Subscription).",
        "sub_btn": "📢 Subscribe: {ch}",
        "check_sub_btn": "🔄 Check Subscription",
        "sub_success": "✅ Thanks for subscribing to all channels! You can now use the bot.",
        "sub_failed": "❌ You haven't subscribed to all required channels yet!",
        "choose_lang": "🌐 **الرجاء اختيار لغتك المفضلة / Please choose your preferred language:**",
        "lang_saved": "✅ Success! Your current language is: **English**.\nSend /start to begin.",
        "avatar_start": (
            "👤 **Avatar creation mode activated!**\n\n"
            "Send now **4 to 10 clear face photos**, and when finished click **Start Training**."
        ),
        "avatar_btn_run": "✅ Start Training ({count} photos)",
        "avatar_btn_cancel": "❌ Cancel",
        "avatar_saved_img": "📥 Photo #{count} saved for avatar.",
        "choose_mode": "⚙️ **Choose the processing mode for this image:**",
        "mode_enhance": "✨ Enhance",
        "mode_multitool": "🔥 Multitool",
        "mode_colorize": "🎨 Colorize Old Photo",
        "mode_stylize": "🎨 Stylize (Toon)",
        "mode_magicvideo": "🎬 Magic Video (5m)",
        "mode_sticker": "😎 AI Sticker",
        "support_btn": "⭐ Support Developer ($5 or Stars)",
        "support_text": (
            "⭐ **Why support the bot?**\n\n"
            "Donating Telegram Stars or $5 helps directly with:\n"
            "• Upgrading servers and speeding up generation.\n"
            "• Keeping the bot free and running 24/7 for everyone.\n\n"
            "💳 **Developer Contact:**\n"
            "Developer: `@c2ccm`"
        ),
        "processing": "⏳ Compressing and processing image ({mode})... Please wait.",
        "uploading": "📤 Processing complete! Sending result...",
        "success_caption": "✅ Successfully processed ({mode})",
        "error_msg": "❌ An error occurred during processing:\n{err}",
        "avatar_progress": "⏳ Training AI model on {count} photos...\nThis may take a few minutes, please wait.",
        "avatar_success": "👤 Avatar generated successfully!",
        "avatar_failed": "❌ Failed to create avatar:\n{err}",
        "cancel_avatar": "✅ Avatar mode cancelled and temp files deleted.",
        "no_photo": "⚠️ Original image not found, please send it again.",
        "need_more_photos": "⚠️ Send at least 2 photos first!",
        "not_allowed": "⛔ This command is for the developer only.",
    },
}


def get_lang(user_id):
    return USER_LANGS.get(str(user_id), "ar")


def t(user_id, key, **kwargs):
    lang = get_lang(user_id)
    text_dict = TEXTS.get(lang, TEXTS["ar"])
    txt = text_dict.get(key, TEXTS["ar"].get(key, key))
    return txt.format(**kwargs)


# ==========================================
# إعدادات وخوادم Remini
# ==========================================
ORACLE = "https://api.remini.ai/v1/mobile/oracle"
API = "https://a.android.api.remini.ai/v1/mobile"
API2 = "https://a.android.api.remini.ai/v2/mobile"
UA = "okhttp/4.12.0"

DEVICES = [
    ("Samsung", "SM-G998B", "6.8", "33"),
    ("Google", "Pixel 7 Pro", "6.7", "33"),
    ("Xiaomi", "2201116SG", "6.67", "32"),
    ("OPPO", "CPH2211", "6.5", "31"),
    ("INFINIX", "Infinix X669", "6.6", "31"),
]

MIMES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}

ENHANCE_PIPELINE = {
    "type": "multi-tool",
    "pipelines": [
        {
            "color_enhance": {"model": "prism-blend"},
            "auto_balance": {"auto_contrast": {"contrast_intensity_coefficient": "1.2"}},
            "background_enhance": {"model": "shiba-strong-tensorrt", "remove_color_shift": "true"},
            "clip_extractor": {},
            "face_enhance": {"model": "recommender_entire_dataset", "pre_blur": "0.6"},
            "jpeg_quality": "90",
            "interpolation": "bicubic",
            "max_output_resolution": "3480",
            "enlarge_small_images_to": "2048",
            "smart_subject_selection": "true",
            "smart_subject_selection_factor": "1.5",
        }
    ],
}

MULTITOOL = {
    "type": "multi-tool",
    "pipelines": [
        {
            "bokeh": {
                "aperture_radius": "0.30",
                "apply_front_bokeh": "false",
                "group_picture": "true",
                "highlights": "0.25",
                "rescale_kernel_for_small_images": "true",
                "vivid": "0.75",
            },
            "color_enhance": {"model": "prism-blend"},
            "auto_balance": {"auto_contrast": {"contrast_intensity_coefficient": "1.5"}},
            "background_enhance": {"model": "shiba-strong-tensorrt", "remove_color_shift": "true"},
            "face_lifting": {"model": "pinko_bigger_dataset-style"},
            "dodge_burn": {"intensity": 0.5, "model": "dodge_burn_residuals_big"},
            "clip_extractor": {},
            "face_enhance": {"model": "recommender_entire_dataset", "pre_blur": "0.6"},
            "jpeg_quality": "85",
            "interpolation": "bicubic",
            "max_output_resolution": "3480",
            "enlarge_small_images_to": "2048",
            "smart_subject_selection": "true",
            "smart_subject_selection_factor": "1.5",
        }
    ],
}

DEFAULT_MAGIC_PRESET = "magic_video_wan_distill_lora_v2"
DEFAULT_AVATAR_PRESET = "female_caucasian_00174"

WORKDIR = "remini_temp"
os.makedirs(WORKDIR, exist_ok=True)


class Identity:
    def __init__(self, proxy=None):
        self.s = requests.Session()
        if proxy:
            self.s.proxies = {"http": proxy, "https": proxy}
        self.proxy = proxy
        self.token = None
        self.android_id = uuid.uuid4().hex[:16]
        self.aaid = str(uuid.uuid4())
        self.backend_id = str(uuid.uuid4())
        man, model, dtype, osv = random.choice(DEVICES)
        self.base = {
            "bsp-id": "com.bigwinepot.nwdn.international.android",
            "build-number": "202526404",
            "build-version": "3.7.1477",
            "country": "US",
            "device-manufacturer": man,
            "device-model": model,
            "device-type": dtype,
            "language": "en",
            "locale": "en_US",
            "os-version": osv,
            "platform": "Android",
            "timezone": "America/New_York",
            "android-id": self.android_id,
            "aaid": self.aaid,
            "user-agent": UA,
        }

    def headers(self, extra=None):
        h = dict(self.base)
        if self.token:
            h["identity-token"] = self.token
        if extra:
            h.update(extra)
        return h

    def auth(self):
        h = self.headers({
            "first-install-timestamp": str(int(time.time())) + "E9",
            "backup-persistent-id": self.android_id + "_com.bigwinepot.nwdn.international",
            "non-backup-persistent-id": self.backend_id,
            "environment": "Production",
            "settings-response-version": "v2",
            "is-app-running-in-background": "false",
            "is-old-user": "true",
            "app-set-id": str(uuid.uuid4()),
        })
        r = self.s.get(ORACLE + "/setup", headers=h, timeout=40)
        r.raise_for_status()
        self.token = r.json()["settings"]["__identity__"]["token"]
        self.s.get(API + "/users/@me", headers=self.headers(), timeout=40)
        return self


class Farm:
    def __init__(self, proxies=None):
        self.proxies = proxies or []
        self.lock = threading.Lock()
        self.count = 0

    def next_proxy(self):
        with self.lock:
            self.count += 1
            if not self.proxies:
                return None
            return self.proxies[self.count % len(self.proxies)]

    def identity(self):
        last_err = None
        for _ in range(3):
            try:
                return Identity(self.next_proxy()).auth()
            except Exception as e:
                last_err = e
                time.sleep(1)
        raise last_err


def load_proxies(path="proxies.txt"):
    if not path or not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    out = []
    for l in lines:
        if l.startswith("http"):
            out.append(l)
        else:
            parts = l.split(":")
            if len(parts) == 4:
                out.append(f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}")
            else:
                out.append("http://" + l)
    return out


def compress_image(path, max_size=1920):
    try:
        from PIL import Image
        with Image.open(path) as img:
            img = img.convert("RGB")
            w, h = img.size
            if max(w, h) > max_size:
                ratio = max_size / float(max(w, h))
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img.save(path, "JPEG", quality=85)
    except Exception:
        pass


def parse_dimensions_from_bytes(data):
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
            w, h = struct.unpack(">II", data[16:24])
            return int(w), int(h)
        if data[:2] == b"\xff\xd8":
            idx = 2
            size = len(data)
            while idx < size - 9:
                while idx < size and data[idx] != 0xFF:
                    idx += 1
                while idx < size and data[idx] == 0xFF:
                    idx += 1
                if idx >= size:
                    break
                marker = data[idx]
                idx += 1
                if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7):
                    continue
                if idx + 2 > size:
                    break
                seg_len = struct.unpack(">H", data[idx : idx + 2])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", data[idx + 3 : idx + 7])
                    return int(w), int(h)
                idx += seg_len
    except Exception:
        pass
    return 1024, 1024


def read_image(path):
    with open(path, "rb") as f:
        content = f.read()
    md5 = base64.b64encode(hashlib.md5(content).digest()).decode()
    mime = MIMES.get(os.path.splitext(path)[1].lower(), "image/jpeg")
    w = h = None
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
    except Exception:
        pass
    if not w or not h:
        w, h = parse_dimensions_from_bytes(content)
    return content, md5, mime, w, h


def gcs_put(url, headers, content):
    uh = {}
    for k, v in (headers or {}).items():
        uh[k] = v[0] if isinstance(v, list) and v else str(v)
    uh["Content-Length"] = str(len(content))
    uh["User-Agent"] = UA
    requests.put(url, headers=uh, data=content, timeout=180).raise_for_status()


def poll_v1(ident, task_id, max_wait=420):
    t0 = time.time()
    while time.time() - t0 < max_wait:
        time.sleep(4)
        r = ident.s.get(f"{API}/tasks/{task_id}", headers=ident.headers(), timeout=40)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        d = r.json()
        st = d.get("status")
        if st == "completed":
            res = d.get("result") or {}
            outs = res.get("outputs") or d.get("outputs") or []
            if outs and isinstance(outs, list):
                first = outs[0]
                if isinstance(first, dict):
                    url = first.get("url") or first.get("uri")
                    if url:
                        return url
            if res.get("output_url"):
                return res["output_url"]
            raise RuntimeError("completed without outputs")
        if st in ("failed", "error"):
            raise RuntimeError("task failed: " + json.dumps(d)[:200])
    raise TimeoutError("poll timeout")


def poll_v2(ident, task_id, max_wait=600):
    t0 = time.time()
    while time.time() - t0 < max_wait:
        time.sleep(6)
        r = ident.s.get(f"{API2}/multi-avatar/tasks/{task_id}", headers=ident.headers(), timeout=40)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        d = r.json()
        st = d.get("status")
        if st == "completed":
            res = d.get("results") or []
            if res:
                return res[0].get("uri") or res[0].get("url")
            raise RuntimeError("completed without results")
        if st in ("failed", "error"):
            raise RuntimeError("task failed: " + json.dumps(d)[:200])
    raise TimeoutError("poll timeout")


def download(url, out_path):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=300)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)
    return len(r.content)


def _run_enhance_pipeline(farm, image, out, pipeline_feature):
    ident = farm.identity()
    content, md5, mime, w, h = read_image(image)
    body = {
        "image_content_type": mime,
        "image_md5": md5,
        "image_size": len(content),
        "image_resolution_width": int(w or 1024),
        "image_resolution_height": int(h or 1024),
        "feature": pipeline_feature,
    }
    r = ident.s.post(
        API + "/tasks",
        headers=ident.headers({"content-type": "application/json; charset=UTF-8"}),
        json=body,
        timeout=40,
    )
    r.raise_for_status()
    d = r.json()
    gcs_put(d["upload_url"], d.get("upload_headers", {}), content)
    ident.s.post(
        f"{API}/tasks/{d['task_id']}/process",
        headers=ident.headers({"content-length": "0"}),
        timeout=40,
    ).raise_for_status()
    url = poll_v1(ident, d["task_id"])
    size = download(url, out)
    return out, size


def enhance(farm, image, out, multitool=False):
    primary_feature = MULTITOOL if multitool else ENHANCE_PIPELINE
    try:
        return _run_enhance_pipeline(farm, image, out, primary_feature)
    except Exception:
        return _run_enhance_pipeline(farm, image, out, MULTITOOL)


# دالة تلوين الصور القديمة (Colorize)
def colorize(farm, image, out):
    ident = farm.identity()
    content, md5, mime, w, h = read_image(image)
    feature = {"type": "colorize"}
    body = {
        "image_content_type": mime,
        "image_md5": md5,
        "image_size": len(content),
        "image_resolution_width": int(w or 1024),
        "image_resolution_height": int(h or 1024),
        "feature": feature,
    }
    r = ident.s.post(
        API + "/tasks",
        headers=ident.headers({"content-type": "application/json; charset=UTF-8"}),
        json=body,
        timeout=40,
    )
    r.raise_for_status()
    d = r.json()
    gcs_put(d["upload_url"], d.get("upload_headers", {}), content)
    ident.s.post(
        f"{API}/tasks/{d['task_id']}/process",
        headers=ident.headers({"content-length": "0"}),
        timeout=40,
    ).raise_for_status()
    url = poll_v1(ident, d["task_id"])
    size = download(url, out)
    return out, size


def magic_video(farm, face_image, out, preset=DEFAULT_MAGIC_PRESET):
    ident = farm.identity()
    content, md5, mime, w, h = read_image(face_image)
    h2 = ident.headers({"content-type": "application/json; charset=UTF-8"})
    r = ident.s.post(
        API2 + "/multi-avatar/multi-images/models",
        headers=h2,
        json={"subjects": [{"images": [{"content_type": mime, "md5": md5}]}]},
        timeout=40,
    )
    r.raise_for_status()
    subj = r.json()["subjects"][0]
    gcs_put(subj["images"][0]["upload_uri"], subj["images"][0]["upload_headers"], content)
    body = {
        "subjects": [{"photo_model_id": subj["photo_model_id"]}],
        "preset_ids": [preset],
        "n_output_images": 1,
        "ai_generation_config": {
            "free": {"generation": {"config": {"job_type": "multiavatar"}, "handler_type": "multiavatar"}},
            "premium": {"generation": {"config": {"job_type": "multiavatar"}, "handler_type": "multiavatar"}},
        },
        "input_people": 1,
    }
    r = ident.s.post(API2 + "/multi-avatar/tasks", headers=h2, json=body, timeout=40)
    r.raise_for_status()
    tid = r.json()["photo_task_id"]
    url = poll_v2(ident, tid)
    size = download(url, out)
    return out, size


def stylize(farm, image, out, style="toon"):
    ident = farm.identity()
    content, md5, mime, w, h = read_image(image)
    body = {
        "image_content_type": mime,
        "image_md5": md5,
        "image_size": len(content),
        "image_resolution_width": int(w or 1024),
        "image_resolution_height": int(h or 1024),
        "feature": {"type": "stylization-v2", "id": style},
    }
    r = ident.s.post(API + "/tasks", headers=ident.headers({"content-type": "application/json; charset=UTF-8"}), json=body, timeout=40)
    r.raise_for_status()
    d = r.json()
    gcs_put(d["upload_url"], d.get("upload_headers", {}), content)
    ident.s.post(f"{API}/tasks/{d['task_id']}/process", headers=ident.headers({"content-length": "0"}), timeout=40).raise_for_status()
    url = poll_v1(ident, d["task_id"])
    size = download(url, out)
    return out, size


def ai_sticker(farm, image, out, preset="ai_sticker_geemoji"):
    ident = farm.identity()
    content, md5, mime, w, h = read_image(image)
    H = ident.headers({"content-type": "application/json; charset=UTF-8"})
    r = ident.s.post(
        API2 + "/ai-sticker/input-photos",
        headers=H,
        json={"input_photos": [{"content_type": mime, "md5": md5}]},
        timeout=40,
    )
    r.raise_for_status()
    d = r.json()
    up = d["input_photos"][0]
    gcs_put(up["upload_uri"], up["upload_headers"], content)
    r = ident.s.post(
        API2 + "/ai-sticker/tasks",
        headers=H,
        json={"input_photo_group_id": d["input_photo_group_id"], "preset_ids": [preset]},
        timeout=40,
    )
    r.raise_for_status()
    tid = r.json()["task_id"]
    t0 = time.time()
    while time.time() - t0 < 1800:
        time.sleep(10)
        resp = ident.s.get(f"{API2}/ai-sticker/tasks/{tid}", headers=ident.headers(), timeout=40)
        if resp.status_code == 404:
            continue
        resp.raise_for_status()
        p = resp.json()
        st = p.get("status")
        if st == "completed":
            res = p.get("results") or []
            if not res:
                raise RuntimeError("completed without results")
            size = download(res[0].get("uri") or res[0].get("url"), out)
            return out, size
        if st in ("failed", "error"):
            raise RuntimeError("task failed: " + json.dumps(p)[:200])
    raise TimeoutError("sticker poll timeout")


def avatar(farm, image_paths, out, preset=DEFAULT_AVATAR_PRESET):
    ident = farm.identity()
    H = ident.headers({"content-type": "application/json; charset=UTF-8"})
    imgs = []
    datas = []
    for p in image_paths:
        content, md5, mime, w, h = read_image(p)
        imgs.append({"content_type": mime, "md5": md5})
        datas.append(content)
    r = ident.s.post(API2 + "/photo-tasks/models", headers=H, json={"images": imgs}, timeout=40)
    r.raise_for_status()
    d = r.json()
    mid = d["photo_model_id"]
    for up, content in zip(d["images"], datas):
        gcs_put(up["upload_uri"], up["upload_headers"], content)
    t0 = time.time()
    while time.time() - t0 < 3600:
        time.sleep(20)
        resp = ident.s.get(f"{API2}/photo-tasks/models/{mid}", headers=ident.headers(), timeout=40)
        if resp.status_code == 404:
            continue
        resp.raise_for_status()
        m = resp.json()
        st = m.get("status")
        if st in ("ready", "completed", "trained"):
            break
        if st in ("failed", "error"):
            raise RuntimeError("model failed: " + json.dumps(m)[:200])
    else:
        raise TimeoutError("model training timeout")
    gen = {"generation": {"config": {"job_type": "multiavatar"}, "handler_type": "multiavatar"}}
    r = ident.s.post(
        API2 + "/photo-tasks/pack-photo",
        headers=H,
        json={"ai_generation_config": {"free": gen, "premium": gen}, "presets": [{"preset_id": preset, "photo_model_id": mid}]},
        timeout=40,
    )
    r.raise_for_status()
    tid = r.json().get("photo_task_id") or r.json().get("task_id")
    t0 = time.time()
    while time.time() - t0 < 1800:
        time.sleep(10)
        resp = ident.s.get(f"{API2}/photo-tasks/preset-photo/{tid}", headers=ident.headers(), timeout=40)
        if resp.status_code == 404:
            continue
        resp.raise_for_status()
        g = resp.json()
        st = g.get("status")
        if st == "completed":
            res = g.get("results") or []
            if not res:
                raise RuntimeError("completed without results")
            size = download(res[0].get("uri") or res[0].get("url"), out)
            return out, size
        if st in ("failed", "error"):
            raise RuntimeError("task failed: " + json.dumps(g)[:200])
    raise TimeoutError("avatar poll timeout")


# ==========================================
# الفحص والدعم والتحكم
# ==========================================
def check_sub(user_id):
    if not REQUIRED_CHANNELS:
        return True
    for ch in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True


def sub_keyboard(user_id):
    markup = InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        link = f"https://t.me/{ch.replace('@', '')}"
        markup.add(InlineKeyboardButton(t(user_id, "sub_btn", ch=ch), url=link))
    markup.add(InlineKeyboardButton(t(user_id, "check_sub_btn"), callback_data="check_sub"))
    return markup


def lang_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("العربية 🇸🇦", callback_data="set_lang:ar"),
        InlineKeyboardButton("English 🇺🇸", callback_data="set_lang:en"),
    )
    return markup


def mode_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(t(user_id, "mode_enhance"), callback_data="mode:enhance"),
        InlineKeyboardButton(t(user_id, "mode_multitool"), callback_data="mode:multitool"),
        InlineKeyboardButton(t(user_id, "mode_colorize"), callback_data="mode:colorize"),
        InlineKeyboardButton(t(user_id, "mode_stylize"), callback_data="mode:stylize"),
        InlineKeyboardButton(t(user_id, "mode_magicvideo"), callback_data="mode:magicvideo"),
        InlineKeyboardButton(t(user_id, "mode_sticker"), callback_data="mode:sticker"),
        InlineKeyboardButton(t(user_id, "support_btn"), callback_data="support_dev"),
    )
    return markup


# ==========================================
# إعداد بوت التليجرام والأوامر
# ==========================================
bot = telebot.TeleBot(BOT_TOKEN)
farm = Farm(load_proxies())
avatar_sessions = {}


def is_allowed(user_id):
    if PRIVATE_MODE and user_id != ADMIN_ID:
        return False
    return True


@bot.message_handler(commands=["start", "language"])
def cmd_start(message):
    uid = message.from_user.id
    if not is_allowed(uid):
        bot.reply_to(message, "⛔ This bot is private.")
        return

    register_user(uid)

    if message.text.startswith("/language") or str(uid) not in USER_LANGS:
        bot.reply_to(
            message,
            "🌐 **الرجاء اختيار لغتك المفضلة / Please choose your preferred language:**",
            reply_markup=lang_keyboard(),
            parse_mode="Markdown",
        )
        return

    if not check_sub(uid):
        bot.reply_to(message, t(uid, "force_sub"), reply_markup=sub_keyboard(uid), parse_mode="Markdown")
        return

    bot.reply_to(message, t(uid, "welcome"), parse_mode="Markdown")


@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    uid = message.from_user.id
    if uid != ADMIN_ID:
        bot.reply_to(message, t(uid, "not_allowed"))
        return

    total_users = len(USERS_LIST)
    total_msgs = BOT_SETTINGS.get("total_messages", 0)
    channels_list = "\n".join([f"• `{ch}`" for ch in REQUIRED_CHANNELS]) if REQUIRED_CHANNELS else "لا توجد قنوات حالياً"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ إضافة قناة", callback_data="admin:add_ch"),
        InlineKeyboardButton("➖ حذف قناة", callback_data="admin:del_ch"),
        InlineKeyboardButton("⏱ تعديل وقت الانتظار", callback_data="admin:set_cooldown"),
        InlineKeyboardButton("📢 إذاعة عامة", callback_data="admin:broadcast"),
    )

    text = (
        "🛠 **لوحة تحكم المطور المتقدمة:**\n\n"
        f"👥 إجمالي المستخدمين: `{total_users}`\n"
        f"📨 إجمالي الرسائل والمعالجات: `{total_msgs}`\n"
        f"⏱ وقت الانتظار الحالي (عادي): `{int(BOT_SETTINGS.get('normal_cooldown', 60)/60)} دقيقة`\n"
        f"⏱ وقت الانتظار الحالي (فيديو): `{int(BOT_SETTINGS.get('video_cooldown', 300)/60)} دقيقة`\n\n"
        f"📢 **قنوات الاشتراك الإجباري:**\n{channels_list}"
    )
    bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")


@bot.message_handler(commands=["avatar"])
def cmd_avatar(message):
    uid = message.from_user.id
    if not is_allowed(uid):
        return
    if not check_sub(uid):
        bot.reply_to(message, t(uid, "force_sub"), reply_markup=sub_keyboard(uid), parse_mode="Markdown")
        return

    avatar_sessions[uid] = []
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(t(uid, "avatar_btn_cancel"), callback_data="avatar:cancel"))
    bot.reply_to(message, t(uid, "avatar_start"), reply_markup=markup, parse_mode="Markdown")


@bot.message_handler(content_types=["text"])
def handle_admin_text(message):
    uid = message.from_user.id
    if uid == ADMIN_ID and uid in admin_states:
        state = admin_states[uid]
        text = message.text.strip()

        if state == "waiting_add_ch":
            if not text.startswith("@"):
                bot.reply_to(message, "⚠️ يرجى إدخال معرف القناة بـ @ (مثال: @Channel)")
                return
            if text not in REQUIRED_CHANNELS:
                REQUIRED_CHANNELS.append(text)
                save_json(CHANNELS_FILE, REQUIRED_CHANNELS)
                bot.reply_to(message, f"✅ تم إضافة القناة `{text}` بنجاح.", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ القناة مضافة مسبقاً.")
            admin_states.pop(uid, None)
            return

        elif state == "waiting_del_ch":
            if text in REQUIRED_CHANNELS:
                REQUIRED_CHANNELS.remove(text)
                save_json(CHANNELS_FILE, REQUIRED_CHANNELS)
                bot.reply_to(message, f"✅ تم حذف القناة `{text}` بنجاح.", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ القناة غير موجودة.")
            admin_states.pop(uid, None)
            return

        elif state == "waiting_cooldown":
            try:
                mins = int(text)
                BOT_SETTINGS["normal_cooldown"] = mins * 60
                BOT_SETTINGS["video_cooldown"] = mins * 60 * 5
                save_json(SETTINGS_FILE, BOT_SETTINGS)
                bot.reply_to(message, f"✅ تم تحديث وقت الانتظار إلى **{mins} دقائق** بنجاح.", parse_mode="Markdown")
            except ValueError:
                bot.reply_to(message, "⚠️ يرجى إدخال رقم صحيح بالدقائق (مثال: 1 أو 2).")
            admin_states.pop(uid, None)
            return

        elif state == "waiting_broadcast":
            admin_states.pop(uid, None)
            bot.reply_to(message, "🚀 جاري بدء الإذاعة لجميع المستخدمين...")
            threading.Thread(target=run_broadcast, args=(message,), daemon=True).start()
            return


def run_broadcast(message):
    success = 0
    failed = 0
    for uid_str in list(USERS_LIST.keys()):
        try:
            bot.copy_message(chat_id=int(uid_str), from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
            time.sleep(0.05)
        except Exception:
            failed += 1
    bot.send_message(ADMIN_ID, f"📢 **تمت الإذاعة بنجاح!**\n\n✅ وصل إلى: `{success}` مستخدم\n❌ فشل لدى: `{failed}` مستخدم", parse_mode="Markdown")


@bot.message_handler(content_types=["photo", "document"])
def handle_photo(message):
    uid = message.from_user.id
    if not is_allowed(uid):
        return

    register_user(uid)

    if not check_sub(uid):
        bot.reply_to(message, t(uid, "force_sub"), reply_markup=sub_keyboard(uid), parse_mode="Markdown")
        return

    file_id = None
    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
    elif message.content_type == "document":
        mime = (message.document.mime_type or "").lower()
        if not mime.startswith("image/"):
            return
        file_id = message.document.file_id

    if not file_id:
        return

    if uid in avatar_sessions:
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = os.path.join(WORKDIR, f"av_{uid}_{uuid.uuid4().hex[:8]}.jpg")
        with open(img_path, "wb") as f:
            f.write(downloaded)
        compress_image(img_path)
        avatar_sessions[uid].append(img_path)
        count = len(avatar_sessions[uid])

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(t(uid, "avatar_btn_run", count=count), callback_data="avatar:run"),
            InlineKeyboardButton(t(uid, "avatar_btn_cancel"), callback_data="avatar:cancel"),
        )
        bot.reply_to(message, t(uid, "avatar_saved_img", count=count), reply_markup=markup)
        return

    bot.reply_to(message, t(uid, "choose_mode"), reply_markup=mode_keyboard(uid), parse_mode="Markdown")


def extract_reply_file_id(reply_msg):
    if not reply_msg:
        return None
    if reply_msg.photo:
        return reply_msg.photo[-1].file_id
    if reply_msg.document and (reply_msg.document.mime_type or "").lower().startswith("image/"):
        return reply_msg.document.file_id
    return None


def process_single_task(call, mode):
    chat_id = call.message.chat.id
    uid = call.from_user.id
    lang = get_lang(uid)

    now = time.time()
    cooldown_limit = BOT_SETTINGS.get("video_cooldown", 300) if mode == "magicvideo" else BOT_SETTINGS.get("normal_cooldown", 60)
    last_time = LAST_USED_VIDEO.get(uid, 0) if mode == "magicvideo" else LAST_USED_NORMAL.get(uid, 0)

    if uid != ADMIN_ID and (now - last_time) < cooldown_limit:
        remaining = int((cooldown_limit - (now - last_time)) / 60) or 1
        msg_template = BOT_SETTINGS.get("msg_ar" if lang == "ar" else "msg_en", "⚠️ Wait {mins} mins.")
        msg = msg_template.format(mins=remaining)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        return

    if mode == "magicvideo":
        LAST_USED_VIDEO[uid] = now
    else:
        LAST_USED_NORMAL[uid] = now

    reply_msg = call.message.reply_to_message
    file_id = extract_reply_file_id(reply_msg)

    if not file_id:
        bot.edit_message_text(t(uid, "no_photo"), chat_id, call.message.message_id)
        return

    src_path = os.path.join(WORKDIR, f"in_{uuid.uuid4().hex[:10]}.jpg")
    out_path = ""

    try:
        bot.edit_message_text(t(uid, "processing", mode=mode), chat_id, call.message.message_id)
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        with open(src_path, "wb") as f:
            f.write(downloaded)

        compress_image(src_path)

        uid_tag = uuid.uuid4().hex[:10]
        if mode == "enhance":
            out_path = os.path.join(WORKDIR, f"out_{uid_tag}_hd.jpg")
            enhance(farm, src_path, out_path, multitool=False)
        elif mode == "multitool":
            out_path = os.path.join(WORKDIR, f"out_{uid_tag}_multi.jpg")
            enhance(farm, src_path, out_path, multitool=True)
        elif mode == "colorize":
            out_path = os.path.join(WORKDIR, f"out_{uid_tag}_color.jpg")
            colorize(farm, src_path, out_path)
        elif mode == "stylize":
            out_path = os.path.join(WORKDIR, f"out_{uid_tag}_toon.jpg")
            stylize(farm, src_path, out_path, style="toon")
        elif mode == "sticker":
            out_path = os.path.join(WORKDIR, f"out_{uid_tag}_sticker.png")
            ai_sticker(farm, src_path, out_path)
        elif mode == "magicvideo":
            out_path = os.path.join(WORKDIR, f"out_{uid_tag}_magic.mp4")
            magic_video(farm, src_path, out_path)

        BOT_SETTINGS["total_messages"] = BOT_SETTINGS.get("total_messages", 0) + 1
        save_json(SETTINGS_FILE, BOT_SETTINGS)

        bot.edit_message_text(t(uid, "uploading"), chat_id, call.message.message_id)

        if mode == "magicvideo":
            with open(out_path, "rb") as result_file:
                bot.send_video(chat_id, result_file, caption="🎬 Remini Video AI", reply_to_message_id=reply_msg.message_id)
        elif mode == "sticker":
            with open(out_path, "rb") as result_file:
                bot.send_document(chat_id, result_file, caption="😎 Remini Sticker AI", reply_to_message_id=reply_msg.message_id)
        else:
            try:
                with open(out_path, "rb") as result_file:
                    bot.send_photo(chat_id, result_file, caption=t(uid, "success_caption", mode=mode), reply_to_message_id=reply_msg.message_id)
            except Exception:
                with open(out_path, "rb") as result_file:
                    bot.send_document(chat_id, result_file, caption=t(uid, "success_caption", mode=mode), reply_to_message_id=reply_msg.message_id)

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass

    except Exception as e:
        try:
            bot.edit_message_text(t(uid, "error_msg", err=str(e)[:200]), chat_id, call.message.message_id)
        except Exception:
            pass
    finally:
        for p in (src_path, out_path):
            if p and os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


def process_avatar_task(call, uid, photos):
    chat_id = call.message.chat.id
    out_path = os.path.join(WORKDIR, f"avatar_{uid}_{uuid.uuid4().hex[:8]}.jpg")
    try:
        bot.edit_message_text(t(uid, "avatar_progress", count=len(photos)), chat_id, call.message.message_id)
        avatar(farm, photos, out_path, DEFAULT_AVATAR_PRESET)
        with open(out_path, "rb") as f:
            bot.send_photo(chat_id, f, caption=t(uid, "avatar_success"))
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass
    except Exception as e:
        try:
            bot.edit_message_text(t(uid, "avatar_failed", err=str(e)[:200]), chat_id, call.message.message_id)
        except Exception:
            pass
    finally:
        for p in photos + [out_path]:
            if p and os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    if not is_allowed(uid):
        bot.answer_callback_query(call.id, "⛔ Not allowed.")
        return

    data = call.data

    if data == "support_dev":
        bot.answer_callback_query(call.id, "⭐ شكراً لاهتمامك بدعم استمرارية البوت!")
        bot.send_message(call.message.chat.id, t(uid, "support_text"), parse_mode="Markdown")
        return

    if data == "admin:add_ch":
        if uid != ADMIN_ID:
            return
        admin_states[uid] = "waiting_add_ch"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "✍️ أرسل معرف القناة (مثال: `@ChannelName`):")
        return

    if data == "admin:del_ch":
        if uid != ADMIN_ID:
            return
        admin_states[uid] = "waiting_del_ch"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "✍️ أرسل معرف القناة المراد حذفها:")
        return

    if data == "admin:set_cooldown":
        if uid != ADMIN_ID:
            return
        admin_states[uid] = "waiting_cooldown"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "⏱ أرسل وقت الانتظار الجديد **بالدقائق** فقط (مثال: `1` أو `2`):", parse_mode="Markdown")
        return

    if data == "admin:broadcast":
        if uid != ADMIN_ID:
            return
        admin_states[uid] = "waiting_broadcast"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📢 قم بإرسال الرسالة (نص، صورة، أو فيديو) التي تريد إذاعتها لجميع المستخدمين:")
        return

    if data.startswith("set_lang:"):
        lang = data.split(":", 1)[1]
        USER_LANGS[str(uid)] = lang
        save_json(LANG_FILE, USER_LANGS)
        bot.answer_callback_query(call.id, "Language saved!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.send_message(call.message.chat.id, t(uid, "lang_saved"), parse_mode="Markdown")
        return

    if data == "check_sub":
        if check_sub(uid):
            bot.answer_callback_query(call.id, t(uid, "sub_success"), show_alert=True)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(call.message.chat.id, t(uid, "welcome"), parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, t(uid, "sub_failed"), show_alert=True)
        return

    if not check_sub(uid):
        bot.answer_callback_query(call.id, "⚠️ Subscribe first!", show_alert=True)
        return

    if data.startswith("mode:"):
        mode = data.split(":", 1)[1]
        bot.answer_callback_query(call.id, f"Starting {mode}...")
        threading.Thread(target=process_single_task, args=(call, mode), daemon=True).start()

    elif data == "avatar:cancel":
        photos = avatar_sessions.pop(uid, [])
        for p in photos:
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        bot.edit_message_text(t(uid, "cancel_avatar"), call.message.chat.id, call.message.message_id)

    elif data == "avatar:run":
        photos = avatar_sessions.pop(uid, [])
        if len(photos) < 2:
            bot.answer_callback_query(call.id, t(uid, "need_more_photos"), show_alert=True)
            avatar_sessions[uid] = photos
            return
        bot.answer_callback_query(call.id, "Avatar training started...")
        threading.Thread(target=process_avatar_task, args=(call, uid, photos), daemon=True).start()


if __name__ == "__main__":
    print("=" * 55)
    print("  Remini Telegram Bot (Colorize + All Features) is Running...")
    print(f"  Admin ID: {ADMIN_ID}")
    print("=" * 55)
    try:
        bot.send_message(ADMIN_ID, "✅ Remini Bot is running with Colorize feature and all updates!")
    except Exception:
        pass
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
