import flet as ft
import sqlite3
from datetime import datetime
from model_handler import generate_reply
from sidebar import render_sidebar  # Optional sidebar module if you use one

class LawyerChatBotApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.chat = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.sidebar = render_sidebar() if 'render_sidebar' in globals() else ft.Container()
        self.user_input = ft.TextField(
            hint_text="Type your legal question...",
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=5,
        )
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND,
            on_click=self.send_click,
            tooltip="Send question",
        )
        
        # Initialize database and load previous messages
        self.initialize_database()
        self.load_previous_messages()
        self.init_ui()

    def initialize_database(self):
        """Create database and table if they don't exist"""
        self.conn = sqlite3.connect('database.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        ''')
        self.conn.commit()

    def load_previous_messages(self):
        """Load previous messages from database when app starts"""
        self.cursor.execute('SELECT sender, message FROM messages ORDER BY timestamp')
        messages = self.cursor.fetchall()
        
        for sender, message in messages:
            if sender == "user":
                self.chat.controls.append(
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            message,
                                            selectable=True,
                                            size=15,
                                            color=ft.colors.BLACK,
                                        )
                                    ],
                                    tight=True,
                                ),
                                alignment=ft.alignment.center_right,
                                bgcolor=ft.colors.BLUE_100,
                                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                border_radius=ft.border_radius.only(
                                    top_left=16,
                                    top_right=16,
                                    bottom_left=16,
                                    bottom_right=4,
                                ),
                                margin=ft.margin.only(bottom=6),
                                shadow=ft.BoxShadow(
                                    spread_radius=0.5,
                                    blur_radius=3,
                                    color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                                    offset=ft.Offset(0, 1.5),
                                ),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    )



                )
            else:  # bot or system messages
                self.chat.controls.append(
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            "BOB:",
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.BLUE_800,
                                        ),
                                        ft.Text(
                                            message,
                                            selectable=True,
                                            size=15,
                                            color=ft.colors.BLACK,
                                        )
                                    ],
                                    spacing=4,
                                    tight=True,
                                ),
                                alignment=ft.alignment.center_left,
                                bgcolor=ft.colors.GREEN_100,
                                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                border_radius=ft.border_radius.only(
                                    top_left=16,
                                    top_right=16,
                                    bottom_left=4,
                                    bottom_right=16,
                                ),
                                margin=ft.margin.only(bottom=6),
                                shadow=ft.BoxShadow(
                                    spread_radius=0.5,
                                    blur_radius=3,
                                    color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                                    offset=ft.Offset(0, 1.5),
                                ),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    )
                )
        self.page.update()

    def store_message(self, sender, message):
        """Store a message in the database"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO messages (sender, message, timestamp)
            VALUES (?, ?, ?)
        ''', (sender, message, timestamp))
        self.conn.commit()

    def init_ui(self):
        self.page.title = "Bob the lawyer"
        self.page.window_width = 800
        self.page.window_height = 600
        self.page.padding = 20

        main_column = ft.Column(
            expand=True,
            controls=[
                ft.Text("Chat", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.chat,
                ft.Row([self.user_input, self.send_button], spacing=10),
            ],
        )

        content = ft.Row(
            controls=[
                self.sidebar,
                ft.Container(width=1, bgcolor=ft.colors.GREY_300),
                main_column,
            ],
            expand=True,
        )

        self.page.add(content)
        self.user_input.focus()

    def send_click(self, e):
        question = self.user_input.value.strip()
        if not question:
            return

        # Store user message in database
        self.store_message("user", question)

        self.chat.controls.append(
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            question,
                                            selectable=True,
                                            size=15,
                                            color=ft.colors.BLACK,
                                        )
                                    ],
                                    tight=True,
                                ),
                                alignment=ft.alignment.center_right,
                                bgcolor=ft.colors.BLUE_100,
                                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                border_radius=ft.border_radius.only(
                                    top_left=16,
                                    top_right=16,
                                    bottom_left=16,
                                    bottom_right=4,
                                ),
                                margin=ft.margin.only(bottom=6),
                                shadow=ft.BoxShadow(
                                    spread_radius=0.5,
                                    blur_radius=3,
                                    color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                                    offset=ft.Offset(0, 1.5),
                                ),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    )



                )

        thinking = ft.Container(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Thinking...")
            ], spacing=10),
            alignment=ft.alignment.center_left,
        )
        self.chat.controls.append(thinking)
        self.user_input.disabled = True
        self.send_button.disabled=True
        self.page.update()

        try:
            reply = generate_reply(question)
            # Store bot reply in database
            self.store_message("bot", reply)
        except Exception as err:
            reply = f"⚠️ Error: {str(err)}"
            self.store_message("system", f"Error: {str(err)}")

        self.chat.controls.remove(thinking)
        self.chat.controls.append(
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "BOB:",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.BLUE_800,
                                    ),
                                    ft.Text(
                                        reply,
                                        selectable=True,
                                        size=15,
                                        color=ft.colors.BLACK,
                                    )
                                ],
                                spacing=4,
                                tight=True,
                            ),
                            alignment=ft.alignment.center_left,
                            bgcolor=ft.colors.GREEN_100,
                            padding=ft.padding.symmetric(horizontal=14, vertical=10),
                            border_radius=ft.border_radius.only(
                                top_left=16,
                                top_right=16,
                                bottom_left=4,
                                bottom_right=16,
                            ),
                            margin=ft.margin.only(bottom=6),
                            shadow=ft.BoxShadow(
                                spread_radius=0.5,
                                blur_radius=3,
                                color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                                offset=ft.Offset(0, 1.5),
                            ),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                )
            )

        self.user_input.value = ""
        self.user_input.disabled = False
        self.send_button.disabled= False
        self.page.update()
        self.user_input.focus()

    def __del__(self):
        """Close database connection when the app is closed"""
        if hasattr(self, 'conn'):
            self.conn.close()


def main(page: ft.Page):
    LawyerChatBotApp(page)

ft.app(target=main)