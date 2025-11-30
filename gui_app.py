import flet as ft
import threading
import time
import re
from services.email_manager import EmailManager
from services.llm_brain import analyze_email, generate_email_reply, translate_to_hindi
from services.murf_tts import VoiceEngine
from services.transcriber import Transcriber
from services.intent_router import determine_intent

class ModernLightApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        
        # --- Backend Services ---
        self.voice = VoiceEngine()
        self.ears = Transcriber()
        self.is_recording = False
        
        # --- MEMORY ---
        self.log_history = [] 
        self.cached_analyses = [] 

        # --- DYNAMIC UI COMPONENTS ---
        self.col_positive = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.col_neutral = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.col_negative = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.middle_content_area = ft.Container(expand=True)

        # --- Build Views ---
        self.dashboard_view = self.build_dashboard()
        self.logs_view = self.build_logs_page()
        self.settings_view = self.build_settings_page()

        # --- Sidebar ---
        self.sidebar = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            bgcolor=ft.Colors.WHITE,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD_ROUNDED, label="Dashboard"),
                ft.NavigationRailDestination(icon=ft.Icons.RECEIPT_LONG_OUTLINED, selected_icon=ft.Icons.RECEIPT_LONG_ROUNDED, label="Logs"),
                ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS_ROUNDED, label="Settings"),
            ],
            on_change=self.switch_tab,
        )

        self.content_area = ft.Container(content=self.dashboard_view, expand=True, padding=30, bgcolor=ft.Colors.BLUE_GREY_50)
        self.page.add(ft.Row([ft.Container(self.sidebar, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200)), self.content_area], expand=True, spacing=0))
        
        self.show_empty_state()
        self.page.run_task(self.initial_greeting)

    def setup_page(self):
        self.page.title = "Murf Falcon Agent"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 1200
        self.page.window_height = 850
        self.page.bgcolor = ft.Colors.BLUE_GREY_50
        self.page.padding = 0
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Action Completed"), action="OK")

    # ==========================
    # 1. VIEW BUILDERS
    # ==========================
    def build_dashboard(self):
        self.status_ring = ft.Container(width=12, height=12, border_radius=12, bgcolor=ft.Colors.RED_400, animate=ft.Animation(500, ft.AnimationCurve.BOUNCE_OUT))
        self.status_text = ft.Text("OFFLINE", size=12, weight="bold", color=ft.Colors.GREY_500)

        self.mic_icon = ft.Icon(name=ft.Icons.MIC_NONE, size=40, color=ft.Colors.WHITE)
        self.mic_btn = ft.Container(
            content=self.mic_icon, width=90, height=90, border_radius=45,
            gradient=ft.LinearGradient(colors=[ft.Colors.BLUE_400, ft.Colors.INDIGO_500]),
            alignment=ft.alignment.center, on_click=self.toggle_recording, on_hover=self.animate_hover,
            animate_scale=ft.Animation(100, ft.AnimationCurve.EASE_OUT), animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLUE_200, spread_radius=5)
        )
        self.visualizer = ft.Container(width=90, height=90, border_radius=45, bgcolor=ft.Colors.BLUE_100, opacity=0, animate_opacity=300, animate_scale=500)

        return ft.Column([
            ft.Row([
                ft.Column([ft.Text("Welcome back, Manager", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.Text("Voice Operations Center", size=14, color=ft.Colors.GREY_500)]),
                ft.Container(expand=True),
                ft.Container(content=ft.Row([self.status_ring, self.status_text], spacing=10), padding=ft.padding.symmetric(horizontal=15, vertical=8), bgcolor=ft.Colors.WHITE, border_radius=20, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200))
            ]),
            ft.Container(height=20),
            self.middle_content_area,
            ft.Container(height=20),
            ft.Container(height=160, content=ft.Column([ft.Stack([ft.Container(self.visualizer, alignment=ft.alignment.center), ft.Container(self.mic_btn, alignment=ft.alignment.center)], alignment=ft.alignment.center), ft.Container(height=15), ft.Text("Tap to Speak", size=13, weight="bold", color=ft.Colors.GREY_400)], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        ])

    def show_empty_state(self):
        content = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=80, color=ft.Colors.GREY_300),
                ft.Text("Nothing analyzed yet.", size=20, weight="bold", color=ft.Colors.GREY_400),
                ft.Text("Say 'Start Analysis' to begin.", size=14, color=ft.Colors.GREY_400),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center, expand=True, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200)
        )
        self.middle_content_area.content = content
        self.page.update()

    def show_loading_state(self):
        content = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=60, height=60, stroke_width=5, color=ft.Colors.INDIGO_500),
                ft.Container(height=20),
                ft.Text("Analyzing Inbox...", size=18, weight="bold", color=ft.Colors.INDIGO_500),
                ft.Text("Connecting to Gemini & Gmail...", size=12, color=ft.Colors.GREY_500),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center, expand=True, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200)
        )
        self.middle_content_area.content = content
        self.page.update()

    def show_results_state(self):
        content = ft.Container(
            content=ft.Row([
                self.build_column_container("Positive", ft.Colors.GREEN_500, self.col_positive),
                self.build_column_container("Neutral", ft.Colors.BLUE_GREY_400, self.col_neutral),
                self.build_column_container("Negative", ft.Colors.RED_500, self.col_negative),
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True),
            expand=True
        )
        self.middle_content_area.content = content
        self.page.update()

    def build_column_container(self, title, color, col_control):
        return ft.Container(
            content=ft.Column([
                ft.Container(content=ft.Row([ft.Icon(ft.Icons.CIRCLE, size=10, color=color), ft.Text(title, weight="bold", color=ft.Colors.GREY_800)]), padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.GREY_200))),
                ft.Container(content=col_control, padding=10, expand=True)
            ]),
            expand=True, bgcolor=ft.Colors.WHITE, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200)
        )

    def build_logs_page(self):
        self.full_log_list = ft.ListView(expand=True, spacing=10)
        return ft.Column([ft.Text("System Logs", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.Container(height=10), ft.Container(content=self.full_log_list, expand=True, bgcolor=ft.Colors.WHITE, border_radius=20, padding=20, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200))])

    def build_settings_page(self):
        return ft.Column([
            ft.Text("Configuration", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900),
            ft.Container(height=20),
            ft.Container(
                bgcolor=ft.Colors.WHITE, padding=25, border_radius=20,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200),
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.RECORD_VOICE_OVER, color=ft.Colors.INDIGO), ft.Text("Voice Engine", weight="bold", size=16)]),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Dropdown(
                        label="Murf Voice ID",
                        value="en-US-natalie",
                        options=[ft.dropdown.Option("en-US-natalie"), ft.dropdown.Option("en-US-falcon-male"), ft.dropdown.Option("hi-IN-namrita")],
                        border_radius=10, border_color=ft.Colors.GREY_300, focused_border_color=ft.Colors.INDIGO
                    ),
                    ft.Slider(min=0, max=100, divisions=10, value=80, label="Speed: {value}%", active_color=ft.Colors.INDIGO),
                ])
            ),
            ft.Container(height=20),
            ft.Container(
                bgcolor=ft.Colors.WHITE, padding=25, border_radius=20,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200),
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.SECURITY, color=ft.Colors.TEAL), ft.Text("API Connections", weight="bold", size=16)]),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.TextField(label="Murf API Key", value="••••••••••••••••", password=True, disabled=True, border_radius=10, border_color=ft.Colors.GREY_300),
                    ft.TextField(label="AssemblyAI Key", value="••••••••••••••••", password=True, disabled=True, border_radius=10, border_color=ft.Colors.GREY_300),
                ])
            )
        ], scroll=ft.ScrollMode.AUTO)

    # ==========================
    # 2. LOGIC & EVENTS
    # ==========================
    def animate_hover(self, e): e.control.scale = 1.1 if e.data == "true" else 1.0; e.control.update()
    def switch_tab(self, e):
        if e.control.selected_index == 0: self.content_area.content = self.dashboard_view
        elif e.control.selected_index == 1: self.refresh_full_logs(); self.content_area.content = self.logs_view
        elif e.control.selected_index == 2: self.content_area.content = self.settings_view
        self.page.update()
    
    async def initial_greeting(self):
        self.speak_system("System ready.")
        self.set_status("READY", ft.Colors.GREEN_500)

    def toggle_recording(self, e):
        if not self.is_recording:
            self.is_recording = True; self.mic_icon.name = ft.Icons.STOP; self.mic_btn.gradient = ft.LinearGradient(colors=[ft.Colors.RED_500, ft.Colors.PINK_600])
            self.visualizer.opacity = 0.4; self.visualizer.scale = 1.6; self.visualizer.bgcolor = ft.Colors.RED_100
            self.set_status("LISTENING", ft.Colors.RED_500); self.ears.start_recording()
        else:
            self.is_recording = False; self.mic_icon.name = ft.Icons.MIC_NONE; self.mic_btn.gradient = ft.LinearGradient(colors=[ft.Colors.BLUE_400, ft.Colors.INDIGO_500])
            self.visualizer.opacity = 0; self.visualizer.scale = 1.0
            self.set_status("PROCESSING", ft.Colors.ORANGE_400); self.page.update()
            threading.Thread(target=self.process_recording, daemon=True).start()
        self.page.update()

    def speak_system(self, text, language_code="en"):
        self.add_log_entry(text, "System", ft.Colors.INDIGO_400)
        self.voice.speak(text, language_code=language_code)

    def parse_number_word(self, text):
        text = text.lower()
        word_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
        digits = re.findall(r'\d+', text)
        if digits: return int(digits[0])
        for word, num in word_map.items():
            if word in text: return num
        return None

    def process_recording(self):
        time.sleep(0.5)
        transcript = self.ears.stop_recording()
        if not transcript: self.set_status("READY", ft.Colors.GREEN_500); return
        self.add_log_entry(f"{transcript}", "User", ft.Colors.GREY_700)
        self.set_status("THINKING", ft.Colors.PURPLE_300)
        
        intent_data = determine_intent(transcript)
        action = intent_data.action; lang = intent_data.language
        self.add_log_entry(f"Action: {action} | Lang: {lang} | Key: {intent_data.keywords}", "Intent", ft.Colors.BLUE_GREY_400)

        if action == "ANALYZE_NEW":
            if lang == "hi": self.speak_system("Thik hai. Inbox scan kar raha hoon.", language_code="hi")
            else: self.speak_system("Sure, scanning your inbox now.")
            self.run_analysis_workflow(use_cache=False, language=lang)
            
        # --- CHANGED: Renamed Action ---
        elif action == "SUMMARIZE_SPECIFIC":
            target = intent_data.keywords
            if target and target.lower() != "none":
                # Calls the generic explainer (which handles English OR Hindi internally)
                self.explain_specific_email(target, language=lang)
            else:
                self.speak_system("Which email?", language_code=lang)
                
        elif action == "GET_SENTIMENT_STATS": self.run_sentiment_report()
        elif action == "FILTER_BY_CATEGORY": self.run_analysis_workflow(filter_keyword=intent_data.keywords, use_cache=False)
        elif action == "DRAFT_REPLY": self.run_drafting_workflow(intent_data.keywords)
        elif action == "EXIT":
            self.speak_system("Goodbye.")
            self.page.window.destroy()
        else: self.speak_system("I didn't understand."); self.set_status("READY", ft.Colors.GREEN_500)

    # --- CORE WORKFLOW ---
    def run_analysis_workflow(self, language="en", filter_keyword=None, use_cache=False):
        self.set_status("ANALYZING", ft.Colors.PURPLE_500)
        
        if not use_cache: self.show_loading_state()
        self.col_positive.controls.clear(); self.col_neutral.controls.clear(); self.col_negative.controls.clear()
        
        if use_cache and self.cached_analyses:
            analyses_data = self.cached_analyses
        else:
            try:
                email_bot = EmailManager()
                emails = email_bot.fetch_recent_emails(count=6)
                if not emails:
                    self.speak_system("No emails found.", language_code=language)
                    self.show_empty_state(); self.set_status("READY", ft.Colors.GREEN_500); return
                
                analyses_data = []
                for i, mail in enumerate(emails):
                    full_text = f"Subject: {mail['subject']}\nFrom: {mail['sender']}\nContent: {mail['snippet']}"
                    analysis_result = analyze_email(full_text)
                    email_bot.log_to_sheet(analysis_result)
                    analyses_data.append({'id': i+1, 'data': analysis_result})
                self.cached_analyses = analyses_data
            except Exception as e:
                self.speak_system("Error occurred."); print(e); self.show_empty_state(); return

        self.show_results_state() 
        for item in analyses_data:
            if filter_keyword and filter_keyword.lower() not in (item['data'].category + item['data'].summary).lower(): continue 
            self.add_dashboard_card(item['id'], item['data'])
        self.page.update()

        negative_count = 0
        summaries = []
        for item in analyses_data:
            analysis = item['data']
            if filter_keyword and filter_keyword.lower() not in (analysis.category + analysis.summary).lower(): continue 

            text = f"Email {item['id']} from {analysis.customer_name}: {analysis.summary}. Recommendation: {analysis.recommendation}"
            if filter_keyword: summaries.append(text)
            elif analysis.sentiment == "Negative": negative_count += 1; summaries.append(text)

        if language == "hi":
             self.speak_system(f"Mujhe {negative_count} negative emails mile hain.", language_code="hi")
             # --- HINDI LOOP ---
             for item in analyses_data:
                 if item['data'].sentiment == "Negative":
                     details = f"{item['data'].summary}. Recommendation: {item['data'].recommendation}"
                     hindi_details = translate_to_hindi(details)
                     self.speak_system(f"Email {item['id']}: {hindi_details}", language_code="hi")
        else:
            if summaries:
                self.speak_system(f"Analysis complete.")
                for s in summaries: self.voice.speak(s); time.sleep(0.5)
            else:
                self.speak_system("All recent feedback is positive.")
        
        self.set_status("READY", ft.Colors.GREEN_500)

    # --- HELPERS (Renamed to be generic) ---
    def explain_specific_email(self, target_keyword, language="en"):
        self.set_status("ANALYZING", ft.Colors.ORANGE_400)
        target_id = self.parse_number_word(target_keyword)
        target_item = None
        if target_id:
            for item in self.cached_analyses:
                if item['id'] == target_id: target_item = item; break
        else:
             for item in self.cached_analyses:
                if target_keyword.lower() in item['data'].customer_name.lower(): target_item = item; break

        if not target_item:
            msg = f"Email {target_keyword} nahi mila." if language == "hi" else f"I couldn't find email {target_keyword}."
            self.speak_system(msg, language_code=language)
            self.set_status("READY", ft.Colors.GREEN_500)
            return

        # Prepare Text
        summary_text = f"Email {target_item['id']} from {target_item['data'].customer_name}. {target_item['data'].summary}"
        
        # Translate if needed
        if language == "hi":
            self.set_status("TRANSLATING", ft.Colors.ORANGE_400)
            summary_text = translate_to_hindi(summary_text)
        
        self.speak_system(summary_text, language_code=language)
        self.set_status("READY", ft.Colors.GREEN_500)

    def run_drafting_workflow(self, target_keyword):
        self.set_status("DRAFTING", ft.Colors.ORANGE_500)
        target_id = self.parse_number_word(target_keyword)
        target_item = None
        
        if target_id:
            self.speak_system(f"Drafting for email #{target_id}...")
            for item in self.cached_analyses:
                if item['id'] == target_id: target_item = item; break
        else:
            self.speak_system(f"Drafting for {target_keyword}...")
            for item in self.cached_analyses:
                if target_keyword.lower() in item['data'].customer_name.lower(): target_item = item; break
        
        if not target_item: self.speak_system(f"I couldn't find that email."); self.set_status("READY", ft.Colors.GREEN_500); return

        analysis = target_item['data']
        reply_body = generate_email_reply(analysis.customer_name, analysis.summary, analysis.sentiment)
        email_bot = EmailManager()
        success = email_bot.create_draft(to_email="customer@example.com", subject=f"Re: Support (Ref #{target_item['id']})", body_text=reply_body)
        
        if success:
            self.speak_system(f"Draft created successfully.")
            self.page.snack_bar.open = True; self.page.update()
        else: self.speak_system("Failed to create draft.")
        self.set_status("READY", ft.Colors.GREEN_500)

    def run_sentiment_report(self):
        if self.cached_analyses:
            source = self.cached_analyses
            self.add_log_entry("Generating stats...", "System", ft.Colors.PURPLE_300)
        else: self.speak_system("Please scan emails first."); return

        pos, neg, neu = 0, 0, 0
        for item in source:
            a = item['data']
            if a.sentiment == "Negative": neg += 1
            elif a.sentiment == "Positive": pos += 1
            else: neu += 1
        self.speak_system(f"Session Stats: {pos} positive, {neg} negative, {neu} neutral."); self.set_status("READY", ft.Colors.GREEN_500)

    def add_dashboard_card(self, ID, analysis):
        if analysis.sentiment == "Positive": bg = ft.Colors.GREEN_50; border = ft.Colors.GREEN_200; icon = ft.Colors.GREEN_600; col_ref = self.col_positive
        elif analysis.sentiment == "Negative": bg = ft.Colors.RED_50; border = ft.Colors.RED_200; icon = ft.Colors.RED_600; col_ref = self.col_negative
        else: bg = ft.Colors.BLUE_50; border = ft.Colors.BLUE_200; icon = ft.Colors.BLUE_600; col_ref = self.col_neutral

        card = ft.Container(content=ft.Column([ft.Row([ft.Container(content=ft.Text(f"#{ID}", weight="bold", color=ft.Colors.WHITE, size=10), bgcolor=icon, padding=5, border_radius=5), ft.Text(analysis.customer_name, weight="bold", color=ft.Colors.GREY_800, size=12, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)]), ft.Container(height=5), ft.Text(analysis.summary, size=11, color=ft.Colors.GREY_700), ft.Divider(height=10, color=ft.Colors.TRANSPARENT), ft.Row([ft.Icon(ft.Icons.PSYCHOLOGY, size=12, color=ft.Colors.GREY_500), ft.Text(f"Tone: {analysis.tone}", size=10, color=ft.Colors.GREY_500)])]), bgcolor=bg, padding=10, border_radius=10, border=ft.border.all(1, border), animate_opacity=300)
        col_ref.controls.append(card)
    
    def set_status(self, text, color): self.status_text.value = text; self.status_text.color = color; self.status_ring.bgcolor = color; self.page.update()
    def add_log_entry(self, message, sender, color=ft.Colors.GREY_800):
        self.log_history.append({"msg": message, "sender": sender, "color": color, "type": "text"})
        if self.content_area.content == self.logs_view: self.refresh_full_logs()
    def refresh_full_logs(self):
        self.full_log_list.controls.clear()
        for item in self.log_history:
            if item["type"] == "text": self.full_log_list.controls.append(ft.Text(f"{item['sender']}: {item['msg']}", color=item['color']))
        self.page.update()

def main(page: ft.Page): ModernLightApp(page)
if __name__ == "__main__": ft.app(target=main)