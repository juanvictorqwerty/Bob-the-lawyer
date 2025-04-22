import flet as ft
from langchain_ollama import OllamaLLM
from langchain.memory import ConversationBufferMemory

def main(page: ft.Page):
    # Configure the page
    page.title = "Lawyer Chatbot (Phi)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 600
    page.padding = 20

    # Initialize the model (will load when first used)
    llm = OllamaLLM(model="phi", temperature=0.7)
    memory = ConversationBufferMemory()
    
    # Create chat messages list
    chat = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    
    # Create input field
    user_input = ft.TextField(
        hint_text="Type your legal question...",
        expand=True,
        multiline=True,
        min_lines=1,
        max_lines=5,
    )
    
    def send_click(e):
        if not user_input.value.strip():
            return
            
        # Add user message to chat
        user_message = user_input.value
        chat.controls.append(ft.Container(
            ft.Text(f"You: {user_message}"),
            alignment=ft.alignment.center_right,
            bgcolor=ft.colors.BLUE_100,
            padding=10,
            border_radius=10,
        ))
        
        # Show "thinking" indicator
        thinking_indicator = ft.Container(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Processing your question...")
            ], spacing=10),
            alignment=ft.alignment.center_left,
        )
        chat.controls.append(thinking_indicator)
        user_input.disabled = True
        page.update()
        
        # Process the question
        try:
            response = llm.invoke(input=user_message)
            
            # Remove thinking indicator
            chat.controls.remove(thinking_indicator)
            
            # Add bot response
            chat.controls.append(ft.Container(
                ft.Text(f"Lawyer Bot: {response}"),
                alignment=ft.alignment.center_left,
                bgcolor=ft.colors.GREEN_100,
                padding=10,
                border_radius=10,
            ))
            
        except Exception as e:
            chat.controls.append(ft.Text(f"Error: {str(e)}", color=ft.colors.RED))
        
        # Reset input
        user_input.value = ""
        user_input.disabled = False
        page.update()
        user_input.focus()
    
    # Create send button
    send_button = ft.IconButton(
        icon=ft.icons.SEND,
        on_click=send_click,
        tooltip="Send question",
    )
    
    # Create input row
    input_row = ft.Row(
        [user_input, send_button],
        spacing=10,
    )
    
    # Add all controls to page
    page.add(
        ft.Text("Legal Assistant Chatbot", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        chat,
        input_row,
    )
    
    # Set focus to input field
    user_input.focus()

# Run the app
ft.app(target=main)
