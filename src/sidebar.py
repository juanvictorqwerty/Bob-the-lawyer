import flet as ft 
import sqlite3      

class ModernNavBar(ft.Container):

    def __init__(self, main_app):
        self.main_app = main_app  
        self.current_selected = None 
        self.highest_discussion_num = 0  
        
        table_names = self.get_database_tables()  
        self.update_highest_discussion_num(table_names)  
        
        super().__init__(
            width=250,  
            padding=10, 
            clip_behavior=ft.ClipBehavior.HARD_EDGE, 
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(bottom=20),
                        content=ft.Text("Bob the lawyer", size=16, weight=ft.FontWeight.BOLD) 
                    ),
                    self.create_discussion_button(),  
                    *self.create_table_list_items(table_names),  
                ],
            ),
        )


    def update_highest_discussion_num(self, table_names):
        for table in table_names: 
            if table.startswith("discussion_"): 
                try:
                    num = int(table.split("_")[1])  
                    if num > self.highest_discussion_num: 
                        self.highest_discussion_num = num 
                except (IndexError, ValueError): 
                    continue 


    def create_discussion_button(self):
        return ft.Container(
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            content=ft.Row(
                controls=[
                    ft.Icon(name=ft.Icons.ADD, size=18),
                    ft.Text("Create a Discussion", size=14),
                ],
                spacing=10
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
            on_click=self.create_new_discussion 
        )


    def create_new_discussion(self, e):
        
        try:
            self.highest_discussion_num += 1
            table_name = f"discussion_{self.highest_discussion_num}"  
            
            conn = sqlite3.connect(self.main_app.get_database_path()) 
            cursor = conn.cursor()
            
            cursor.execute(f""" 
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    sender TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit() 
            conn.close() 
            
            self.main_app.switch_discussion(table_name) 
            self.refresh_sidebar(e.page, table_name) 
            
        except Exception as ex:
            print(e)


    def get_database_tables(self):
        
        try:
            conn = sqlite3.connect(self.main_app.get_database_path()) 
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';") 
            tables_data = cursor.fetchall()
            conn.close() 
            table_names = [
                table[0] for table in tables_data if table[0].startswith("discussion_")
            ]
            table_names.sort(reverse=True) 
            return table_names
        
        except Exception as e: 
            print(f"Error accessing database: {e}")
            return [] 


    def create_table_list_items(self, table_names):
        items = []
        for table in table_names:
            show_delete = table.startswith("discussion_") 
            items.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10, horizontal=15),
                    content=ft.Row(
                        controls=[
                            ft.Icon(name=ft.Icons.TABLE_ROWS, size=18),
                            ft.Text(
                                table, 
                                size=14,
                                color=ft.Colors.WHITE if table == self.current_selected else None
                            ),
                            
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_size=18,
                                icon_color=ft.Colors.RED_400,
                                visible=False,  
                                data=table,  
                                on_click=self.delete_discussion,
                            ) if show_delete else ft.Container(width=0)  
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)), 
                    bgcolor=ft.Colors.BLUE_800 if table == self.current_selected else None, 
                    on_click=lambda e, table=table: self.on_table_click(e, table), 
                    on_hover=lambda e, table=table: self.on_discussion_hover(e, table, show_delete), 
                )
            )
        return items


    def on_discussion_hover(self, e, table_name, show_delete):
        if show_delete:
            row = e.control.content
            delete_button = row.controls[-1] 
            delete_button.visible = e.data == "true" 
            e.control.update() 


    def delete_discussion(self, e, confirm=False):
        table_name = e.control.data  
        try:
            conn = sqlite3.connect(self.main_app.get_database_path())
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE {table_name}")
            conn.commit()
            conn.close()             
            if self.current_selected == table_name:
                self.current_selected = None 
                self.main_app.switch_discussion(None) 
                self.main_app.clear_chat()
            
            self.refresh_sidebar(e.page)   
        except Exception as ex:
            print("ERROR DELETION")


    def refresh_sidebar(self, page, new_table_name=None):
        table_names = self.get_database_tables() 
        if new_table_name:
            self.current_selected = new_table_name 
        self.content.controls = [
            ft.Container(
                padding=ft.padding.only(bottom=20),
                content=ft.Text("Bob the lawyer", size=16, weight=ft.FontWeight.BOLD)
            ),
            self.create_discussion_button(), 
            *self.create_table_list_items(table_names), 
        ]
        page.update()

    def on_table_click(self, e, table_name):
        self.current_selected = table_name 
        self.main_app.switch_discussion(table_name) 
        self.refresh_sidebar(e.page) 
        


def render_sidebar(main_app):
    return ModernNavBar(main_app)
