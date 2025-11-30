import flet as ft
import threading
import time
from services.email_manager import EmailManager
from services.llm_brain import analyze_email
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
        
        # --- MEMORY (The "Agent" Upgrade) ---
        self.log_history = [] 
        self.cached_analyses = [] # <--- STORES THE LAST RESULTS

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

        # --- Layout ---
        self.content_area = ft.Container(
            content=self.dashboard_view,
            expand=True,
            padding=30,
            bgcolor=ft.Colors.BLUE_GREY_50 
        )

        self.page.add(ft.Row([ft.Container(self.sidebar, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200)), self.content_area], expand=True, spacing=0))
        self.page.run_task(self.initial_greeting)

    def setup_page(self):
        self.page.title = "Murf Falcon Agent"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 1100
        self.page.window_height = 850
        self.page.bgcolor = ft.Colors.BLUE_GREY_50
        self.page.padding = 0

    # ==========================
    # 1. VIEW BUILDERS
    # ==========================
    def build_dashboard(self):
        self.status_ring = ft.Container(width=12, height=12, border_radius=12, bgcolor=ft.Colors.RED_400, animate=ft.Animation(500, ft.AnimationCurve.BOUNCE_OUT))
        self.status_text = ft.Text("OFFLINE", size=12, weight="bold", color=ft.Colors.GREY_500)

        self.mic_icon = ft.Icon(name=ft.Icons.MIC_NONE, size=40, color=ft.Colors.WHITE)
        self.mic_btn = ft.Container(
            content=self.mic_icon, width=90, height=90, border_radius=45,
            gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=[ft.Colors.BLUE_400, ft.Colors.INDIGO_500]),
            alignment=ft.alignment.center, on_click=self.toggle_recording, on_hover=self.animate_hover,
            animate_scale=ft.Animation(100, ft.AnimationCurve.EASE_OUT), animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLUE_200, spread_radius=5)
        )
        
        self.visualizer = ft.Container(width=90, height=90, border_radius=45, bgcolor=ft.Colors.BLUE_100, opacity=0, animate_opacity=300, animate_scale=500)
        self.mini_log_list = ft.ListView(expand=True, spacing=15, auto_scroll=True)
        
        return ft.Column([
            ft.Row([
                ft.Column([ft.Text("Welcome back, Manager", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.Text("Voice Operations Center", size=14, color=ft.Colors.GREY_500)]),
                ft.Container(expand=True),
                ft.Container(content=ft.Row([self.status_ring, self.status_text], spacing=10), padding=ft.padding.symmetric(horizontal=15, vertical=8), bgcolor=ft.Colors.WHITE, border_radius=20, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200))
            ]),
            ft.Container(height=20),
            ft.Container(content=ft.Column([ft.Text("RECENT INSIGHTS", size=11, weight="bold", color=ft.Colors.GREY_600), ft.Container(content=self.mini_log_list, expand=True, padding=10)]), expand=True, bgcolor=ft.Colors.WHITE, border_radius=25, padding=20, shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.GREY_200, offset=ft.Offset(0, 5))),
            ft.Container(height=30),
            ft.Container(height=180, content=ft.Column([ft.Stack([ft.Container(self.visualizer, alignment=ft.alignment.center), ft.Container(self.mic_btn, alignment=ft.alignment.center)], alignment=ft.alignment.center), ft.Container(height=15), ft.Text("Tap to Speak", size=13, weight="bold", color=ft.Colors.GREY_400)], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        ])

    def build_logs_page(self):
        self.full_log_list = ft.ListView(expand=True, spacing=10)
        return ft.Column([ft.Text("System Logs", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.Container(height=10), ft.Container(content=self.full_log_list, expand=True, bgcolor=ft.Colors.WHITE, border_radius=20, padding=20, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200))])

    def build_settings_page(self):
        return ft.Column([
            ft.Text("Configuration", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.Container(height=20),
            ft.Container(bgcolor=ft.Colors.WHITE, padding=25, border_radius=20, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200), content=ft.Column([ft.Row([ft.Icon(ft.Icons.RECORD_VOICE_OVER, color=ft.Colors.INDIGO), ft.Text("Voice Engine", weight="bold", size=16)]), ft.Divider(height=20, color=ft.Colors.TRANSPARENT), ft.Dropdown(label="Murf Voice ID", value="en-US-natalie", options=[ft.dropdown.Option("en-US-natalie"), ft.dropdown.Option("en-US-falcon-male"), ft.dropdown.Option("hi-IN-namrita")], border_radius=10, border_color=ft.Colors.GREY_300, focused_border_color=ft.Colors.INDIGO), ft.Slider(min=0, max=100, divisions=10, value=80, label="Speed: {value}%", active_color=ft.Colors.INDIGO)])),
            ft.Container(height=20),
            ft.Container(bgcolor=ft.Colors.WHITE, padding=25, border_radius=20, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_200), content=ft.Column([ft.Row([ft.Icon(ft.Icons.SECURITY, color=ft.Colors.TEAL), ft.Text("API Connections", weight="bold", size=16)]), ft.Divider(height=20, color=ft.Colors.TRANSPARENT), ft.TextField(label="Murf API Key", value="••••••••••••••••", password=True, disabled=True, border_radius=10, border_color=ft.Colors.GREY_300), ft.TextField(label="AssemblyAI Key", value="••••••••••••••••", password=True, disabled=True, border_radius=10, border_color=ft.Colors.GREY_300)]))
        ], scroll=ft.ScrollMode.AUTO)

    # ==========================
    # 2. LOGIC & EVENTS
    # ==========================
    def animate_hover(self, e):
        e.control.scale = 1.1 if e.data == "true" else 1.0
        e.control.update()

    def switch_tab(self, e):
        index = e.control.selected_index
        if index == 0: self.content_area.content = self.dashboard_view
        elif index == 1: self.refresh_full_logs(); self.content_area.content = self.logs_view
        elif index == 2: self.content_area.content = self.settings_view
        self.page.update()

    async def initial_greeting(self):
        self.add_log_entry("System initialized.", "System")
        self.set_status("READY", ft.Colors.GREEN_500)
        self.voice.speak("System ready.")

    def toggle_recording(self, e):
        if not self.is_recording:
            self.is_recording = True
            self.mic_icon.name = ft.Icons.STOP
            self.mic_btn.gradient = ft.LinearGradient(colors=[ft.Colors.RED_500, ft.Colors.PINK_600])
            self.mic_btn.shadow.color = ft.Colors.RED_200
            self.visualizer.opacity = 0.4; self.visualizer.scale = 1.6; self.visualizer.bgcolor = ft.Colors.RED_100
            self.set_status("LISTENING", ft.Colors.RED_500)
            self.ears.start_recording()
        else:
            self.is_recording = False
            self.mic_icon.name = ft.Icons.MIC_NONE
            self.mic_btn.gradient = ft.LinearGradient(colors=[ft.Colors.BLUE_400, ft.Colors.INDIGO_500])
            self.mic_btn.shadow.color = ft.Colors.BLUE_200
            self.visualizer.opacity = 0; self.visualizer.scale = 1.0
            self.set_status("PROCESSING", ft.Colors.ORANGE_400)
            self.page.update()
            threading.Thread(target=self.process_recording, daemon=True).start()
        self.page.update()

    def process_recording(self):
        transcript = self.ears.stop_recording()
        if not transcript:
            self.set_status("READY", ft.Colors.GREEN_500)
            return

        self.add_log_entry(f"{transcript}", "User", ft.Colors.GREY_700)
        self.set_status("THINKING", ft.Colors.PURPLE_300)
        
        intent_data = determine_intent(transcript)
        action = intent_data.action
        self.add_log_entry(f"Intent: {action}", "System", ft.Colors.BLUE_GREY_400)

        # --- INTELLIGENT ROUTING ---
        if action == "ANALYZE_NEW":
            # New Request: Fetch new data (use_cache=False)
            self.run_analysis_workflow(use_cache=False)
            
        elif action == "GET_SENTIMENT_STATS":
            self.run_sentiment_report()
            
        elif action == "SUMMARIZE_HINDI":
            # Smart Request: Use existing memory (use_cache=True)
            if not self.cached_analyses:
                self.voice.speak("Mere paas koi purana data nahi hai. Pehle 'Start Analysis' kahein.", language_code="hi")
            else:
                self.voice.speak("Thik hai. Main pichli report Hindi mein batata hoon.", language_code="hi")
                self.run_analysis_workflow(language="hi", use_cache=True)
        
        elif action == "FILTER_BY_CATEGORY":
             # Smart Request: Filter NEW data (or you could filter cached if you prefer)
             self.voice.speak(f"Looking for emails about {intent_data.keywords}.")
             self.run_analysis_workflow(filter_keyword=intent_data.keywords, use_cache=False)

        elif action == "EXIT":
            self.voice.speak("Goodbye.")
            self.page.window_close()
        else:
            self.voice.speak("I am not sure what you mean.")
            self.set_status("READY", ft.Colors.GREEN_500)

    # --- THE CORE WORKFLOW (NOW WITH MEMORY) ---
    def run_analysis_workflow(self, language="en", filter_keyword=None, use_cache=False):
        self.set_status("ANALYZING", ft.Colors.PURPLE_500)
        
        # 1. Decide Source: Cache vs Fresh
        if use_cache and self.cached_analyses:
            # MEMORY MODE
            analyses = self.cached_analyses
            self.add_log_entry("Using cached data from memory.", "System", ft.Colors.BLUE_GREY_400)
        else:
            # FRESH MODE
            if not filter_keyword and language == "en":
                self.voice.speak("Scanning inbox.")
            
            try:
                email_bot = EmailManager()
                fetch_count = 10 if filter_keyword else 5
                emails = email_bot.fetch_recent_emails(count=fetch_count)
                
                if not emails:
                    msg = "No new emails." if language == "en" else "Koi naye email nahi hain."
                    self.voice.speak(msg, language_code=language)
                    self.set_status("READY", ft.Colors.GREEN_500)
                    return

                # Perform Fresh Analysis
                analyses = []
                for mail in emails:
                    full_text = f"Subject: {mail['subject']}\nFrom: {mail['sender']}\nContent: {mail['snippet']}"
                    analysis_result = analyze_email(full_text)
                    # We store the 'mail' object too if needed, but for now just the result
                    analyses.append(analysis_result)
                    
                    # Log to sheets only on fresh run
                    email_bot.log_to_sheet(analysis_result)

                # UPDATE MEMORY
                self.cached_analyses = analyses
                
            except Exception as e:
                self.add_log_entry(f"Error: {e}", "System", ft.Colors.RED)
                self.voice.speak("An error occurred.")
                self.set_status("READY", ft.Colors.GREEN_500)
                return

        # 2. Process Results (Works for both Fresh and Cached)
        negative_count = 0
        summaries_to_speak = []
        matched_count = 0

        for analysis in analyses:
            # Filter Logic
            if filter_keyword:
                search_blob = f"{analysis.category} {analysis.summary}".lower()
                if filter_keyword.lower() not in search_blob:
                    continue 

            matched_count += 1
            
            # UI Card
            color = ft.Colors.RED_50 if analysis.sentiment == "Negative" else ft.Colors.GREEN_50
            border = ft.Colors.RED_200 if analysis.sentiment == "Negative" else ft.Colors.GREEN_200
            icon_c = ft.Colors.RED_400 if analysis.sentiment == "Negative" else ft.Colors.GREEN_400
            
            # Only add cards if we are doing a fresh run OR if it's a specific filter request
            # (To avoid spamming UI on every language switch)
            if not use_cache or filter_keyword:
                card_body = f"{analysis.summary}\n\n💡 Action: {analysis.recommendation}\n🎭 Tone: {analysis.tone}"
                self.add_log_card(analysis.customer_name, analysis.sentiment, card_body, color, border, icon_c)

            # Speech Logic
            spoken_text = f"From {analysis.customer_name}: {analysis.summary}. Recommendation: {analysis.recommendation}"

            if filter_keyword:
                summaries_to_speak.append(spoken_text)
            else:
                if analysis.sentiment == "Negative":
                    negative_count += 1
                    summaries_to_speak.append(spoken_text)

        # 3. Final Report
        if filter_keyword:
            if matched_count == 0:
                self.voice.speak(f"I checked memory, but none were about {filter_keyword}.")
            else:
                self.voice.speak(f"I found {matched_count} emails regarding {filter_keyword}.")
                for s in summaries_to_speak:
                    self.voice.speak(s)
                    time.sleep(0.5)
        else:
            if language == "hi":
                self.voice.speak(f"Mujhe {negative_count} negative emails mile hain.", language_code="hi")
                if negative_count > 0:
                    self.voice.speak("Kripya turant check karein.", language_code="hi")
            else:
                if negative_count > 0:
                    self.voice.speak(f"Alert. Found {negative_count} negative reviews.")
                    for s in summaries_to_speak:
                        self.voice.speak(s)
                        time.sleep(0.5)
                else:
                    self.voice.speak("All recent feedback is positive.")
        
        self.set_status("READY", ft.Colors.GREEN_500)

    def run_sentiment_report(self):
        # Use Cache if available!
        if self.cached_analyses:
            source = self.cached_analyses
            self.add_log_entry("Generating stats from memory...", "System", ft.Colors.PURPLE_300)
        else:
            self.voice.speak("I need to scan emails first. Say 'Start Analysis'.")
            return

        pos, neg, neu = 0, 0, 0
        for a in source:
            if a.sentiment == "Negative": neg += 1
            elif a.sentiment == "Positive": pos += 1
            else: neu += 1
        
        report = f"In the current session: {pos} positive, {neg} negative, {neu} neutral."
        self.voice.speak(report)
        self.set_status("READY", ft.Colors.GREEN_500)

    # --- UI HELPERS ---
    def set_status(self, text, color):
        self.status_text.value = text; self.status_text.color = color; self.status_ring.bgcolor = color; self.page.update()
    def add_log_entry(self, message, sender, color=ft.Colors.GREY_800):
        self.mini_log_list.controls.append(ft.Text(f"{sender}: {message}", color=color, font_family="Roboto", size=13))
        self.log_history.append({"msg": message, "sender": sender, "color": color, "type": "text"})
        self.page.update()
    def add_log_card(self, title, sentiment, body, bg_color, border_color, icon_color):
        card = ft.Container(content=ft.Column([ft.Row([ft.Icon(ft.Icons.PERSON, size=18, color=icon_color), ft.Text(title, weight="bold", color=ft.Colors.GREY_900), ft.Container(expand=True), ft.Container(content=ft.Text(sentiment, size=10, color=icon_color, weight="bold"), bgcolor=ft.Colors.WHITE, padding=5, border_radius=5)]), ft.Container(height=5), ft.Text(body, size=13, color=ft.Colors.GREY_700)]), bgcolor=bg_color, padding=15, border_radius=15, border=ft.border.all(1, border_color))
        self.mini_log_list.controls.append(card)
        self.log_history.append({"type": "card", "title": title, "sentiment": sentiment, "body": body, "bg_color": bg_color, "border_color": border_color, "icon_color": icon_color})
        self.page.update()
    def refresh_full_logs(self):
        self.full_log_list.controls.clear()
        for item in self.log_history:
            if item["type"] == "text": self.full_log_list.controls.append(ft.Text(f"{item['sender']}: {item['msg']}", color=item['color']))
            elif item["type"] == "card": self.full_log_list.controls.append(ft.Container(content=ft.Column([ft.Row([ft.Text(f"{item['title']} ({item['sentiment']})", weight="bold", color=item['icon_color'])]), ft.Text(item['body'], size=12, color=ft.Colors.GREY_700)]), bgcolor=item['bg_color'], padding=10, border_radius=10, margin=ft.margin.only(bottom=5), border=ft.border.all(1, item['border_color'])))
        self.page.update()

def main(page: ft.Page): ModernLightApp(page)
if __name__ == "__main__": ft.app(target=main)