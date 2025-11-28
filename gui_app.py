import flet as ft
import threading
import time
from services.email_manager import EmailManager
from services.llm_brain import analyze_email
from services.murf_tts import VoiceEngine
from services.transcriber import Transcriber

class ModernVoiceApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        
        # Services
        self.voice = VoiceEngine()
        self.ears = Transcriber()
        self.is_recording = False

        # --- UI ELEMENTS ---
        self.build_sidebar()
        self.build_main_area()
        
        # Add to page
        self.page.add(
            ft.Row(
                [
                    self.sidebar,
                    ft.VerticalDivider(width=1, color=ft.Colors.WHITE10),
                    self.main_area
                ],
                expand=True
            )
        )
        
        # Initial greeting (delayed so UI loads first)
        self.page.run_task(self.initial_greeting)

    def setup_page(self):
        self.page.title = "Murf Falcon Agent"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.window_width = 1000
        self.page.window_height = 800
        self.page.bgcolor = "#111111" # Deep dark background

    def build_sidebar(self):
        self.sidebar = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_ROUNDED, 
                    selected_icon=ft.Icons.DASHBOARD_OUTLINED, 
                    label="Dashboard"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.MAIL_OUTLINE, 
                    selected_icon=ft.Icons.MAIL, 
                    label="Logs"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED, 
                    selected_icon=ft.Icons.SETTINGS, 
                    label="Settings"
                ),
            ],
            on_change=lambda e: print("Tab changed"),
        )

    def build_main_area(self):
        # 1. Status Indicator (The "Brain" Pulse)
        self.status_ring = ft.Container(
            width=20, height=20, border_radius=10, bgcolor=ft.Colors.RED_500,
            animate=ft.Animation(500, ft.AnimationCurve.BOUNCE_OUT)
        )
        self.status_text = ft.Text("OFFLINE", size=12, weight="bold", color=ft.Colors.RED_200)

        # 2. The Log Window (Modern Cards)
        self.log_list = ft.ListView(expand=True, spacing=15, padding=20, auto_scroll=True)
        
        # 3. The Big Mic Button
        self.mic_icon = ft.Icon(name=ft.Icons.MIC_NONE, size=40, color=ft.Colors.WHITE)
        self.mic_btn = ft.Container(
            content=self.mic_icon,
            width=80, height=80,
            border_radius=40,
            bgcolor=ft.Colors.BLUE_700,
            alignment=ft.alignment.center,
            on_click=self.toggle_recording,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.BLUE_900)
        )
        
        # 4. Visualizer Ring (Animates behind the mic)
        self.visualizer = ft.Container(
            width=80, height=80, border_radius=40,
            bgcolor=ft.Colors.BLUE_500, opacity=0,
            animate_opacity=300, animate_scale=500
        )

        # Assemble Main Area
        self.main_area = ft.Container(
            expand=True,
            padding=30,
            content=ft.Column([
                # Top Bar
                ft.Row([
                    ft.Text("Voice Operations Center", size=28, weight="bold", font_family="Roboto Mono"),
                    ft.Container(expand=True),
                    ft.Row([self.status_ring, self.status_text], spacing=10)
                ]),
                ft.Divider(color=ft.Colors.WHITE10),
                
                # Middle: Logs
                ft.Container(
                    content=self.log_list,
                    expand=True,
                    bgcolor=ft.Colors.WHITE10,
                    border_radius=15,
                    padding=10
                ),
                
                # Bottom: Mic Controls
                ft.Container(
                    height=150,
                    content=ft.Stack([
                        ft.Container(self.visualizer, alignment=ft.alignment.center), # Background Ring
                        ft.Container(self.mic_btn, alignment=ft.alignment.center),    # Foreground Button
                    ], alignment=ft.alignment.center)
                ),
                ft.Text("Click to Speak • Click again to Send", size=12, color=ft.Colors.GREY_500, text_align="center")
            ])
        )

    # --- LOGIC ---
    async def initial_greeting(self):
        self.add_log("System initialized.", "System")
        self.set_status("READY", ft.Colors.GREEN)
        self.voice.speak("System ready.")

    def toggle_recording(self, e):
        if not self.is_recording:
            # START RECORDING
            self.is_recording = True
            self.mic_icon.name = ft.Icons.STOP
            self.mic_btn.bgcolor = ft.Colors.RED_600
            self.mic_btn.shadow.color = ft.Colors.RED_900
            
            # Animate Visualizer (Pulsing Effect)
            self.visualizer.opacity = 0.3
            self.visualizer.scale = 1.5
            
            self.set_status("LISTENING...", ft.Colors.RED)
            self.ears.start_recording()
        else:
            # STOP RECORDING
            self.is_recording = False
            self.mic_icon.name = ft.Icons.MIC
            self.mic_btn.bgcolor = ft.Colors.BLUE_700
            self.mic_btn.shadow.color = ft.Colors.BLUE_900
            
            # Reset Visualizer
            self.visualizer.opacity = 0
            self.visualizer.scale = 1.0
            
            self.set_status("PROCESSING...", ft.Colors.YELLOW)
            self.page.update()

            # Process in background thread
            threading.Thread(target=self.process_recording, daemon=True).start()
        
        self.page.update()

    def process_recording(self):
        # 1. Get Text
        transcript = self.ears.stop_recording()
        if not transcript:
            self.add_log("No speech detected.", "Error")
            self.set_status("READY", ft.Colors.GREEN)
            return

        self.add_log(f"{transcript}", "User", ft.Colors.CYAN_200)

        # 2. Check Commands
        text = transcript.lower()
        if "start" in text or "analyze" in text:
            self.run_analysis()
        elif "exit" in text:
            self.voice.speak("Goodbye.")
            self.page.window_close()
        else:
            self.voice.speak("I didn't catch that command.")
            self.set_status("READY", ft.Colors.GREEN)

    def run_analysis(self):
        self.set_status("ANALYZING...", ft.Colors.PURPLE)
        self.voice.speak("Scanning inbox.")
        
        try:
            email_bot = EmailManager()
            emails = email_bot.fetch_recent_emails(count=3)
            
            if not emails:
                self.voice.speak("No new emails.")
                self.add_log("No new emails found.", "System")
                self.set_status("READY", ft.Colors.GREEN)
                return

            self.add_log(f"Found {len(emails)} emails.", "System")
            
            negative_count = 0
            summaries = []

            for mail in emails:
                # Add a 'Card' for each email processed
                full_text = f"Subject: {mail['subject']}\nFrom: {mail['sender']}\nContent: {mail['snippet']}"
                analysis = analyze_email(full_text)
                email_bot.log_to_sheet(analysis)

                color = ft.Colors.RED_400 if analysis.sentiment == "Negative" else ft.Colors.GREEN_400
                self.add_log_card(analysis.customer_name, analysis.sentiment, analysis.summary, color)

                if analysis.sentiment == "Negative":
                    negative_count += 1
                    summaries.append(f"From {analysis.customer_name}: {analysis.summary}")

            # Voice Report
            if negative_count > 0:
                self.voice.speak(f"Alert. Found {negative_count} negative reviews.")
                for s in summaries:
                    self.voice.speak(s)
                    time.sleep(0.5)
            else:
                self.voice.speak("All feedback is positive.")
                
        except Exception as e:
            self.add_log(f"Error: {e}", "System", ft.Colors.RED)
            self.voice.speak("An error occurred.")
        
        self.set_status("READY", ft.Colors.GREEN)

    # --- UI HELPERS ---
    def set_status(self, text, color):
        self.status_text.value = text
        self.status_text.color = color
        self.status_ring.bgcolor = color
        self.page.update()

    def add_log(self, message, sender="System", color=ft.Colors.WHITE):
        self.log_list.controls.append(
            ft.Text(f"{sender}: {message}", color=color, font_family="Roboto Mono")
        )
        self.page.update()

    def add_log_card(self, title, sentiment, body, color):
        """Adds a beautiful card for analysis results"""
        card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=16),
                    ft.Text(title, weight="bold"),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(sentiment, size=10, color=ft.Colors.BLACK),
                        bgcolor=color, padding=5, border_radius=5
                    )
                ]),
                ft.Text(body, size=12, color=ft.Colors.WHITE70)
            ]),
            bgcolor=ft.Colors.WHITE10,
            padding=10,
            border_radius=10,
            border=ft.border.all(1, color)
        )
        self.log_list.controls.append(card)
        self.page.update()

def main(page: ft.Page):
    ModernVoiceApp(page)

if __name__ == "__main__":
    ft.app(target=main)