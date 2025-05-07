# app.py
import flet as ft
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
        self.init_ui()

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

        self.chat.controls.append(
            ft.Container(
                ft.Text(f"YOU: {question}"),
                alignment=ft.alignment.center_right,
                bgcolor=ft.colors.BLUE_100,
                padding=10,
                border_radius=10,
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
        except Exception as err:
            reply = f"⚠️ Error: {str(err)}"

        self.chat.controls.remove(thinking)
        self.chat.controls.append(
            ft.Container(
                ft.Text(f"BOB: {reply}"),
                alignment=ft.alignment.center_left,
                bgcolor=ft.colors.GREEN_100,
                padding=10,
                border_radius=10,
            )
        )

        self.user_input.value = ""
        self.user_input.disabled = False
        self.send_button.disabled= False
        self.page.update()
        self.user_input.focus()


def main(page: ft.Page):
    LawyerChatBotApp(page)

ft.app(target=main)
