import flet as ft
import sqlite3
from typing import List

class ModernNavBar(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(
            width=250,
            padding=10,
            bgcolor=ft.colors.BLUE_GREY_50,
            content=ft.Column(
                expand=True,
                controls=[
                    self._create_header(),
                    ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                    self._create_nav_items(),
                    ft.Divider(height=20),
                    self._create_database_tables_section(),
                ],
                spacing=10,
            ),
        )
        self.page = page

    def _create_header(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=40),
                            ft.Text("Bob the Lawyer", size=18, weight="bold"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    ft.Text("Legal AI Assistant", size=12, color=ft.colors.BLUE_GREY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=ft.padding.only(bottom=20),
        )

    def _create_nav_items(self):
        return ft.Column(
            controls=[
                self._create_nav_item(ft.icons.CHAT, "Chat", "chat"),
                self._create_nav_item(ft.icons.FOLDER, "Documents", "documents"),
                self._create_nav_item(ft.icons.HISTORY, "History", "history"),
                self._create_nav_item(ft.icons.SETTINGS, "Settings", "settings"),
            ],
            spacing=5,
        )

    def _create_nav_item(self, icon, text, route):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=20),
                    ft.Text(text, size=14),
                ],
                spacing=10,
            ),
            padding=10,
            border_radius=5,
            on_click=lambda e: self._change_route(route),
            on_hover=self._highlight_item,
        )

    def _create_database_tables_section(self):
        self.tables_container = ft.Column(
            controls=[
                ft.Text("Database Tables", size=14, weight="bold"),
                ft.Divider(),
            ],
            spacing=5,
        )
        self._load_database_tables()
        return self.tables_container

    def _load_database_tables(self):
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()

            for table in tables:
                table_name = table[0]
                self.tables_container.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.TABLE_CHART, size=16),
                                ft.Text(table_name, size=12),
                            ],
                            spacing=5,
                        ),
                        padding=ft.padding.only(left=10, top=5, bottom=5),
                        on_click=lambda e, table=table_name: self._show_table_content(table),
                    )
                )
        except Exception as e:
            self.tables_container.controls.append(
                ft.Text(f"Error loading tables: {str(e)}", size=12, color=ft.colors.RED)
            )

    def _show_table_content(self, table_name: str):
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 50;")
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            conn.close()

            # Create a data table to display the content
            data_columns = [ft.DataColumn(ft.Text(col)) for col in column_names]
            data_rows = [
                ft.DataRow(
                    cells=[ft.DataCell(ft.Text(str(cell))) for cell in row]
                ) for row in rows
            ]

        except : 
            print("error")
