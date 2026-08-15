import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import random
import os
from datetime import datetime, timedelta
import hashlib


DB_FILE = "church_app.db"
IMAGES_DIR = "member_images"
os.makedirs(IMAGES_DIR, exist_ok=True)


THEMES = {
    "Dark": {
        "BG_COLOR": "#0B0F19",
        "CARD_BG": "#151B2B",
        "CARD_BG_ALT": "#1A2133",
        "CARD_BORDER": "#232D45",
        "SIDEBAR_BG": "#0D1321",
        "INPUT_BG": "#0F1525",
        "TEXT_PRIMARY": "#F8FAFC",
        "TEXT_SECONDARY": "#94A3B8",
        "TEXT_MUTED": "#64748B",
        "HEADER_BG": "#1E3A5F",
        "PRIMARY": "#6366F1",
        "PRIMARY_HOVER": "#818CF8",
        "PRIMARY_GLOW": "#4338CA",
        "ACCENT": "#10B981",
        "ACCENT_HOVER": "#34D399",
        "WARNING": "#F59E0B",
        "DANGER": "#EF4444",
        "DANGER_HOVER": "#F87171",
        "PURPLE": "#A855F7",
        "PRESENT_COLOR": "#10B981",
        "ABSENT_COLOR": "#EF4444",
        "PRESENT_BG": "#0F291E",
        "ABSENT_BG": "#291515",
        "GRADIENT_TOP": "#6366F1",
        "GRADIENT_BOTTOM": "#8B5CF6",
    },
    "Light": {
        "BG_COLOR": "#F1F5F9",
        "CARD_BG": "#FFFFFF",
        "CARD_BG_ALT": "#F8FAFC",
        "CARD_BORDER": "#E2E8F0",
        "SIDEBAR_BG": "#FFFFFF",
        "INPUT_BG": "#F8FAFC",
        "TEXT_PRIMARY": "#0F172A",
        "TEXT_SECONDARY": "#64748B",
        "TEXT_MUTED": "#94A3B8",
        "HEADER_BG": "#3B82F6",
        "PRIMARY": "#4F46E5",
        "PRIMARY_HOVER": "#6366F1",
        "PRIMARY_GLOW": "#C7D2FE",
        "ACCENT": "#059669",
        "ACCENT_HOVER": "#10B981",
        "WARNING": "#D97706",
        "DANGER": "#DC2626",
        "DANGER_HOVER": "#EF4444",
        "PURPLE": "#7C3AED",
        "PRESENT_COLOR": "#059669",
        "ABSENT_COLOR": "#DC2626",
        "PRESENT_BG": "#DCFCE7",
        "ABSENT_BG": "#FEE2E2",
        "GRADIENT_TOP": "#4F46E5",
        "GRADIENT_BOTTOM": "#7C3AED",
    }
}

# ============================================
# Database
# ============================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            school_age TEXT,
            family_name TEXT,
            confessor TEXT,
            address TEXT,
            phone TEXT,
            notes TEXT,
            birth_date TEXT,
            photo_path TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    c.execute("PRAGMA table_info(members)")
    columns = [col[1] for col in c.fetchall()]
    if 'user_id' not in columns:
        c.execute("ALTER TABLE members ADD COLUMN user_id INTEGER REFERENCES users(id)")
    if 'confessor' not in columns:
        c.execute("ALTER TABLE members ADD COLUMN confessor TEXT")

    c.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place TEXT NOT NULL,
            visit_date TEXT NOT NULL,
            phone TEXT,
            visit_type TEXT,
            member_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY(member_id) REFERENCES members(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    c.execute("PRAGMA table_info(visits)")
    columns_visits = [col[1] for col in c.fetchall()]
    if 'user_id' not in columns_visits:
        c.execute("ALTER TABLE visits ADD COLUMN user_id INTEGER REFERENCES users(id)")

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            user_id INTEGER,
            FOREIGN KEY(member_id) REFERENCES members(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    c.execute("PRAGMA table_info(attendance)")
    columns_att = [col[1] for col in c.fetchall()]
    if 'user_id' not in columns_att:
        c.execute("ALTER TABLE attendance ADD COLUMN user_id INTEGER REFERENCES users(id)")

    conn.commit()
    conn.close()


BIBLE_VERSES = [
    "لأَنَّهُ هكَذَا أَحَبَّ اللهُ الْعَالَمَ حَتَّى بَذَلَ ابْنَهُ الْوَحِيدَ، لِكَيْ لاَ يَهْلِكَ كُلُّ مَنْ يُؤْمِنُ بِهِ، بَلْ تَكُونُ لَهُ الْحَيَاةُ الأَبَدِيَّةُ. — يوحنا ٣:١٦",
    "أَنَا هُوَ الطَّرِيقُ وَالْحَقُّ وَالْحَيَاةُ. لَيْسَ أَحَدٌ يَأْتِي إِلَى الآبِ إِلاَّ بِي. — يوحنا ١٤:٦",
    "تَعَالَوْا إِلَيَّ يَا جَمِيعَ الْمُتْعَبِينَ وَالثَّقِيلِي الأَحْمَالِ، وَأَنَا أُرِيحُكُمْ. — متى ١١:٢٨",
    "كُلُّ مَنْ يَسْأَلُ يَأْخُذُ، وَمَنْ يَطْلُبُ يَجِدُ، وَمَنْ يَقْرَعُ يُفْتَحُ لَهُ. — متى ٧:٨",
    "اَلرَّبُّ نُورِي وَخَلاَصِي، مِمَّنْ أَخَافُ؟ — مزمور ٢٧:١",
    "اَللهُ مَلْجَأُنَا وَقُوَّتُنَا، عَوْنًا فِي الضِّيقَاتِ وُجِدَ شَدِيدًا. — مزمور ٤٦:١",
    "اِفْرَحُوا فِي الرَّبِّ كُلَّ حِينٍ، وَأَقُولُ أَيْضًا: افْرَحُوا! — فيلبي ٤:٤",
    "وَأَمَّا ثَمَرُ الرُّوحِ فَهُوَ: مَحَبَّةٌ، فَرَحٌ، سَلاَمٌ، طُولُ أَنَاةٍ، لُطْفٌ، صَلاَحٌ، إِيمَانٌ، وَدَاعَةٌ، تَعَفُّفٌ. — غلاطية ٥:٢٢-٢٣",
    "كُلُّ شَيْءٍ يَسْتَطِيعُ فِي الَّذِي يُقَوِّينِي. — فيلبي ٤:١٣",
    "وَأَمَّا مُنْتَهَى الأَمْرِ فَلْيَسْمَعُ الْجَمِيعُ: أَحِبُّوا الرَّبَّ إِلَهَكُمْ مِنْ كُلِّ قَلْبِكُمْ، وَمِنْ كُلِّ نَفْسِكُمْ، وَمِنْ كُلِّ فِكْرِكُمْ. — متى ٢٢:٣٧",
    "اَلْمَحَبَّةُ تَتَأَنَّى وَتَرْفُقُ. اَلْمَحَبَّةُ لاَ تَحْسِدُ. اَلْمَحَبَّةُ لاَ تَتَفَاخَرُ وَلاَ تَنْتَفِخُ. — ١ كورنثوس ١٣:٤",
    "لأَنَّنَا بِالإِيمَانِ نَسْلُكُ لاَ بِالرُّؤْيَا. — ٢ كورنثوس ٥:٧",
    "وَأَمَّا مَنْ يَصْبِرُ إِلَى الْمُنْتَهَى فَهذَا يَخْلُصُ. — متى ٢٤:١٣",
    "لأَنَّهُ مَكْتُوبٌ: كُونُوا قِدِّيسِينَ لأَنِّي أَنَا قُدُّوسٌ. — ١ بطرس ١:١٦",
    "وَأَمَّا مَنْ يَثِقُ بِالرَّبِّ فَيُحَاطُ بِرَحْمَتِهِ. — أمثال ٢٨:٢٥",
    "اَلرَّبُّ صَخْرَتِي وَحِصْنِي وَمُنْقِذِي. إِلَهِي صَخْرَتِي بِهِ أَحْتَمِي. — مزمور ١٨:٢",
    "اَلْمَحَبَّةُ لاَ تَسْقُطُ أَبَدًا. — ١ كورنثوس ١٣:٨",
    "اِحْمَدُوا الرَّبَّ لأَنَّهُ صَالِحٌ، لأَنَّ إِلَى الأَبَدِ رَحْمَتَهُ. — مزمور ١٣٦:١",
    "اَلرَّبُّ رَاعِيَّ فَلاَ يُعْوِزُنِي شَيْءٌ. — مزمور ٢٣:١",
    "وَأَمَّا مُنْتَهَى الأَمْرِ فَلْيَسْمَعُ الْجَمِيعُ: أَحِبُّوا قَرِيبَكُمْ كَنَفْسِكُمْ. — متى ٢٢:٣٩",
    "اَلرَّبُّ نُورِي وَخَلاَصِي، فَمِمَّنْ أَخَافُ؟ — مزمور ٢٧:١",
    "اِفْرَحُوا فِي الرَّبِّ كُلَّ حِينٍ، وَأَقُولُ أَيْضًا: افْرَحُوا! — فيلبي ٤:٤",
    "لأَنَّهُ مَكْتُوبٌ: كُونُوا أَنْتُمْ قِدِّيسِينَ كَمَا أَنَا قُدُّوسٌ. — ١ بطرس ١:١٦",
    "وَأَمَّا مَنْ يَثِقُ بِالرَّبِّ فَيُحَاطُ بِرَحْمَتِهِ. — أمثال ٢٨:٢٥",
    "اَلرَّبُّ صَخْرَتِي وَحِصْنِي وَمُنْقِذِي. — مزمور ١٨:٢",
]

def get_random_verse():
    return random.choice(BIBLE_VERSES)


SCHOOL_AGES = [
    "حضانة",
    "أولى ابتدائي", "ثانية ابتدائي", "ثالثة ابتدائي", "رابعة ابتدائي",
    "خامسة ابتدائي", "سادسة ابتدائي",
    "أولى إعدادي", "ثانية إعدادي", "ثالثة إعدادي",
    "أولى ثانوي", "ثانية ثانوي", "ثالثة ثانوي",
    "جامعة",
    "خريج",
]


class ChurchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("✝ نظام إدارة المخدومين")
        self.geometry("1350x900")
        self.minsize(1000, 700)

        self.current_theme = "Dark"
        self.apply_theme(self.current_theme)

        self.current_user_id = None
        self.active_menu = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.show_login()

    def t(self, key):
        """Get current theme color"""
        return THEMES[self.current_theme][key]

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        ctk.set_appearance_mode(theme_name)
        self.configure(fg_color=self.t("BG_COLOR"))


    def show_login(self):
        # مسح أي محتوى سابق
        for widget in self.winfo_children():
            widget.destroy()

        # إطار تسجيل الدخول في المنتصف
        login_frame = ctk.CTkFrame(self, fg_color=self.t("CARD_BG"), corner_radius=20,
                                   border_width=2, border_color=self.t("PRIMARY"),
                                   width=500, height=550)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        login_frame.pack_propagate(False)

        login_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(login_frame, text="✝  تسجيل الدخول", font=("Segoe UI", 28, "bold"),
                             text_color=self.t("TEXT_PRIMARY"))
        title.pack(pady=(40, 20))

        self.username_entry = ctk.CTkEntry(login_frame, placeholder_text="اسم المستخدم",
                                          font=("Segoe UI", 14), height=45,
                                          border_color=self.t("CARD_BORDER"), corner_radius=12,
                                          fg_color=self.t("INPUT_BG"))
        self.username_entry.pack(pady=10, padx=40, fill="x")

        self.password_entry = ctk.CTkEntry(login_frame, placeholder_text="كلمة المرور",
                                          font=("Segoe UI", 14), height=45,
                                          border_color=self.t("CARD_BORDER"), corner_radius=12,
                                          fg_color=self.t("INPUT_BG"), show="*")
        self.password_entry.pack(pady=10, padx=40, fill="x")

        btn_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        login_btn = self.create_gradient_button(btn_frame, "🔑  دخول", self.t("PRIMARY"),
                                                self.t("PRIMARY_HOVER"),
                                                self.do_login,
                                                width=130, height=45)
        login_btn.pack(side="right", padx=10)

        register_btn = ctk.CTkButton(btn_frame, text="📝  إنشاء حساب", fg_color="transparent",
                                    hover_color=self.t("CARD_BORDER"),
                                    text_color=self.t("TEXT_SECONDARY"),
                                    font=("Segoe UI", 12, "bold"), height=45, width=130,
                                    corner_radius=12, border_width=1,
                                    border_color=self.t("CARD_BORDER"),
                                    command=self.do_register)
        register_btn.pack(side="right", padx=10)

        self.login_message = ctk.CTkLabel(login_frame, text="", font=("Segoe UI", 12),
                                         text_color=self.t("DANGER"))
        self.login_message.pack(pady=(5, 20))

    def do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.login_message.configure(text="⚠️  الرجاء ملء جميع الحقول", text_color=self.t("DANGER"))
            return

        hashed = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed))
        row = c.fetchone()
        conn.close()

        if row:
            self.current_user_id = row[0]
            self.login_message.configure(text="✅  تم تسجيل الدخول بنجاح", text_color=self.t("ACCENT"))
            self.after(500, self.enter_app)
        else:
            self.login_message.configure(text="❌  اسم المستخدم أو كلمة المرور غير صحيحة", text_color=self.t("DANGER"))

    def do_register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.login_message.configure(text="⚠️  الرجاء ملء جميع الحقول", text_color=self.t("DANGER"))
            return

        if len(password) < 4:
            self.login_message.configure(text="⚠️  كلمة المرور يجب أن تكون 4 أحرف على الأقل", text_color=self.t("DANGER"))
            return

        hashed = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            conn.close()
            self.login_message.configure(text="✅  تم إنشاء الحساب بنجاح، يمكنك تسجيل الدخول الآن", text_color=self.t("ACCENT"))
        except sqlite3.IntegrityError:
            conn.close()
            self.login_message.configure(text="⚠️  اسم المستخدم موجود بالفعل", text_color=self.t("DANGER"))

    def enter_app(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.create_sidebar()

        self.content_container = ctk.CTkFrame(self, fg_color=self.t("BG_COLOR"), corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self.content_frame = ctk.CTkFrame(self.content_container, fg_color=self.t("BG_COLOR"), corner_radius=0)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.show_dashboard()

    def logout(self):
        self.current_user_id = None
        for widget in self.winfo_children():
            widget.destroy()
        self.show_login()


    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=self.t("SIDEBAR_BG"), corner_radius=0, width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        top_line = ctk.CTkFrame(self.sidebar, fg_color=self.t("PRIMARY"), height=3, corner_radius=0)
        top_line.pack(fill="x")

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", pady=(25, 10), padx=20)

        icon_bg = ctk.CTkFrame(brand_frame, fg_color=self.t("PRIMARY"), width=60, height=60, corner_radius=30)
        icon_bg.pack(side="left", padx=(0, 15))
        icon_bg.pack_propagate(False)

        icon_lbl = ctk.CTkLabel(icon_bg, text="✝", font=("Segoe UI", 28, "bold"), text_color="white")
        icon_lbl.pack(expand=True)

        title_frame = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="both", expand=True)

        title_lbl = ctk.CTkLabel(title_frame, text="نظام المخدومين",
                                 font=("Segoe UI", 20, "bold"), text_color=self.t("TEXT_PRIMARY"), anchor="w")
        title_lbl.pack(anchor="w")

        subtitle_lbl = ctk.CTkLabel(title_frame, text="إدارة الخدمة الكنسية",
                                    font=("Segoe UI", 11), text_color=self.t("TEXT_MUTED"), anchor="w")
        subtitle_lbl.pack(anchor="w")

        sep_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=2)
        sep_frame.pack(fill="x", padx=25, pady=(0, 12))
        sep_line = ctk.CTkFrame(sep_frame, fg_color=self.t("CARD_BORDER"), height=1)
        sep_line.pack(fill="x", pady=1)

        self.menu_buttons = {}
        menu_items = [
            ("dashboard", "🏠", "الرئيسية", self.show_dashboard),
            ("add_member", "➕", "تسجيل مخدوم", self.show_add_member),
            ("members", "📋", "قائمة المخدومين", self.show_members_list),
            ("add_visit", "📅", "تسجيل افتقاد", self.show_add_visit),
            ("visits", "📆", "مواعيد الافتقاد", self.show_visits_list),
            ("attendance", "✅", "الحضور والغياب", self.show_attendance),
            ("history", "📊", "سجل الحضور", self.show_attendance_history),
            ("developer", "👨‍💻", "المطور", self.show_developer),
        ]

        for key, icon, text, cmd in menu_items:
            btn = self.create_menu_button(key, icon, text, cmd)
            btn.pack(fill="x", padx=15, pady=4)

        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=15, padx=20)

        logout_btn = ctk.CTkButton(bottom_frame, text="🚪  تسجيل الخروج", fg_color=self.t("DANGER"),
                                   hover_color=self.t("DANGER_HOVER"), text_color="white",
                                   font=("Segoe UI", 11, "bold"), height=42, corner_radius=12,
                                   command=self.logout)
        logout_btn.pack(fill="x", pady=(0, 8))

        theme_icon = "🌙" if self.current_theme == "Light" else "☀️"
        theme_text = "الوضع الفاتح" if self.current_theme == "Dark" else "الوضع الداكن"
        theme_btn = ctk.CTkButton(bottom_frame, text=f"{theme_icon}  {theme_text}",
                                  fg_color=self.t("CARD_BG"), hover_color=self.t("CARD_BORDER"),
                                  text_color=self.t("TEXT_PRIMARY"), font=("Segoe UI", 11, "bold"),
                                  height=42, corner_radius=12, border_width=1,
                                  border_color=self.t("CARD_BORDER"),
                                  command=self.toggle_theme)
        theme_btn.pack(fill="x", pady=(0, 8))

        version_card = ctk.CTkFrame(bottom_frame, fg_color=self.t("CARD_BG"), corner_radius=10,
                                    border_width=1, border_color=self.t("CARD_BORDER"))
        version_card.pack(fill="x")
        version_lbl = ctk.CTkLabel(version_card, text="✨  v3.0  |  معكم في الخدمة",
                                   font=("Segoe UI", 10), text_color=self.t("TEXT_MUTED"))
        version_lbl.pack(pady=10)

    def create_menu_button(self, key, icon, text, command):
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=52, corner_radius=12)
        btn_frame.pack_propagate(False)

        inner = ctk.CTkFrame(btn_frame, fg_color="transparent", corner_radius=12)
        inner.pack(fill="both", expand=True, padx=5, pady=3)

        indicator = ctk.CTkFrame(inner, fg_color="transparent", width=4, corner_radius=2)
        indicator.pack(side="right", fill="y", padx=(0, 10))

        icon_lbl = ctk.CTkLabel(inner, text=icon, font=("Segoe UI", 18), text_color=self.t("TEXT_SECONDARY"))
        icon_lbl.pack(side="right", padx=(0, 12))

        text_lbl = ctk.CTkLabel(inner, text=text, font=("Segoe UI", 13, "bold"),
                                text_color=self.t("TEXT_SECONDARY"), anchor="e")
        text_lbl.pack(side="right", fill="y")

        btn_frame._indicator = indicator
        btn_frame._icon = icon_lbl
        btn_frame._text = text_lbl
        btn_frame._key = key

        def on_enter(e):
            if self.active_menu != key:
                btn_frame.configure(fg_color=self.t("CARD_BG"))
                inner.configure(fg_color=self.t("CARD_BG"))
                icon_lbl.configure(text_color=self.t("TEXT_PRIMARY"))
                text_lbl.configure(text_color=self.t("TEXT_PRIMARY"))

        def on_leave(e):
            if self.active_menu != key:
                btn_frame.configure(fg_color="transparent")
                inner.configure(fg_color="transparent")
                icon_lbl.configure(text_color=self.t("TEXT_SECONDARY"))
                text_lbl.configure(text_color=self.t("TEXT_SECONDARY"))

        def on_click():
            self.set_active_menu(key)
            command()

        for widget in [btn_frame, inner, icon_lbl, text_lbl]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda e: on_click())

        btn_frame._click = on_click
        return btn_frame

    def set_active_menu(self, key):
        self.active_menu = key
        for k, btn in self.menu_buttons.items():
            if k == key:
                btn.configure(fg_color=self.t("PRIMARY"))
                btn.winfo_children()[0].configure(fg_color=self.t("PRIMARY"))
                btn._indicator.configure(fg_color="white")
                btn._icon.configure(text_color="white")
                btn._text.configure(text_color="white")
            else:
                btn.configure(fg_color="transparent")
                btn.winfo_children()[0].configure(fg_color="transparent")
                btn._indicator.configure(fg_color="transparent")
                btn._icon.configure(text_color=self.t("TEXT_SECONDARY"))
                btn._text.configure(text_color=self.t("TEXT_SECONDARY"))

    def clear_content(self):
        if hasattr(self, 'content_frame'):
            for widget in self.content_frame.winfo_children():
                widget.destroy()

    def toggle_theme(self):
        new_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.apply_theme(new_theme)

        if hasattr(self, 'content_container'):
            self.content_container.configure(fg_color=self.t("BG_COLOR"))
        if hasattr(self, 'content_frame'):
            self.content_frame.configure(fg_color=self.t("BG_COLOR"))


        self.sidebar.destroy()
        self.create_sidebar()
        self.set_active_menu(self.active_menu or "dashboard")


        if self.active_menu == "dashboard":
            self.show_dashboard()
        elif self.active_menu == "add_member":
            self.show_add_member()
        elif self.active_menu == "members":
            self.show_members_list()
        elif self.active_menu == "add_visit":
            self.show_add_visit()
        elif self.active_menu == "visits":
            self.show_visits_list()
        elif self.active_menu == "attendance":
            self.show_attendance()
        elif self.active_menu == "history":
            self.show_attendance_history()
        elif self.active_menu == "developer":
            self.show_developer()

    def create_card(self, parent, title=None, padx=0, pady=12):
        card = ctk.CTkFrame(parent, fg_color=self.t("CARD_BG"), corner_radius=16,
                            border_width=1, border_color=self.t("CARD_BORDER"))
        card.pack(fill="x", padx=padx, pady=pady)
        card.grid_columnconfigure(0, weight=1)

        if title:
            title_container = ctk.CTkFrame(card, fg_color="transparent")
            title_container.pack(fill="x", padx=20, pady=(18, 8))

            accent_bar = ctk.CTkFrame(title_container, fg_color=self.t("PRIMARY"), width=4, height=22, corner_radius=2)
            accent_bar.pack(side="right", padx=(10, 0))

            title_lbl = ctk.CTkLabel(title_container, text=title, font=("Segoe UI", 16, "bold"),
                                     text_color=self.t("TEXT_PRIMARY"), anchor="e")
            title_lbl.pack(side="right", fill="y")

            line = ctk.CTkFrame(card, fg_color=self.t("CARD_BORDER"), height=1)
            line.pack(fill="x", padx=20, pady=(0, 12))

        return card

    def create_gradient_button(self, parent, text, color, hover_color, command, width=160, height=42):
        return ctk.CTkButton(parent, text=text, fg_color=color, hover_color=hover_color,
                             font=("Segoe UI", 12, "bold"), height=height, width=width,
                             corner_radius=12, command=command, border_width=0)

    def create_stat_card(self, parent, icon, label, value, color, row, col):
        card = ctk.CTkFrame(parent, fg_color=self.t("CARD_BG"), corner_radius=16,
                            border_width=1, border_color=self.t("CARD_BORDER"))
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        strip = ctk.CTkFrame(card, fg_color=color, height=4, corner_radius=2)
        strip.pack(fill="x", padx=16, pady=(16, 0))

        icon_lbl = ctk.CTkLabel(card, text=icon, font=("Segoe UI", 32), text_color=color)
        icon_lbl.pack(pady=(14, 4))

        val_lbl = ctk.CTkLabel(card, text=value, font=("Segoe UI", 30, "bold"), text_color=self.t("TEXT_PRIMARY"))
        val_lbl.pack()

        lbl = ctk.CTkLabel(card, text=label, font=("Segoe UI", 11), text_color=self.t("TEXT_SECONDARY"))
        lbl.pack(pady=(4, 16))

        return card


    def show_dashboard(self):
        self.set_active_menu("dashboard")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))

        greeting = self.get_greeting()
        header = ctk.CTkLabel(header_frame, text=f"{greeting} 👋",
                              font=("Segoe UI", 28, "bold"), text_color=self.t("TEXT_PRIMARY"), anchor="e")
        header.pack(side="right")

        date_lbl = ctk.CTkLabel(header_frame, text=datetime.now().strftime("%A, %d %B %Y"),
                                font=("Segoe UI", 13), text_color=self.t("TEXT_MUTED"), anchor="w")
        date_lbl.pack(side="left", padx=(0, 10))

        verse_card = ctk.CTkFrame(scroll, fg_color=self.t("CARD_BG"), corner_radius=16,
                                  border_width=1, border_color=self.t("CARD_BORDER"))
        verse_card.pack(fill="x", pady=(0, 20))

        verse_top = ctk.CTkFrame(verse_card, fg_color=self.t("GRADIENT_BOTTOM"), height=3, corner_radius=0)
        verse_top.pack(fill="x")

        verse_inner = ctk.CTkFrame(verse_card, fg_color=self.t("CARD_BG"), corner_radius=0)
        verse_inner.pack(fill="x", padx=1, pady=1)

        verse_icon = ctk.CTkLabel(verse_inner, text="✝️", font=("Segoe UI", 22))
        verse_icon.pack(pady=(18, 8))

        verse_text = get_random_verse()
        verse_lbl = ctk.CTkLabel(verse_inner, text=verse_text, font=("Segoe UI", 15, "italic"),
                                 text_color=self.t("PRIMARY_HOVER"), wraplength=1000, justify="center")
        verse_lbl.pack(padx=30, pady=(0, 18))

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM members WHERE user_id = ?", (self.current_user_id,))
        total_members = c.fetchone()[0]
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM visits WHERE visit_date >= ? AND user_id = ?", (today, self.current_user_id))
        upcoming_visits = c.fetchone()[0]
        upcoming_bdays = self.get_upcoming_bdays_count()
        thirty_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM visits WHERE visit_date >= ? AND visit_date <= ? AND user_id = ?",
                  (thirty_ago, today, self.current_user_id))
        recent_visits = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'present' AND user_id = ?",
                  (today, self.current_user_id))
        today_present = c.fetchone()[0]
        conn.close()

        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 10))
        for i in range(5):
            stats_frame.grid_columnconfigure(i, weight=1)

        self.create_stat_card(stats_frame, "👥", "المخدومين", str(total_members), self.t("PRIMARY"), 0, 0)
        self.create_stat_card(stats_frame, "📅", "افتقادات قادمة", str(upcoming_visits), self.t("ACCENT"), 0, 1)
        self.create_stat_card(stats_frame, "🎂", "أعياد ميلاد", str(upcoming_bdays), self.t("WARNING"), 0, 2)
        self.create_stat_card(stats_frame, "📊", "افتقادات الشهر", str(recent_visits), self.t("PURPLE"), 0, 3)
        self.create_stat_card(stats_frame, "✅", "حضور اليوم", str(today_present), self.t("PRESENT_COLOR"), 0, 4)

        if upcoming_bdays > 0:
            bday_card = self.create_card(scroll, "🎉  تذكير بأعياد الميلاد القريبة")
            bday_list = self.get_upcoming_bdays_list()
            text = ""
            for name, _, days in bday_list:
                if days == 0:
                    text += f"• {name}  —  اليوم! 🎂\n"
                elif days == 1:
                    text += f"• {name}  —  غدًا\n"
                else:
                    text += f"• {name}  —  بعد {days} يوم\n"

            bday_lbl = ctk.CTkLabel(bday_card, text=text, font=("Segoe UI", 13),
                                    text_color=self.t("TEXT_PRIMARY"), justify="right", anchor="e")
            bday_lbl.pack(fill="x", padx=25, pady=15, anchor="e")

        actions_card = self.create_card(scroll, "⚡  إجراءات سريعة")
        actions_inner = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_inner.pack(pady=20, padx=20)

        self.create_gradient_button(actions_inner, "➕  تسجيل مخدوم", self.t("PRIMARY"), self.t("PRIMARY_HOVER"),
                                    self.show_add_member, width=190).pack(side="right", padx=6)
        self.create_gradient_button(actions_inner, "📅  تسجيل افتقاد", self.t("ACCENT"), self.t("ACCENT_HOVER"),
                                    self.show_add_visit, width=190).pack(side="right", padx=6)
        self.create_gradient_button(actions_inner, "✅  تسجيل حضور", self.t("PRESENT_COLOR"), self.t("ACCENT_HOVER"),
                                    self.show_attendance, width=190).pack(side="right", padx=6)
        self.create_gradient_button(actions_inner, "📋  عرض المخدومين", self.t("PURPLE"), self.t("GRADIENT_BOTTOM"),
                                    self.show_members_list, width=190).pack(side="right", padx=6)

    def get_greeting(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "صباح الخير"
        elif 12 <= hour < 17:
            return "مساء الخير"
        else:
            return "مساء النور"

    def get_upcoming_bdays_count(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT birth_date FROM members WHERE birth_date IS NOT NULL AND birth_date != '' AND user_id = ?",
                  (self.current_user_id,))
        rows = c.fetchall()
        conn.close()

        count = 0
        today = datetime.now()
        for (bd,) in rows:
            try:
                bd_date = datetime.strptime(bd, "%Y-%m-%d")
                next_bday = bd_date.replace(year=today.year)
                if next_bday < today:
                    next_bday = next_bday.replace(year=today.year + 1)
                if (next_bday - today).days <= 30:
                    count += 1
            except:
                pass
        return count

    def get_upcoming_bdays_list(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT birth_date, name FROM members WHERE birth_date IS NOT NULL AND birth_date != '' AND user_id = ?",
                  (self.current_user_id,))
        rows = c.fetchall()
        conn.close()

        result = []
        today = datetime.now()
        for bd, name in rows:
            try:
                bd_date = datetime.strptime(bd, "%Y-%m-%d")
                next_bday = bd_date.replace(year=today.year)
                if next_bday < today:
                    next_bday = next_bday.replace(year=today.year + 1)
                delta = (next_bday - today).days
                if delta <= 30:
                    result.append((name, bd, delta))
            except:
                pass
        result.sort(key=lambda x: x[2])
        return result


    def show_add_member(self):
        self.set_active_menu("add_member")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(scroll, text="تسجيل مخدوم جديد", font=("Segoe UI", 26, "bold"),
                              text_color=self.t("TEXT_PRIMARY"), anchor="e")
        header.pack(fill="x", pady=(0, 25), anchor="e")

        card = self.create_card(scroll, "📝  بيانات المخدوم")
        main_form = ctk.CTkFrame(card, fg_color="transparent")
        main_form.pack(pady=20, padx=30, fill="x")

        # Photo section
        photo_frame = ctk.CTkFrame(main_form, fg_color="transparent", width=220)
        photo_frame.pack(side="right", padx=(20, 0), fill="y")
        photo_frame.pack_propagate(False)

        self.member_photo_path = None
        self.photo_display = ctk.CTkFrame(photo_frame, fg_color=self.t("INPUT_BG"),
                                          width=180, height=180, corner_radius=16,
                                          border_width=2, border_color=self.t("CARD_BORDER"))
        self.photo_display.pack(pady=(10, 10))
        self.photo_display.pack_propagate(False)

        self.photo_label = ctk.CTkLabel(self.photo_display, text="📷\nلا توجد صورة",
                                        font=("Segoe UI", 14), text_color=self.t("TEXT_MUTED"))
        self.photo_label.pack(expand=True)

        upload_btn = self.create_gradient_button(photo_frame, "📷  اختيار صورة", self.t("PRIMARY"),
                                                 self.t("PRIMARY_HOVER"), self.upload_member_photo,
                                                 width=180, height=40)
        upload_btn.pack(pady=(5, 5))

        remove_btn = ctk.CTkButton(photo_frame, text="🗑️  إزالة الصورة", fg_color="transparent",
                                   hover_color=self.t("CARD_BORDER"), text_color=self.t("DANGER"),
                                   font=("Segoe UI", 11), height=35, width=180, corner_radius=10,
                                   border_width=1, border_color=self.t("CARD_BORDER"),
                                   command=self.remove_member_photo)
        remove_btn.pack(pady=(0, 10))

        # Fields
        form = ctk.CTkFrame(main_form, fg_color="transparent")
        form.pack(side="right", fill="both", expand=True)

        fields = [
            ("الاسم الكامل *", "name", "أدخل الاسم الكامل..."),
            ("اسم الأسرة", "family_name", "أدخل اسم الأسرة..."),
            ("أب الاعتراف", "confessor", "أدخل اسم أب الاعتراف..."),
            ("العنوان", "address", "أدخل العنوان..."),
            ("رقم الهاتف", "phone", "مثال: 01xxxxxxxxx..."),
            ("تاريخ الميلاد", "birth_date", "YYYY-MM-DD"),
        ]

        self.member_entries = {}
        for label, key, placeholder in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=8)

            lbl = ctk.CTkLabel(row, text=label + " :", font=("Segoe UI", 13),
                               text_color=self.t("TEXT_PRIMARY"), width=200, anchor="e")
            lbl.pack(side="right", padx=(0, 12))

            entry = ctk.CTkEntry(row, font=("Segoe UI", 13), height=42,
                                 placeholder_text=placeholder,
                                 border_color=self.t("CARD_BORDER"), border_width=1,
                                 corner_radius=12, fg_color=self.t("INPUT_BG"))
            entry.pack(side="right", fill="x", expand=True)
            self.member_entries[key] = entry

        # School age
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=8)

        lbl = ctk.CTkLabel(row, text="السن الدراسي :", font=("Segoe UI", 13),
                           text_color=self.t("TEXT_PRIMARY"), width=200, anchor="e")
        lbl.pack(side="right", padx=(0, 12))

        self.school_age_var = ctk.StringVar(value="اختر السن الدراسي")
        self.school_age_combo = ctk.CTkComboBox(row, values=SCHOOL_AGES,
                                                font=("Segoe UI", 13), height=42,
                                                border_color=self.t("CARD_BORDER"), corner_radius=12,
                                                fg_color=self.t("INPUT_BG"), variable=self.school_age_var,
                                                dropdown_fg_color=self.t("CARD_BG"),
                                                dropdown_hover_color=self.t("PRIMARY_GLOW"),
                                                dropdown_text_color=self.t("TEXT_PRIMARY"),
                                                button_color=self.t("PRIMARY"),
                                                button_hover_color=self.t("PRIMARY_HOVER"))
        self.school_age_combo.pack(side="right", fill="x", expand=True)

        # Notes
        notes_row = ctk.CTkFrame(form, fg_color="transparent")
        notes_row.pack(fill="x", pady=8)
        notes_lbl = ctk.CTkLabel(notes_row, text="ملاحظات :", font=("Segoe UI", 13),
                                 text_color=self.t("TEXT_PRIMARY"), width=200, anchor="e")
        notes_lbl.pack(side="right", padx=(0, 12))

        self.notes_text = ctk.CTkTextbox(notes_row, font=("Segoe UI", 13), height=100,
                                         border_color=self.t("CARD_BORDER"), border_width=1,
                                         corner_radius=12, fg_color=self.t("INPUT_BG"))
        self.notes_text.pack(side="right", fill="x", expand=True)

        # Buttons
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=25)

        save_btn = self.create_gradient_button(btn_row, "💾  حفظ البيانات", self.t("ACCENT"),
                                               self.t("ACCENT_HOVER"), self.save_member, width=190, height=48)
        save_btn.pack(side="right", padx=6)

        clear_btn = ctk.CTkButton(btn_row, text="🔄  مسح الحقول", fg_color="transparent",
                                  hover_color=self.t("CARD_BORDER"), text_color=self.t("TEXT_SECONDARY"),
                                  font=("Segoe UI", 12, "bold"), height=48, width=160, corner_radius=12,
                                  border_width=1, border_color=self.t("CARD_BORDER"),
                                  command=self.clear_member_form)
        clear_btn.pack(side="right", padx=6)

    def upload_member_photo(self):
        file_path = filedialog.askopenfilename(
            title="اختيار صورة المخدوم",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            self.member_photo_path = file_path
            try:
                img = Image.open(file_path)
                img = img.resize((150, 150), Image.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 150))
                self.photo_label.configure(image=photo, text="")
                self.photo_label.image = photo
            except Exception as e:
                messagebox.showerror("خطأ", f"لا يمكن تحميل الصورة: {e}")

    def remove_member_photo(self):
        self.member_photo_path = None
        self.photo_label.configure(image=None, text="📷\nلا توجد صورة")

    def validate_date(self, date_str, allow_future=False):
        if not date_str:
            return True
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if not allow_future and dt > datetime.now():
                return False
            return True
        except ValueError:
            return False

    def save_member(self):
        name = self.member_entries["name"].get().strip()
        if not name:
            messagebox.showerror("⚠️ خطأ", "الاسم مطلوب!")
            return

        birth_date = self.member_entries["birth_date"].get().strip()
        if birth_date and not self.validate_date(birth_date, allow_future=False):
            messagebox.showerror("⚠️ خطأ", "تاريخ الميلاد غير صحيح! يجب أن يكون بصيغة YYYY-MM-DD ولا يمكن أن يكون في المستقبل.")
            return

        photo_dest = None
        if self.member_photo_path and os.path.exists(self.member_photo_path):
            ext = os.path.splitext(self.member_photo_path)[1]
            photo_dest = os.path.join(IMAGES_DIR, f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")
            try:
                import shutil
                shutil.copy2(self.member_photo_path, photo_dest)
            except:
                photo_dest = None

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO members (name, school_age, family_name, confessor, address, phone, birth_date, notes, photo_path, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            self.school_age_var.get() if self.school_age_var.get() != "اختر السن الدراسي" else "",
            self.member_entries["family_name"].get().strip(),
            self.member_entries["confessor"].get().strip(),
            self.member_entries["address"].get().strip(),
            self.member_entries["phone"].get().strip(),
            birth_date,
            self.notes_text.get("0.0", "end").strip(),
            photo_dest,
            self.current_user_id
        ))
        conn.commit()
        conn.close()

        messagebox.showinfo("✅ تم", "تم تسجيل المخدوم بنجاح!")
        self.clear_member_form()

    def clear_member_form(self):
        for entry in self.member_entries.values():
            entry.delete(0, "end")
        self.school_age_var.set("اختر السن الدراسي")
        self.notes_text.delete("0.0", "end")
        self.remove_member_photo()


    def show_members_list(self):
        self.set_active_menu("members")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(scroll, text="قائمة المخدومين", font=("Segoe UI", 26, "bold"),
                              text_color=self.t("TEXT_PRIMARY"), anchor="e")
        header.pack(fill="x", pady=(0, 25), anchor="e")

        filter_card = self.create_card(scroll, "🔍  بحث وفلترة متقدم")
        filter_frame = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_frame.pack(pady=18, padx=25, fill="x")

        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="🔍  بحث بالاسم...",
                                         font=("Segoe UI", 12), height=42,
                                         border_color=self.t("CARD_BORDER"), corner_radius=12,
                                         fg_color=self.t("INPUT_BG"))
        self.search_entry.pack(side="right", padx=6, fill="x", expand=True)

        self.filter_age_var = ctk.StringVar(value="الكل")
        filter_age_combo = ctk.CTkComboBox(filter_frame, values=["الكل"] + SCHOOL_AGES,
                                           font=("Segoe UI", 12), height=42, width=150,
                                           border_color=self.t("CARD_BORDER"), corner_radius=12,
                                           fg_color=self.t("INPUT_BG"), variable=self.filter_age_var,
                                           dropdown_fg_color=self.t("CARD_BG"),
                                           dropdown_hover_color=self.t("PRIMARY_GLOW"),
                                           dropdown_text_color=self.t("TEXT_PRIMARY"),
                                           button_color=self.t("PRIMARY"),
                                           button_hover_color=self.t("PRIMARY_HOVER"))
        filter_age_combo.pack(side="right", padx=6)

        self.filter_family = ctk.CTkEntry(filter_frame, placeholder_text="اسم الأسرة",
                                          font=("Segoe UI", 12), height=42, width=150,
                                          border_color=self.t("CARD_BORDER"), corner_radius=12,
                                          fg_color=self.t("INPUT_BG"))
        self.filter_family.pack(side="right", padx=6)

        search_btn = self.create_gradient_button(filter_frame, "بحث", self.t("PRIMARY"),
                                                 self.t("PRIMARY_HOVER"), self.load_members, width=100, height=42)
        search_btn.pack(side="right", padx=(20, 6))

        clear_btn = ctk.CTkButton(filter_frame, text="إلغاء", fg_color="transparent",
                                  hover_color=self.t("CARD_BORDER"), text_color=self.t("TEXT_SECONDARY"),
                                  font=("Segoe UI", 11, "bold"), height=42, width=90, corner_radius=12,
                                  border_width=1, border_color=self.t("CARD_BORDER"),
                                  command=self.clear_filters)
        clear_btn.pack(side="right", padx=6)

        self.results_count = ctk.CTkLabel(scroll, text="", font=("Segoe UI", 12),
                                          text_color=self.t("TEXT_MUTED"), anchor="e")
        self.results_count.pack(fill="x", pady=(5, 10), anchor="e")

        table_card = ctk.CTkFrame(scroll, fg_color=self.t("CARD_BG"), corner_radius=16,
                                  border_width=1, border_color=self.t("CARD_BORDER"))
        table_card.pack(fill="both", expand=True, pady=10)

        headers_frame = ctk.CTkFrame(table_card, fg_color=self.t("HEADER_BG"), corner_radius=0, height=45)
        headers_frame.pack(fill="x", padx=1, pady=(1, 0))
        headers_frame.pack_propagate(False)

        headers = ["#", "الصورة", "الاسم", "السن", "الأسرة", "أب الاعتراف", "العنوان", "الهاتف", "الميلاد"]
        widths = [50, 70, 140, 100, 100, 120, 120, 110, 110]

        for h, w in zip(headers, widths):
            lbl = ctk.CTkLabel(headers_frame, text=h, font=("Segoe UI", 12, "bold"),
                               text_color="white", width=w)
            lbl.pack(side="right", padx=5)

        self.members_rows_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        self.members_rows_frame.pack(fill="both", expand=True, padx=1, pady=1)

        action_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        action_frame.pack(fill="x", pady=15)

        del_btn = self.create_gradient_button(action_frame, "🗑️  حذف المحدد", self.t("DANGER"),
                                              self.t("DANGER_HOVER"), self.delete_member, width=150, height=42)
        del_btn.pack(side="right", padx=6)

        edit_btn = self.create_gradient_button(action_frame, "✏️  تعديل", self.t("WARNING"), "#D97706",
                                               self.edit_member, width=130, height=42)
        edit_btn.pack(side="right", padx=6)

        refresh_btn = self.create_gradient_button(action_frame, "🔄  تحديث", self.t("PRIMARY"),
                                                  self.t("PRIMARY_HOVER"), self.load_members, width=130, height=42)
        refresh_btn.pack(side="right", padx=6)

        self.selected_member_id = None
        self.load_members()

    def load_members(self):
        for widget in self.members_rows_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        query = """
            SELECT id, name, school_age, family_name, confessor, address, phone, birth_date, photo_path
            FROM members WHERE user_id = ?
        """
        params = [self.current_user_id]

        search = self.search_entry.get().strip()
        if search and search != "بحث بالاسم...":
            query += " AND name LIKE ?"
            params.append(f"%{search}%")

        age = self.filter_age_var.get()
        if age and age != "الكل":
            query += " AND school_age = ?"
            params.append(age)

        family = self.filter_family.get().strip()
        if family and family != "اسم الأسرة":
            query += " AND family_name LIKE ?"
            params.append(f"%{family}%")

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        self.results_count.configure(text=f"📋  عدد النتائج: {len(rows)} مخدوم")

        for idx, row in enumerate(rows):
            bg = self.t("CARD_BG") if idx % 2 == 0 else self.t("CARD_BG_ALT")
            row_frame = ctk.CTkFrame(self.members_rows_frame, fg_color=bg, height=55, corner_radius=0)
            row_frame.pack(fill="x")
            row_frame.pack_propagate(False)
            row_frame.bind("<Button-1>", lambda e, rid=row[0], rf=row_frame: self.select_member(rid, rf))

            member_id = row[0]
            photo_path = row[8]

            id_lbl = ctk.CTkLabel(row_frame, text=str(member_id), font=("Segoe UI", 11),
                                  text_color=self.t("TEXT_PRIMARY"), width=50)
            id_lbl.pack(side="right", padx=5)
            id_lbl.bind("<Button-1>", lambda e, rid=row[0], rf=row_frame: self.select_member(rid, rf))

            photo_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=60, height=45)
            photo_frame.pack(side="right", padx=3)
            photo_frame.pack_propagate(False)

            if photo_path and os.path.exists(photo_path):
                try:
                    img = Image.open(photo_path)
                    img = img.resize((40, 40), Image.LANCZOS)
                    photo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
                    photo_lbl = ctk.CTkLabel(photo_frame, image=photo_img, text="")
                    photo_lbl.pack(expand=True)
                    photo_lbl.image = photo_img
                except:
                    ctk.CTkLabel(photo_frame, text="🖼️", font=("Segoe UI", 16)).pack(expand=True)
            else:
                ctk.CTkLabel(photo_frame, text="👤", font=("Segoe UI", 16),
                             text_color=self.t("TEXT_MUTED")).pack(expand=True)

            values = [
                row[1],                   # name
                row[2] or "—",            # school_age
                row[3] or "—",            # family_name
                row[4] or "—",            # confessor
                row[5] or "—",            # address
                row[6] or "—",            # phone
                row[7] or "—"             # birth_date
            ]
            widths = [140, 100, 100, 120, 120, 110, 110]

            for val, w in zip(values, widths):
                lbl = ctk.CTkLabel(row_frame, text=val, font=("Segoe UI", 11),
                                   text_color=self.t("TEXT_PRIMARY"), width=w)
                lbl.pack(side="right", padx=5)
                lbl.bind("<Button-1>", lambda e, rid=row[0], rf=row_frame: self.select_member(rid, rf))

    def select_member(self, member_id, row_frame):
        self.selected_member_id = member_id
        for child in self.members_rows_frame.winfo_children():
            idx = list(self.members_rows_frame.winfo_children()).index(child)
            child.configure(fg_color=self.t("CARD_BG") if idx % 2 == 0 else self.t("CARD_BG_ALT"))
        row_frame.configure(fg_color=self.t("PRIMARY_GLOW"))

    def clear_filters(self):
        self.search_entry.delete(0, "end")
        self.filter_age_var.set("الكل")
        self.filter_family.delete(0, "end")
        self.load_members()

    def delete_member(self):
        if not self.selected_member_id:
            messagebox.showwarning("⚠️ تنبيه", "الرجاء اختيار مخدوم أولاً")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT user_id FROM members WHERE id = ?", (self.selected_member_id,))
        row = c.fetchone()
        if not row or row[0] != self.current_user_id:
            conn.close()
            messagebox.showerror("⚠️ خطأ", "لا يمكن حذف بيانات مستخدم آخر")
            return

        if messagebox.askyesno("🗑️ تأكيد الحذف", "هل أنت متأكد من حذف هذا المخدوم؟\nلا يمكن التراجع عن هذا الإجراء."):
            c.execute("SELECT photo_path FROM members WHERE id = ?", (self.selected_member_id,))
            result = c.fetchone()
            if result and result[0] and os.path.exists(result[0]):
                try:
                    os.remove(result[0])
                except:
                    pass
            c.execute("DELETE FROM members WHERE id = ?", (self.selected_member_id,))
            conn.commit()
            conn.close()
            self.selected_member_id = None
            self.load_members()
            messagebox.showinfo("✅ تم", "تم حذف المخدوم بنجاح")
        else:
            conn.close()

    def edit_member(self):
        if not self.selected_member_id:
            messagebox.showwarning("⚠️ تنبيه", "الرجاء اختيار مخدوم أولاً")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM members WHERE id = ? AND user_id = ?", (self.selected_member_id, self.current_user_id))
        row = c.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("⚠️ خطأ", "لا يمكن تعديل بيانات مستخدم آخر")
            return

        edit_win = ctk.CTkToplevel(self)
        edit_win.title("تعديل بيانات المخدوم")
        edit_win.geometry("700x750")
        edit_win.minsize(600, 600)
        edit_win.configure(fg_color=self.t("BG_COLOR"))

        edit_win.update_idletasks()
        x = (edit_win.winfo_screenwidth() // 2) - (700 // 2)
        y = (edit_win.winfo_screenheight() // 2) - (750 // 2)
        edit_win.geometry(f"+{x}+{y}")

        card = ctk.CTkFrame(edit_win, fg_color=self.t("CARD_BG"), corner_radius=16,
                            border_width=1, border_color=self.t("CARD_BORDER"))
        card.pack(fill="both", expand=True, padx=25, pady=25)

        title = ctk.CTkLabel(card, text="✏️  تعديل بيانات المخدوم", font=("Segoe UI", 20, "bold"),
                             text_color=self.t("TEXT_PRIMARY"))
        title.pack(pady=20)

        # Photo section
        photo_frame = ctk.CTkFrame(card, fg_color="transparent")
        photo_frame.pack(pady=10)

        self.edit_photo_path = row[9]  # photo_path
        self.edit_photo_display = ctk.CTkFrame(photo_frame, fg_color=self.t("INPUT_BG"),
                                               width=120, height=120, corner_radius=16,
                                               border_width=2, border_color=self.t("CARD_BORDER"))
        self.edit_photo_display.pack(side="right", padx=10)
        self.edit_photo_display.pack_propagate(False)

        self.edit_photo_label = ctk.CTkLabel(self.edit_photo_display, text="📷\nلا توجد صورة",
                                             font=("Segoe UI", 12), text_color=self.t("TEXT_MUTED"))
        self.edit_photo_label.pack(expand=True)

        if self.edit_photo_path and os.path.exists(self.edit_photo_path):
            try:
                img = Image.open(self.edit_photo_path)
                img = img.resize((100, 100), Image.LANCZOS)
                photo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                self.edit_photo_label.configure(image=photo_img, text="")
                self.edit_photo_label.image = photo_img
            except:
                pass

        photo_btn_frame = ctk.CTkFrame(photo_frame, fg_color="transparent")
        photo_btn_frame.pack(side="right", padx=10)

        upload_btn = self.create_gradient_button(photo_btn_frame, "📷  تغيير الصورة", self.t("PRIMARY"),
                                                 self.t("PRIMARY_HOVER"),
                                                 lambda: self.upload_edit_photo(), width=160, height=36)
        upload_btn.pack(pady=3)

        remove_btn = ctk.CTkButton(photo_btn_frame, text="🗑️  إزالة", fg_color="transparent",
                                   hover_color=self.t("CARD_BORDER"), text_color=self.t("DANGER"),
                                   font=("Segoe UI", 11), height=36, width=160, corner_radius=10,
                                   border_width=1, border_color=self.t("CARD_BORDER"),
                                   command=self.remove_edit_photo)
        remove_btn.pack(pady=3)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(pady=15, padx=25, fill="x")

        fields_data = [
            ("الاسم", row[1]),
            ("اسم الأسرة", row[3] or ""),
            ("أب الاعتراف", row[4] or ""),
            ("العنوان", row[5] or ""),
            ("رقم الهاتف", row[6] or ""),
            ("تاريخ الميلاد", row[8] or ""),
        ]

        entries = {}
        for label, val in fields_data:
            row_f = ctk.CTkFrame(form, fg_color="transparent")
            row_f.pack(fill="x", pady=6)

            lbl = ctk.CTkLabel(row_f, text=label + " :", font=("Segoe UI", 12),
                               text_color=self.t("TEXT_PRIMARY"), width=160, anchor="e")
            lbl.pack(side="right", padx=(0, 12))

            entry = ctk.CTkEntry(row_f, font=("Segoe UI", 12), height=40,
                                 border_color=self.t("CARD_BORDER"), corner_radius=12,
                                 fg_color=self.t("INPUT_BG"))
            entry.insert(0, val)
            entry.pack(side="right", fill="x", expand=True)
            entries[label] = entry

        # School age
        age_row = ctk.CTkFrame(form, fg_color="transparent")
        age_row.pack(fill="x", pady=6)
        age_lbl = ctk.CTkLabel(age_row, text="السن الدراسي :", font=("Segoe UI", 12),
                               text_color=self.t("TEXT_PRIMARY"), width=160, anchor="e")
        age_lbl.pack(side="right", padx=(0, 12))

        edit_age_var = ctk.StringVar(value=row[2] if row[2] else "اختر السن الدراسي")
        age_combo = ctk.CTkComboBox(age_row, values=SCHOOL_AGES,
                                    font=("Segoe UI", 12), height=40,
                                    border_color=self.t("CARD_BORDER"), corner_radius=12,
                                    fg_color=self.t("INPUT_BG"), variable=edit_age_var,
                                    dropdown_fg_color=self.t("CARD_BG"),
                                    dropdown_hover_color=self.t("PRIMARY_GLOW"),
                                    dropdown_text_color=self.t("TEXT_PRIMARY"),
                                    button_color=self.t("PRIMARY"),
                                    button_hover_color=self.t("PRIMARY_HOVER"))
        age_combo.pack(side="right", fill="x", expand=True)

        # Notes
        notes_row = ctk.CTkFrame(form, fg_color="transparent")
        notes_row.pack(fill="x", pady=6)
        notes_lbl = ctk.CTkLabel(notes_row, text="ملاحظات :", font=("Segoe UI", 12),
                                 text_color=self.t("TEXT_PRIMARY"), width=160, anchor="e")
        notes_lbl.pack(side="right", padx=(0, 12))
        notes_txt = ctk.CTkTextbox(notes_row, font=("Segoe UI", 12), height=80,
                                   border_color=self.t("CARD_BORDER"), corner_radius=12,
                                   fg_color=self.t("INPUT_BG"))
        notes_txt.insert("0.0", row[7] or "")
        notes_txt.pack(side="right", fill="x", expand=True)

        def save_edit():
            new_birth = entries["تاريخ الميلاد"].get().strip()
            if new_birth and not self.validate_date(new_birth, allow_future=False):
                messagebox.showerror("⚠️ خطأ", "تاريخ الميلاد غير صحيح! يجب أن يكون بصيغة YYYY-MM-DD ولا يمكن أن يكون في المستقبل.")
                return

            new_photo = self.edit_photo_path
            if new_photo and os.path.exists(new_photo) and not new_photo.startswith(IMAGES_DIR):
                ext = os.path.splitext(new_photo)[1]
                new_photo = os.path.join(IMAGES_DIR, f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")
                try:
                    import shutil
                    shutil.copy2(self.edit_photo_path, new_photo)
                except:
                    new_photo = self.edit_photo_path

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
                UPDATE members SET name=?, school_age=?, family_name=?, confessor=?, address=?, phone=?, birth_date=?, notes=?, photo_path=?
                WHERE id=? AND user_id=?
            """, (
                entries["الاسم"].get().strip(),
                edit_age_var.get() if edit_age_var.get() != "اختر السن الدراسي" else "",
                entries["اسم الأسرة"].get().strip(),
                entries["أب الاعتراف"].get().strip(),
                entries["العنوان"].get().strip(),
                entries["رقم الهاتف"].get().strip(),
                new_birth,
                notes_txt.get("0.0", "end").strip(),
                new_photo,
                self.selected_member_id,
                self.current_user_id
            ))
            conn.commit()
            conn.close()
            edit_win.destroy()
            self.load_members()
            messagebox.showinfo("✅ تم", "تم تحديث البيانات بنجاح")

        btn = self.create_gradient_button(card, "💾  حفظ التعديلات", self.t("ACCENT"),
                                          self.t("ACCENT_HOVER"), save_edit, width=220, height=48)
        btn.pack(pady=25)

    def upload_edit_photo(self):
        file_path = filedialog.askopenfilename(
            title="اختيار صورة جديدة",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if file_path:
            self.edit_photo_path = file_path
            try:
                img = Image.open(file_path)
                img = img.resize((100, 100), Image.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                self.edit_photo_label.configure(image=photo, text="")
                self.edit_photo_label.image = photo
            except Exception as e:
                messagebox.showerror("خطأ", f"لا يمكن تحميل الصورة: {e}")

    def remove_edit_photo(self):
        self.edit_photo_path = None
        self.edit_photo_label.configure(image=None, text="📷\nلا توجد صورة")


    def show_add_visit(self):
        self.set_active_menu("add_visit")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(scroll, text="تسجيل موعد افتقاد", font=("Segoe UI", 26, "bold"),
                              text_color=self.t("TEXT_PRIMARY"), anchor="e")
        header.pack(fill="x", pady=(0, 25), anchor="e")

        card = self.create_card(scroll, "📅  بيانات الافتقاد")
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(pady=25, padx=35, fill="x")

        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=10)
        lbl = ctk.CTkLabel(row, text="اختيار المخدوم :", font=("Segoe UI", 13),
                           text_color=self.t("TEXT_PRIMARY"), width=220, anchor="e")
        lbl.pack(side="right", padx=(0, 12))

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, name FROM members WHERE user_id = ? ORDER BY name", (self.current_user_id,))
        members = c.fetchall()
        conn.close()

        self.visit_member_var = ctk.StringVar()
        member_combo = ctk.CTkComboBox(row, values=[f"{m[0]} - {m[1]}" for m in members],
                                       font=("Segoe UI", 13), height=45,
                                       border_color=self.t("CARD_BORDER"), corner_radius=12,
                                       fg_color=self.t("INPUT_BG"), variable=self.visit_member_var,
                                       dropdown_fg_color=self.t("CARD_BG"),
                                       dropdown_hover_color=self.t("PRIMARY_GLOW"),
                                       dropdown_text_color=self.t("TEXT_PRIMARY"),
                                       button_color=self.t("PRIMARY"),
                                       button_hover_color=self.t("PRIMARY_HOVER"))
        member_combo.pack(side="right", fill="x", expand=True)

        fields = [
            ("المكان *", "place", "أدخل مكان الافتقاد..."),
            ("التاريخ (YYYY-MM-DD) *", "visit_date", datetime.now().strftime("%Y-%m-%d")),
            ("رقم الهاتف", "phone", "رقم التواصل..."),
            ("نوع الافتقاد", "visit_type", "مثال: زيارة منزلية، اجتماع..."),
        ]

        self.visit_entries = {}
        for label, key, placeholder in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=10)

            lbl = ctk.CTkLabel(row, text=label + " :", font=("Segoe UI", 13),
                               text_color=self.t("TEXT_PRIMARY"), width=220, anchor="e")
            lbl.pack(side="right", padx=(0, 12))

            entry = ctk.CTkEntry(row, font=("Segoe UI", 13), height=45,
                                 placeholder_text=placeholder,
                                 border_color=self.t("CARD_BORDER"), border_width=1,
                                 corner_radius=12, fg_color=self.t("INPUT_BG"))
            entry.pack(side="right", fill="x", expand=True)
            self.visit_entries[key] = entry

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=25)

        save_btn = self.create_gradient_button(btn_row, "💾  حفظ", self.t("ACCENT"),
                                               self.t("ACCENT_HOVER"), self.save_visit, width=160, height=48)
        save_btn.pack(side="right", padx=6)

        clear_btn = ctk.CTkButton(btn_row, text="🔄  مسح", fg_color="transparent",
                                  hover_color=self.t("CARD_BORDER"), text_color=self.t("TEXT_SECONDARY"),
                                  font=("Segoe UI", 12, "bold"), height=48, width=130, corner_radius=12,
                                  border_width=1, border_color=self.t("CARD_BORDER"),
                                  command=self.clear_visit_form)
        clear_btn.pack(side="right", padx=6)

    def save_visit(self):
        place = self.visit_entries["place"].get().strip()
        date_str = self.visit_entries["visit_date"].get().strip()

        if not place or not date_str:
            messagebox.showerror("⚠️ خطأ", "المكان والتاريخ مطلوبان!")
            return

        if not self.validate_date(date_str, allow_future=True):
            messagebox.showerror("⚠️ خطأ", "التاريخ غير صحيح! يجب أن يكون بصيغة YYYY-MM-DD.")
            return

        member_id = None
        member_sel = self.visit_member_var.get()
        if member_sel and " - " in member_sel:
            member_id = int(member_sel.split(" - ")[0])

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO visits (place, visit_date, phone, visit_type, member_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (place, date_str, self.visit_entries["phone"].get().strip(),
              self.visit_entries["visit_type"].get().strip(), member_id, self.current_user_id))
        conn.commit()
        conn.close()

        messagebox.showinfo("✅ تم", "تم تسجيل موعد الافتقاد بنجاح!")
        self.clear_visit_form()

    def clear_visit_form(self):
        for entry in self.visit_entries.values():
            entry.delete(0, "end")
        self.visit_member_var.set("")


    def show_visits_list(self):
        self.set_active_menu("visits")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(scroll, text="مواعيد الافتقاد", font=("Segoe UI", 26, "bold"),
                              text_color=self.t("TEXT_PRIMARY"), anchor="e")
        header.pack(fill="x", pady=(0, 25), anchor="e")

        filter_card = self.create_card(scroll, "🔍  فلترة المواعيد")
        filter_frame = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_frame.pack(pady=15, padx=25)

        show_all = self.create_gradient_button(filter_frame, "الكل", self.t("PRIMARY"),
                                               self.t("PRIMARY_HOVER"), lambda: self.load_visits("all"),
                                               width=110, height=38)
        show_all.pack(side="right", padx=6)

        show_upcoming = self.create_gradient_button(filter_frame, "القادمة", self.t("ACCENT"),
                                                    self.t("ACCENT_HOVER"), lambda: self.load_visits("upcoming"),
                                                    width=110, height=38)
        show_upcoming.pack(side="right", padx=6)

        show_past = ctk.CTkButton(filter_frame, text="السابقة", fg_color="transparent",
                                  hover_color=self.t("CARD_BORDER"), text_color=self.t("TEXT_SECONDARY"),
                                  font=("Segoe UI", 11, "bold"), height=38, width=110, corner_radius=12,
                                  border_width=1, border_color=self.t("CARD_BORDER"),
                                  command=lambda: self.load_visits("past"))
        show_past.pack(side="right", padx=6)

        table_card = ctk.CTkFrame(scroll, fg_color=self.t("CARD_BG"), corner_radius=16,
                                  border_width=1, border_color=self.t("CARD_BORDER"))
        table_card.pack(fill="both", expand=True, pady=15)

        headers_frame = ctk.CTkFrame(table_card, fg_color=self.t("HEADER_BG"), corner_radius=0, height=45)
        headers_frame.pack(fill="x", padx=1, pady=(1, 0))
        headers_frame.pack_propagate(False)

        headers = ["#", "المخدوم", "المكان", "التاريخ", "الهاتف", "نوع الافتقاد"]
        widths = [50, 160, 160, 130, 130, 160]

        for h, w in zip(headers, widths):
            lbl = ctk.CTkLabel(headers_frame, text=h, font=("Segoe UI", 12, "bold"),
                               text_color="white", width=w)
            lbl.pack(side="right", padx=5)

        self.visits_rows_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        self.visits_rows_frame.pack(fill="both", expand=True, padx=1, pady=1)

        action_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        action_frame.pack(fill="x", pady=15)

        del_btn = self.create_gradient_button(action_frame, "🗑️  حذف المحدد", self.t("DANGER"),
                                              self.t("DANGER_HOVER"), self.delete_visit, width=150, height=42)
        del_btn.pack(side="right", padx=6)

        self.selected_visit_id = None
        self.load_visits("all")

    def load_visits(self, filter_type):
        for widget in self.visits_rows_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT v.id, m.name, v.place, v.visit_date, v.phone, v.visit_type
            FROM visits v
            LEFT JOIN members m ON v.member_id = m.id
            WHERE v.user_id = ?
        """
        params = [self.current_user_id]

        if filter_type == "upcoming":
            query += " AND v.visit_date >= ? ORDER BY v.visit_date"
            params.append(today)
        elif filter_type == "past":
            query += " AND v.visit_date < ? ORDER BY v.visit_date DESC"
            params.append(today)
        else:
            query += " ORDER BY v.visit_date"

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        for idx, row in enumerate(rows):
            bg = self.t("CARD_BG") if idx % 2 == 0 else self.t("CARD_BG_ALT")
            row_frame = ctk.CTkFrame(self.visits_rows_frame, fg_color=bg, height=42, corner_radius=0)
            row_frame.pack(fill="x")
            row_frame.pack_propagate(False)
            row_frame.bind("<Button-1>", lambda e, rid=row[0], rf=row_frame: self.select_visit(rid, rf))

            values = [str(row[0]), row[1] or "—", row[2], row[3], row[4] or "", row[5] or ""]
            widths = [50, 160, 160, 130, 130, 160]

            for val, w in zip(values, widths):
                lbl = ctk.CTkLabel(row_frame, text=val, font=("Segoe UI", 11),
                                   text_color=self.t("TEXT_PRIMARY"), width=w)
                lbl.pack(side="right", padx=5)
                lbl.bind("<Button-1>", lambda e, rid=row[0], rf=row_frame: self.select_visit(rid, rf))

    def select_visit(self, visit_id, row_frame):
        self.selected_visit_id = visit_id
        for child in self.visits_rows_frame.winfo_children():
            idx = list(self.visits_rows_frame.winfo_children()).index(child)
            child.configure(fg_color=self.t("CARD_BG") if idx % 2 == 0 else self.t("CARD_BG_ALT"))
        row_frame.configure(fg_color=self.t("PRIMARY_GLOW"))

    def delete_visit(self):
        if not self.selected_visit_id:
            messagebox.showwarning("⚠️ تنبيه", "الرجاء اختيار موعد أولاً")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT user_id FROM visits WHERE id = ?", (self.selected_visit_id,))
        row = c.fetchone()
        if not row or row[0] != self.current_user_id:
            conn.close()
            messagebox.showerror("⚠️ خطأ", "لا يمكن حذف بيانات مستخدم آخر")
            return

        if messagebox.askyesno("🗑️ تأكيد", "هل أنت متأكد من حذف هذا الموعد؟"):
            c.execute("DELETE FROM visits WHERE id = ?", (self.selected_visit_id,))
            conn.commit()
            conn.close()
            self.selected_visit_id = None
            self.load_visits("all")
            messagebox.showinfo("✅ تم", "تم الحذف بنجاح")
        else:
            conn.close()


    def show_attendance(self):
        self.set_active_menu("attendance")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(scroll, text="تسجيل الحضور والغياب", font=("Segoe UI", 26, "bold"),
                              text_color=self.t("TEXT_PRIMARY"), anchor="e")
        header.pack(fill="x", pady=(0, 25), anchor="e")

        filter_card = self.create_card(scroll, "📅  اختر التاريخ والفلتر")
        filter_frame = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_frame.pack(pady=18, padx=25, fill="x")

        date_lbl = ctk.CTkLabel(filter_frame, text="التاريخ :", font=("Segoe UI", 13),
                                text_color=self.t("TEXT_PRIMARY"), width=90, anchor="e")
        date_lbl.pack(side="right", padx=(0, 12))

        today_str = datetime.now().strftime("%Y-%m-%d")
        self.attendance_date = ctk.CTkEntry(filter_frame, font=("Segoe UI", 13), height=45, width=150,
                                            border_color=self.t("CARD_BORDER"), corner_radius=12,
                                            fg_color=self.t("INPUT_BG"))
        self.attendance_date.insert(0, today_str)
        self.attendance_date.pack(side="right", padx=6)

        age_lbl = ctk.CTkLabel(filter_frame, text="السن الدراسي :", font=("Segoe UI", 13),
                               text_color=self.t("TEXT_PRIMARY"), width=130, anchor="e")
        age_lbl.pack(side="right", padx=(35, 12))

        self.attendance_age_filter = ctk.CTkEntry(filter_frame, placeholder_text="الكل",
                                                  font=("Segoe UI", 13), height=45, width=150,
                                                  border_color=self.t("CARD_BORDER"), corner_radius=12,
                                                  fg_color=self.t("INPUT_BG"))
        self.attendance_age_filter.pack(side="right", padx=6)

        load_btn = self.create_gradient_button(filter_frame, "🔍  عرض المخدومين", self.t("PRIMARY"),
                                               self.t("PRIMARY_HOVER"), self.load_attendance_members,
                                               width=170, height=45)
        load_btn.pack(side="right", padx=(25, 6))

        table_card = ctk.CTkFrame(scroll, fg_color=self.t("CARD_BG"), corner_radius=16,
                                  border_width=1, border_color=self.t("CARD_BORDER"))
        table_card.pack(fill="both", expand=True, pady=15)

        headers_frame = ctk.CTkFrame(table_card, fg_color=self.t("HEADER_BG"), corner_radius=0, height=48)
        headers_frame.pack(fill="x", padx=1, pady=(1, 0))
        headers_frame.pack_propagate(False)

        headers = ["#", "الاسم", "السن الدراسي", "الأسرة", "الحالة"]
        widths = [55, 220, 140, 170, 240]

        for h, w in zip(headers, widths):
            lbl = ctk.CTkLabel(headers_frame, text=h, font=("Segoe UI", 12, "bold"),
                               text_color="white", width=w)
            lbl.pack(side="right", padx=5)

        self.attendance_rows_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        self.attendance_rows_frame.pack(fill="both", expand=True, padx=1, pady=1)

        save_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        save_frame.pack(fill="x", pady=20)

        save_btn = self.create_gradient_button(save_frame, "💾  حفظ الحضور والغياب", self.t("ACCENT"),
                                               self.t("ACCENT_HOVER"), self.save_attendance,
                                               width=280, height=52)
        save_btn.pack()

        self.attendance_checkboxes = {}
        self.load_attendance_members()

    def load_attendance_members(self):
        for widget in self.attendance_rows_frame.winfo_children():
            widget.destroy()
        self.attendance_checkboxes = {}

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        query = "SELECT id, name, school_age, family_name FROM members WHERE user_id = ?"
        params = [self.current_user_id]

        age_filter = self.attendance_age_filter.get().strip()
        if age_filter and age_filter != "الكل":
            query += " AND school_age LIKE ?"
            params.append(f"%{age_filter}%")

        c.execute(query, params)
        rows = c.fetchall()

        date_str = self.attendance_date.get().strip()
        c.execute("SELECT member_id, status FROM attendance WHERE date = ? AND user_id = ?", (date_str, self.current_user_id))
        existing = {r[0]: r[1] for r in c.fetchall()}
        conn.close()

        for idx, row in enumerate(rows):
            bg = self.t("CARD_BG") if idx % 2 == 0 else self.t("CARD_BG_ALT")
            row_frame = ctk.CTkFrame(self.attendance_rows_frame, fg_color=bg, height=50, corner_radius=0)
            row_frame.pack(fill="x")
            row_frame.pack_propagate(False)

            member_id = row[0]

            id_lbl = ctk.CTkLabel(row_frame, text=str(member_id), font=("Segoe UI", 12),
                                  text_color=self.t("TEXT_MUTED"), width=55)
            id_lbl.pack(side="right", padx=5)

            name_lbl = ctk.CTkLabel(row_frame, text=row[1], font=("Segoe UI", 13, "bold"),
                                    text_color=self.t("TEXT_PRIMARY"), width=220)
            name_lbl.pack(side="right", padx=5)

            age_lbl = ctk.CTkLabel(row_frame, text=row[2] or "—", font=("Segoe UI", 12),
                                   text_color=self.t("TEXT_SECONDARY"), width=140)
            age_lbl.pack(side="right", padx=5)

            fam_lbl = ctk.CTkLabel(row_frame, text=row[3] or "—", font=("Segoe UI", 12),
                                   text_color=self.t("TEXT_SECONDARY"), width=170)
            fam_lbl.pack(side="right", padx=5)

            status_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=240)
            status_frame.pack(side="right", padx=5)
            status_frame.pack_propagate(False)

            initial_status = existing.get(member_id, None)

            present_btn = ctk.CTkButton(status_frame, text="✅  حاضر", font=("Segoe UI", 11, "bold"),
                                        height=34, width=105, corner_radius=10,
                                        fg_color=self.t("PRESENT_COLOR") if initial_status == "present" else self.t("INPUT_BG"),
                                        hover_color=self.t("PRESENT_COLOR"),
                                        border_width=1 if initial_status == "present" else 0,
                                        border_color=self.t("PRESENT_COLOR"),
                                        text_color="white" if initial_status == "present" else self.t("TEXT_PRIMARY"),
                                        command=lambda mid=member_id: self.set_attendance_status(mid, "present"))
            present_btn.pack(side="right", padx=4)

            absent_btn = ctk.CTkButton(status_frame, text="❌  غائب", font=("Segoe UI", 11, "bold"),
                                       height=34, width=105, corner_radius=10,
                                       fg_color=self.t("ABSENT_COLOR") if initial_status == "absent" else self.t("INPUT_BG"),
                                       hover_color=self.t("ABSENT_COLOR"),
                                       border_width=1 if initial_status == "absent" else 0,
                                       border_color=self.t("ABSENT_COLOR"),
                                       text_color="white" if initial_status == "absent" else self.t("TEXT_PRIMARY"),
                                       command=lambda mid=member_id: self.set_attendance_status(mid, "absent"))
            absent_btn.pack(side="right", padx=4)

            self.attendance_checkboxes[member_id] = {
                "status": initial_status,
                "present_btn": present_btn,
                "absent_btn": absent_btn
            }

    def set_attendance_status(self, member_id, status):
        widgets = self.attendance_checkboxes[member_id]
        widgets["status"] = status

        if status == "present":
            widgets["present_btn"].configure(fg_color=self.t("PRESENT_COLOR"), border_width=1,
                                             border_color=self.t("PRESENT_COLOR"), text_color="white")
            widgets["absent_btn"].configure(fg_color=self.t("INPUT_BG"), border_width=0,
                                            text_color=self.t("TEXT_PRIMARY"))
        else:
            widgets["present_btn"].configure(fg_color=self.t("INPUT_BG"), border_width=0,
                                             text_color=self.t("TEXT_PRIMARY"))
            widgets["absent_btn"].configure(fg_color=self.t("ABSENT_COLOR"), border_width=1,
                                            border_color=self.t("ABSENT_COLOR"), text_color="white")

    def save_attendance(self):
        date_str = self.attendance_date.get().strip()
        if not date_str:
            messagebox.showerror("⚠️ خطأ", "الرجاء إدخال التاريخ!")
            return

        if not self.validate_date(date_str, allow_future=True):
            messagebox.showerror("⚠️ خطأ", "التاريخ غير صحيح! يجب أن يكون بصيغة YYYY-MM-DD.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        saved_count = 0
        for member_id, data in self.attendance_checkboxes.items():
            status = data["status"]
            if status:
                c.execute("DELETE FROM attendance WHERE member_id = ? AND date = ? AND user_id = ?",
                          (member_id, date_str, self.current_user_id))
                c.execute("""
                    INSERT INTO attendance (member_id, date, status, notes, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (member_id, date_str, status, "", self.current_user_id))
                saved_count += 1

        conn.commit()
        conn.close()

        messagebox.showinfo("✅ تم", f"تم حفظ {saved_count} سجل حضور/غياب بنجاح!")


    def show_attendance_history(self):
        self.set_active_menu("history")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(scroll, text="سجل الحضور والغياب", font=("Segoe UI", 26, "bold"),
                              text_color=self.t("TEXT_PRIMARY"), anchor="e")
        header.pack(fill="x", pady=(0, 25), anchor="e")

        filter_card = self.create_card(scroll, "🔍  البحث في السجل")
        filter_frame = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_frame.pack(pady=18, padx=25, fill="x")

        date_lbl = ctk.CTkLabel(filter_frame, text="التاريخ :", font=("Segoe UI", 13),
                                text_color=self.t("TEXT_PRIMARY"), width=90, anchor="e")
        date_lbl.pack(side="right", padx=(0, 12))

        self.history_date = ctk.CTkEntry(filter_frame, font=("Segoe UI", 13), height=45, width=150,
                                         border_color=self.t("CARD_BORDER"), corner_radius=12,
                                         fg_color=self.t("INPUT_BG"))
        self.history_date.pack(side="right", padx=6)

        age_lbl = ctk.CTkLabel(filter_frame, text="السن الدراسي :", font=("Segoe UI", 13),
                               text_color=self.t("TEXT_PRIMARY"), width=130, anchor="e")
        age_lbl.pack(side="right", padx=(35, 12))

        self.history_age_filter = ctk.CTkEntry(filter_frame, placeholder_text="الكل",
                                               font=("Segoe UI", 13), height=45, width=150,
                                               border_color=self.t("CARD_BORDER"), corner_radius=12,
                                               fg_color=self.t("INPUT_BG"))
        self.history_age_filter.pack(side="right", padx=6)

        search_btn = self.create_gradient_button(filter_frame, "🔍  بحث", self.t("PRIMARY"),
                                                 self.t("PRIMARY_HOVER"), self.load_attendance_history,
                                                 width=120, height=45)
        search_btn.pack(side="right", padx=(25, 6))

        self.history_stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.history_stats_frame.pack(fill="x", pady=15)

        table_card = ctk.CTkFrame(scroll, fg_color=self.t("CARD_BG"), corner_radius=16,
                                  border_width=1, border_color=self.t("CARD_BORDER"))
        table_card.pack(fill="both", expand=True, pady=10)

        headers_frame = ctk.CTkFrame(table_card, fg_color=self.t("HEADER_BG"), corner_radius=0, height=45)
        headers_frame.pack(fill="x", padx=1, pady=(1, 0))
        headers_frame.pack_propagate(False)

        headers = ["#", "الاسم", "السن الدراسي", "التاريخ", "الحالة"]
        widths = [55, 220, 140, 160, 160]

        for h, w in zip(headers, widths):
            lbl = ctk.CTkLabel(headers_frame, text=h, font=("Segoe UI", 12, "bold"),
                               text_color="white", width=w)
            lbl.pack(side="right", padx=5)

        self.history_rows_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        self.history_rows_frame.pack(fill="both", expand=True, padx=1, pady=1)

        self.load_attendance_history()

    def load_attendance_history(self):
        for widget in self.history_rows_frame.winfo_children():
            widget.destroy()
        for widget in self.history_stats_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        query = """
            SELECT a.id, m.name, m.school_age, a.date, a.status
            FROM attendance a
            JOIN members m ON a.member_id = m.id
            WHERE a.user_id = ?
        """
        params = [self.current_user_id]

        date_filter = self.history_date.get().strip()
        if date_filter:
            query += " AND a.date = ?"
            params.append(date_filter)

        age_filter = self.history_age_filter.get().strip()
        if age_filter and age_filter != "الكل":
            query += " AND m.school_age LIKE ?"
            params.append(f"%{age_filter}%")

        query += " ORDER BY a.date DESC, m.name"

        c.execute(query, params)
        rows = c.fetchall()

        present_count = sum(1 for r in rows if r[4] == "present")
        absent_count = sum(1 for r in rows if r[4] == "absent")

        stats_data = [
            ("📋  إجمالي السجلات", str(len(rows)), self.t("TEXT_PRIMARY"), self.t("CARD_BG")),
            ("✅  الحاضرين", str(present_count), self.t("PRESENT_COLOR"), self.t("PRESENT_BG")),
            ("❌  الغائبين", str(absent_count), self.t("ABSENT_COLOR"), self.t("ABSENT_BG")),
        ]

        for label, value, color, bg in stats_data:
            card = ctk.CTkFrame(self.history_stats_frame, fg_color=bg, corner_radius=14,
                                border_width=1, border_color=self.t("CARD_BORDER"))
            card.pack(side="right", padx=6, pady=5)

            val_lbl = ctk.CTkLabel(card, text=value, font=("Segoe UI", 22, "bold"), text_color=color)
            val_lbl.pack(pady=(10, 3), padx=20)

            lbl = ctk.CTkLabel(card, text=label, font=("Segoe UI", 11), text_color=self.t("TEXT_SECONDARY"))
            lbl.pack(pady=(3, 10), padx=20)

        for idx, row in enumerate(rows):
            bg = self.t("CARD_BG") if idx % 2 == 0 else self.t("CARD_BG_ALT")
            row_frame = ctk.CTkFrame(self.history_rows_frame, fg_color=bg, height=42, corner_radius=0)
            row_frame.pack(fill="x")
            row_frame.pack_propagate(False)

            values = [str(row[0]), row[1], row[2] or "—", row[3]]
            widths = [55, 220, 140, 160]

            for val, w in zip(values, widths):
                lbl = ctk.CTkLabel(row_frame, text=val, font=("Segoe UI", 11),
                                   text_color=self.t("TEXT_PRIMARY"), width=w)
                lbl.pack(side="right", padx=5)

            status = row[4]
            if status == "present":
                status_text = "✅  حاضر"
                status_color = self.t("PRESENT_COLOR")
                status_bg = self.t("PRESENT_BG")
            else:
                status_text = "❌  غائب"
                status_color = self.t("ABSENT_COLOR")
                status_bg = self.t("ABSENT_BG")

            status_badge = ctk.CTkFrame(row_frame, fg_color=status_bg, corner_radius=8, width=140, height=30)
            status_badge.pack(side="right", padx=5)
            status_badge.pack_propagate(False)

            status_lbl = ctk.CTkLabel(status_badge, text=status_text, font=("Segoe UI", 11, "bold"),
                                      text_color=status_color)
            status_lbl.pack(expand=True)

        conn.close()


    def show_developer(self):
        self.set_active_menu("developer")
        self.clear_content()

        main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)

        card = ctk.CTkFrame(main_frame, fg_color=self.t("CARD_BG"), corner_radius=20,
                            border_width=2, border_color=self.t("PRIMARY"))
        card.pack(pady=40, padx=40, fill="both", expand=True)

        title = ctk.CTkLabel(card, text="👨‍💻  عن المطور", font=("Segoe UI", 28, "bold"),
                             text_color=self.t("TEXT_PRIMARY"))
        title.pack(pady=(40, 20))

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(pady=20, padx=40, fill="x")

        dev_data = [
            ("الاسم", "جاك تامر هنري"),
            ("الكنيسة", "مارجرجس و الانبا انطونيوس محرم بك"),
            ("رقم الهاتف", "01211679629"),
        ]

        for label, value in dev_data:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=10)

            lbl = ctk.CTkLabel(row, text=label + " :", font=("Segoe UI", 16, "bold"),
                               text_color=self.t("TEXT_PRIMARY"), width=150, anchor="e")
            lbl.pack(side="right", padx=(0, 20))

            val_lbl = ctk.CTkLabel(row, text=value, font=("Segoe UI", 16),
                                   text_color=self.t("TEXT_SECONDARY"), anchor="w")
            val_lbl.pack(side="right", fill="x", expand=True)

        icon_lbl = ctk.CTkLabel(card, text="✝", font=("Segoe UI", 48), text_color=self.t("PRIMARY"))
        icon_lbl.pack(pady=20)

# ============================================
# Run Application
# ============================================
if __name__ == "__main__":
    init_db()
    app = ChurchApp()
    app.mainloop()