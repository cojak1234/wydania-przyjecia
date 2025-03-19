import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os
import sys
import configparser

# Wczytywanie ustawień z pliku konfiguracyjnego
config = configparser.ConfigParser()
exe_path = sys.argv[0]
config.read(os.path.splitext(exe_path)[0] + '.ini')

# Definiowanie ścieżek zapisu plików i licznika z pliku konfiguracyjnego
SAVE_PATH = config.get("Paths", "save_path")
COUNTER_PATH = os.path.dirname(exe_path) + config.get("Paths", "counter_path")

print(COUNTER_PATH)

# Tworzenie katalogów, jeśli nie istnieją
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)
if not os.path.exists(COUNTER_PATH):
    os.makedirs(COUNTER_PATH)


class BarcodeScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wydawanie Listów Przewozowych")
        self.center_window(800, 500)
        self.root.config(bg="red")

        self.scan_count = 0  # Licznik skanowanych kodów

        # Sprawdzenie, czy plik z dzisiejszą datą już istnieje, aby zainicjować licznik
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.load_scan_count()

        # Obsługa zdarzeń focus in/out
        self.root.bind("<FocusIn>", self.on_focus_in)
        self.root.bind("<FocusOut>", self.on_focus_out)

        # Obsługa kliknięcia na okno
        self.root.bind("<Button-1>", self.on_click)  # Kliknięcie na okno ustawia fokus na pole skanowania

        # Pole z datą i godziną
        self.datetime_label = tk.Label(root, text=self.get_datetime(), font=("Arial", 12), bg="red", fg="white")
        self.datetime_label.pack()
        self.update_datetime()

        # Napis WYDANIE
        self.wydanie_label = tk.Label(self.root, text="WYDAWANIE", font=("Arial", 30, "bold"), bg="red", fg="white")
        self.wydanie_label.pack(pady=20)

        # Pole do skanowania kodów
        self.entry = tk.Entry(root, font=("Arial", 12))
        self.entry.pack(pady=10, fill=tk.X, padx=20)
        self.entry.bind("<Return>", self.process_scan)
        self.entry.focus_set()

        # Pole z licznikiem skanowań
        self.counter_label = tk.Label(root, text=f"Liczba skanowań: {self.scan_count}", font=("Arial", 12), bg="red", fg="white")
        self.counter_label.pack(pady=10)
        # Napis nad listą zeskanowanych kodów
        self.last_scans_title = tk.Label(root, text="Historia skanów:", font=("Arial", 12, "bold"), bg="red", fg="white")
        self.last_scans_title.pack(pady=(10, 0))

        # Kontener na pole tekstowe i pasek przewijania
        frame = tk.Frame(root)
        frame.pack(padx=20, pady=5, fill="both", expand=True)

        # Pasek przewijania
        scrollbar = tk.Scrollbar(frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # Pole tekstowe z podpiętym paskiem przewijania (zmniejszono szerokość do 25 znaków)
        self.scrolled_text = tk.Text(frame, wrap="none", width=25, height=10, font=("Arial", 10), yscrollcommand=scrollbar.set)
        self.scrolled_text.pack(side="left", fill="both", expand=True)

        # Połączenie paska z polem tekstowym
        scrollbar.config(command=self.scrolled_text.yview)

        # Wczytaj historię na start
        self.load_scan_history()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def get_datetime(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_datetime(self):
        self.datetime_label.config(text=self.get_datetime())
        self.root.after(1000, self.update_datetime)

    def load_scan_count(self):
        filename = os.path.join(COUNTER_PATH, f"{self.today}_wydania_counter.txt")
        print(f"Ładowanie liczby skanowań z: {filename}")  # Debugowanie
        if os.path.exists(filename):
            with open(filename, "r") as file:
                try:
                    self.scan_count = int(file.read().strip())
                    print(f"Załadowano licznik: {self.scan_count}")  # Debugowanie
                except ValueError:
                    self.scan_count = 0
                    print("Błąd formatu w pliku licznika, ustawiono licznik na 0.")  # Debugowanie
        else:
            self.scan_count = 0
            print("Plik z licznikiem nie istnieje, ustawiono licznik na 0.")  # Debugowanie

    def save_scan_count(self):
        filename = os.path.join(COUNTER_PATH, f"{self.today}_wydania_counter.txt")
        print(f"Zapisuję licznik do: {filename}")  # Debugowanie
        with open(filename, "w") as file:
            file.write(str(self.scan_count))
        print(f"Zapisano licznik: {self.scan_count}")  # Debugowanie

    def process_scan(self, event):
        code = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        if not code:
            messagebox.showwarning("Błąd", "Kod nie może być pusty")
            return

        self.scan_count += 1
        self.counter_label.config(text=f"Liczba skanowań: {self.scan_count}")

        # Zapis do pliku
        self.save_scan_count()  # Dodajemy zapis po każdym skanowaniu

        # Pobranie pełnej daty i godziny skanowania
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Zmieniony format
        formatted_entry = f"{scan_time}\t-\t{code}"

        # Zapis do pliku z historią
        filename = os.path.join(SAVE_PATH, f"{self.today}_wydania.txt")
        with open(filename, "a") as file:
            file.write(formatted_entry + "\n")

        # Odświeżenie widoku historii
        self.load_scan_history()

    def load_scan_history(self):
        """Wczytuje i wyświetla historię skanów z pliku."""
        filename = os.path.join(SAVE_PATH, f"{self.today}_wydania.txt")

        if os.path.exists(filename):
            with open(filename, "r") as file:
                lines = file.readlines()

            # Pobranie 10 ostatnich linii
            last_scans = lines[-10:]

            # Wyczyszczenie pola i dodanie nowych danych
            self.scrolled_text.config(state="normal")
            self.scrolled_text.delete("1.0", tk.END)
            self.scrolled_text.insert(tk.END, "".join(lines))  # Wczytaj cały plik
            self.scrolled_text.config(state="disabled")

            # Przewinięcie na dół
            self.scrolled_text.yview_moveto(1.0)

    def on_focus_in(self, event):
        """Zmiana koloru tła na zielony, gdy okno jest aktywne."""
        self.root.config(bg="red")
        self.datetime_label.config(bg="red")
        self.wydanie_label.config(bg="red")
        self.counter_label.config(bg="red")
        self.last_scans_title.config(bg="red")

    def on_focus_out(self, event):
        """Zmiana koloru tła na szary, gdy okno traci focus."""
        self.root.config(bg="gray")
        self.datetime_label.config(bg="gray")
        self.wydanie_label.config(bg="gray")
        self.counter_label.config(bg="gray")
        self.last_scans_title.config(bg="gray")

    def on_click(self, event):
        """Ustaw focus na pole do skanowania, gdy klikniesz gdziekolwiek w oknie."""
        self.entry.focus_set()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = BarcodeScannerApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")
