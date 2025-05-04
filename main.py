import flet as ft
import requests
import json

class LawyerChatBotApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.chat = ft.ListView(expand=True, spacing=10, auto_scroll=True)
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
        self.page.title = "Lawyer Chatbot (Phi)"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 800
        self.page.window_height = 600
        self.page.padding = 20

        input_row = ft.Row([self.user_input, self.send_button], spacing=10)

        self.page.add(
            ft.Text("Legal Assistant Chatbot", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            self.chat,
            input_row,
        )
        self.user_input.focus()

    def send_click(self, e):
        question = self.user_input.value.strip()
        if not question:
            return

        # Display user message
        self.chat.controls.append(
            ft.Container(
                ft.Text(f"You: {question}"),
                alignment=ft.alignment.center_right,
                bgcolor=ft.colors.BLUE_100,
                padding=10,
                border_radius=10,
            )
        )

        # Thinking indicator
        thinking = ft.Container(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Processing your question...")
            ], spacing=10),
            alignment=ft.alignment.center_left,
        )
        self.chat.controls.append(thinking)
        self.user_input.disabled = True
        self.page.update()

        try:
            # Call Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "phi3.5",
                    "prompt": question,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get('response', "⚠️ Unexpected response format.")
            else:
                reply = f"⚠️ Error {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as err:
            reply = f"⚠️ Connection error: {str(err)}"
        except json.JSONDecodeError:
            reply = "⚠️ Invalid JSON from API"
        except Exception as err:
            reply = f"⚠️ Unexpected error: {str(err)}"

        # Update chat
        self.chat.controls.remove(thinking)
        self.chat.controls.append(
            ft.Container(
                ft.Text(f"Lawyer Bot: {reply}"),
                alignment=ft.alignment.center_left,
                bgcolor=ft.colors.GREEN_100,
                padding=10,
                border_radius=10,
            )
        )

        self.user_input.value = ""
        self.user_input.disabled = False
        self.page.update()
        self.user_input.focus()


def main(page: ft.Page):
    LawyerChatBotApp(page)

ft.app(target=main)
