import flet as ft
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import threading

def main(page: ft.Page):
    # ===== APP SETUP =====
    page.title = "Legal Assistant (Phi-3)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 700
    page.window_resizable = True
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # ===== CHAT UI COMPONENTS =====
    chat = ft.Column(
        expand=True,
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        auto_scroll=True,
    )

    def create_message(text, is_user=False):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(
                        content=ft.Icon(ft.icons.PERSON if is_user else ft.icons.GAVEL),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.BLUE_600 if is_user else ft.colors.GREEN_600,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text("You" if is_user else "Legal Assistant", 
                                    weight="bold", size=14),
                            ft.Container(
                                content=ft.Markdown(
                                    text,
                                    selectable=True,
                                    extension_set="gitHubWeb",
                                    code_theme="atom-one-dark",
                                ),
                                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                            ),
                        ],
                        spacing=6,
                        tight=True,
                        width=page.window_width * 0.7,  # Limit width for better readability
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
                wrap=True,
            ),
            bgcolor=ft.colors.BLUE_50 if is_user else ft.colors.GREEN_50,
            padding=12,
            border_radius=15,
            border=ft.border.all(1, ft.colors.BLUE_100 if is_user else ft.colors.GREEN_100),
            margin=ft.margin.only(left=80) if is_user else ft.margin.only(right=80),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

    def create_thinking_indicator():
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(
                        content=ft.Icon(ft.icons.GAVEL),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN_600,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text("Legal Assistant", weight="bold", size=14),
                            ft.Row(
                                controls=[
                                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                                    ft.Text("Researching your question..."),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=ft.colors.GREEN_50,
            padding=12,
            border_radius=15,
            border=ft.border.all(1, ft.colors.GREEN_100),
            margin=ft.margin.only(right=80),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

    # ===== MODEL LOADING =====
    loading_container = ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=50, height=50),
                ft.Text("Loading legal assistant...", size=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        expand=True,
        alignment=ft.alignment.center,
    )
    page.add(loading_container)
    page.update()

    def load_model():
        try:
            model_path = "C:/Program Files/Bob-the-lawyer-model/phi-3-local"
            tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                top_k=40,
                top_p=0.9,
                torch_dtype=torch.float16
            )
            
            # Switch to chat UI when model is loaded
            page.controls.clear()
            setup_chat_ui(pipe, tokenizer)
            page.update()
            
        except Exception as e:
            show_error(str(e))

    # ===== CHAT UI SETUP =====
    def setup_chat_ui(pipe, tokenizer):
        # Input controls
        user_input = ft.TextField(
            hint_text="Type your legal question here...",
            expand=True,
            min_lines=1,
            max_lines=5,
            autofocus=True,
            border_radius=15,
            filled=True,
            border_color=ft.colors.TRANSPARENT,
        )
        
        send_button = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            icon_size=24,
            tooltip="Send message",
            bgcolor=ft.colors.BLUE_500,
            icon_color=ft.colors.WHITE,
        )

        def send_click(e):
            user_message = user_input.value.strip()
            if not user_message:
                return
                
            # Immediately add user message
            chat.controls.append(create_message(user_message, is_user=True))
            user_input.value = ""
            page.update()
            
            # Add thinking indicator
            thinking_indicator = create_thinking_indicator()
            chat.controls.append(thinking_indicator)
            page.update()
            
            # Generate response in background thread
            threading.Thread(
                target=generate_response,
                args=(user_message, thinking_indicator, pipe, tokenizer),
                daemon=True
            ).start()

        def generate_response(user_message, thinking_indicator, pipe, tokenizer):
            try:
                response = pipe(
                    f"<|user|>\n{user_message}<|end|>\n<|assistant|>",
                    max_length=250,
                    pad_token_id=tokenizer.eos_token_id
                )[0]['generated_text'].split("<|assistant|>")[-1].strip()
                
                # Update UI with response
                page.run_thread(lambda: update_chat(thinking_indicator, response))
                
            except Exception as ex:
                page.run_thread(lambda: show_error(f"Error generating response: {str(ex)}"))

        def update_chat(thinking_indicator, response):
            chat.controls.remove(thinking_indicator)
            chat.controls.append(create_message(response))
            page.update()

        send_button.on_click = send_click
        user_input.on_submit = send_click

        # Main layout
        page.add(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.GAVEL, size=28, color=ft.colors.GREEN_700),
                            ft.Text("Legal Assistant", size=24, weight="bold"),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=20),
                    ft.Container(
                        content=chat,
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=10),
                    ),
                    ft.Container(
                        ft.Row(
                            [
                                user_input,
                                ft.Container(send_button, border_radius=15),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.END,
                        ),
                        bgcolor=ft.colors.GREY_100,
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),
                        border_radius=15,
                    ),
                ],
                spacing=15,
                expand=True,
            )
        )
        page.update()

    def show_error(error_msg):
        page.controls.clear()
        page.add(
            ft.Column(
                [
                    ft.Text("Error", size=24, weight="bold", color=ft.colors.RED),
                    ft.Text(error_msg),
                    ft.ElevatedButton(
                        "Retry",
                        on_click=lambda e: retry_loading(),
                        icon=ft.icons.REFRESH,
                    )
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

    def retry_loading():
        page.controls.clear()
        main(page)

    # Start loading the model in a separate thread
    threading.Thread(target=load_model, daemon=True).start()

ft.app(target=main)