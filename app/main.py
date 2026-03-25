import flet as ft
from app.ui import TranscriberApp


def main(page: ft.Page) -> None:
    TranscriberApp(page)


if __name__ == "__main__":
    ft.app(target=main)
