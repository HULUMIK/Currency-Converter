"""
Currency Converter - Конвертер валют с использованием внешнего API
Author: Гвозденко Никита
Description: GUI-приложение для конвертации валют с сохранением истории в JSON
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
from datetime import datetime
import threading

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter - Конвертер валют")
        self.root.geometry("750x550")
        self.root.resizable(False, False)
        
        # Данные
        self.history_file = "conversion_history.json"
        self.history = self.load_history()
        self.exchange_rates = {}
        self.api_key = None  # Бесплатный API не требует ключа, но оставим для возможности
        self.base_url = "https://api.exchangerate-api.com/v4/latest/"
        
        # Переменные
        self.from_currency = tk.StringVar(value="USD")
        self.to_currency = tk.StringVar(value="EUR")
        self.amount_var = tk.StringVar()
        self.result_var = tk.StringVar()
        
        # Загрузка курсов валют при старте
        self.status_var = tk.StringVar()
        self.status_var.set("Загрузка курсов валют...")
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка курсов валют в отдельном потоке
        self.load_currencies_thread()
        
        # Загрузка истории в таблицу
        self.update_history_table()
    
    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # ===== Фрейм конвертации =====
        convert_frame = ttk.LabelFrame(main_frame, text="Конвертация валют", padding="10")
        convert_frame.pack(fill="x", pady=(0, 10))
        
        # Сумма
        ttk.Label(convert_frame, text="Сумма:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.amount_entry = ttk.Entry(convert_frame, textvariable=self.amount_var, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Из валюты
        ttk.Label(convert_frame, text="Из валюты:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.from_combo = ttk.Combobox(convert_frame, textvariable=self.from_currency, width=10, state="readonly")
        self.from_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # В валюту
        ttk.Label(convert_frame, text="В валюту:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.to_combo = ttk.Combobox(convert_frame, textvariable=self.to_currency, width=10, state="readonly")
        self.to_combo.grid(row=0, column=5, padx=5, pady=5)
        
        # Кнопка конвертации
        self.convert_btn = ttk.Button(convert_frame, text="🔄 Конвертировать", command=self.convert)
        self.convert_btn.grid(row=0, column=6, padx=10, pady=5)
        
        # Результат
        ttk.Label(convert_frame, text="Результат:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        result_entry = ttk.Entry(convert_frame, textvariable=self.result_var, width=30, state="readonly", font=("Arial", 10, "bold"))
        result_entry.grid(row=1, column=1, columnspan=6, sticky="we", padx=5, pady=5)
        
        # ===== Статус =====
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 9))
        self.status_label.pack(side="left")
        
        # ===== История конвертаций =====
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding="10")
        history_frame.pack(fill="both", expand=True)
        
        # Таблица истории
        columns = ("datetime", "amount", "from_curr", "to_curr", "rate", "result")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)
        
        # Настройка заголовков
        self.history_tree.heading("datetime", text="Дата и время")
        self.history_tree.heading("amount", text="Сумма")
        self.history_tree.heading("from_curr", text="Из")
        self.history_tree.heading("to_curr", text="В")
        self.history_tree.heading("rate", text="Курс")
        self.history_tree.heading("result", text="Результат")
        
        # Ширина колонок
        self.history_tree.column("datetime", width=140)
        self.history_tree.column("amount", width=80)
        self.history_tree.column("from_curr", width=60)
        self.history_tree.column("to_curr", width=60)
        self.history_tree.column("rate", width=100)
        self.history_tree.column("result", width=120)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Кнопки управления историей
        button_frame = ttk.Frame(history_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="🗑️ Очистить историю", command=self.clear_history).pack(side="right", padx=5)
        ttk.Button(button_frame, text="📂 Обновить курсы", command=self.refresh_rates).pack(side="right", padx=5)
    
    def load_currencies_thread(self):
        """Загрузка списка валют в отдельном потоке"""
        thread = threading.Thread(target=self._load_currencies)
        thread.daemon = True
        thread.start()
    
    def _load_currencies(self):
        """Загрузка списка доступных валют из API"""
        try:
            # Используем USD как базовую валюту для получения списка
            url = self.base_url + "USD"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.exchange_rates = data.get("rates", {})
                currencies = sorted(list(self.exchange_rates.keys()))
                
                # Добавляем популярные валюты, если их нет в списке
                popular = ["USD", "EUR", "RUB", "GBP", "CNY", "JPY", "KZT", "UAH", "BYN"]
                for curr in popular:
                    if curr not in currencies:
                        currencies.append(curr)
                currencies = sorted(set(currencies))
                
                # Обновляем выпадающие списки
                self.root.after(0, lambda: self.from_combo.config(values=currencies))
                self.root.after(0, lambda: self.to_combo.config(values=currencies))
                self.root.after(0, lambda: self.from_combo.set(self.from_currency.get()))
                self.root.after(0, lambda: self.to_combo.set(self.to_currency.get()))
                self.root.after(0, lambda: self.status_var.set("✅ Курсы валют загружены. Готов к работе."))
            else:
                self.root.after(0, lambda: self.status_var.set(f"❌ Ошибка API: {response.status_code}. Использую стандартные курсы."))
                self._set_default_rates()
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"❌ Ошибка сети: {str(e)}. Использую стандартные курсы."))
            self._set_default_rates()
    
    def _set_default_rates(self):
        """Установка стандартных курсов на случай недоступности API"""
        # Базовые курсы относительно USD
        self.exchange_rates = {
            "USD": 1.0, "EUR": 0.92, "RUB": 91.5, "GBP": 0.79,
            "CNY": 7.22, "JPY": 153.5, "KZT": 442.0, "UAH": 39.2, "BYN": 3.26
        }
        currencies = sorted(self.exchange_rates.keys())
        self.root.after(0, lambda: self.from_combo.config(values=currencies))
        self.root.after(0, lambda: self.to_combo.config(values=currencies))
        self.root.after(0, lambda: self.status_var.set("⚠️ Использую стандартные курсы (API недоступен)"))
    
    def refresh_rates(self):
        """Обновление курсов валют"""
        self.status_var.set("Обновление курсов валют...")
        self.convert_btn.config(state="disabled")
        
        thread = threading.Thread(target=self._refresh_rates_thread)
        thread.daemon = True
        thread.start()
    
    def _refresh_rates_thread(self):
        """Обновление курсов в отдельном потоке"""
        try:
            url = self.base_url + "USD"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.exchange_rates = data.get("rates", {})
                self.root.after(0, lambda: self.status_var.set("✅ Курсы валют обновлены успешно!"))
                messagebox.showinfo("Успех", "Курсы валют успешно обновлены!")
            else:
                self.root.after(0, lambda: self.status_var.set(f"❌ Ошибка API: {response.status_code}"))
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось обновить курсы: {response.status_code}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"❌ Ошибка: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.convert_btn.config(state="normal"))
    
    def validate_amount(self, amount_str):
        """Валидация суммы"""
        if not amount_str:
            return False, "Введите сумму для конвертации!"
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "Сумма должна быть положительным числом!"
            if amount > 1e12:  # Ограничение на очень большие числа
                return False, "Сумма слишком большая (максимум 1,000,000,000,000)!"
            return True, amount
        except ValueError:
            return False, "Введите корректное число (используйте точку для десятичных)!"
    
    def get_exchange_rate(self, from_curr, to_curr):
        """Получение курса конвертации"""
        if from_curr not in self.exchange_rates or to_curr not in self.exchange_rates:
            return None
        
        # Конвертация через USD (базовая валюта)
        rate_from_usd = self.exchange_rates[from_curr]
        rate_to_usd = self.exchange_rates[to_curr]
        
        # Курс from_curr -> to_curr
        return rate_to_usd / rate_from_usd
    
    def convert(self):
        """Конвертация валюты"""
        # Валидация суммы
        valid, amount_or_error = self.validate_amount(self.amount_var.get())
        if not valid:
            messagebox.showerror("Ошибка ввода", amount_or_error)
            return
        
        amount = amount_or_error
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        
        # Проверка наличия курсов
        if from_curr not in self.exchange_rates or to_curr not in self.exchange_rates:
            messagebox.showerror("Ошибка", "Выбранные валюты недоступны. Обновите курсы.")
            return
        
        # Получение курса
        rate = self.get_exchange_rate(from_curr, to_curr)
        
        if rate is None:
            messagebox.showerror("Ошибка", "Не удалось получить курс конвертации!")
            return
        
        # Расчёт результата
        result = amount * rate
        
        # Форматирование результата
        result_str = f"{result:.2f} {to_curr}"
        
        # Форматирование суммы
        amount_formatted = f"{amount:.2f}" if amount == int(amount) and amount < 1000 else f"{amount:.2f}"
        
        # Отображение результата
        self.result_var.set(result_str)
        
        # Запись в историю
        history_entry = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount_formatted,
            "from_curr": from_curr,
            "to_curr": to_curr,
            "rate": f"{rate:.4f}",
            "result": f"{result:.2f} {to_curr}"
        }
        
        self.history.append(history_entry)
        
        # Ограничиваем историю последними 50 записями
        if len(self.history) > 50:
            self.history = self.history[-50:]
        
        self.save_history()
        self.update_history_table()
        self.status_var.set(f"✅ Конвертация выполнена: {amount} {from_curr} → {result:.2f} {to_curr}")
    
    def update_history_table(self):
        """Обновление таблицы истории"""
        # Очистка таблицы
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Добавление записей из истории (от новых к старым)
        for entry in reversed(self.history):
            self.history_tree.insert("", "end", values=(
                entry["datetime"],
                entry["amount"],
                entry["from_curr"],
                entry["to_curr"],
                entry["rate"],
                entry["result"]
            ))
    
    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю конвертаций?"):
            self.history = []
            self.save_history()
            self.update_history_table()
            self.status_var.set("История очищена.")
    
    # ---------- Работа с JSON ----------
    def load_history(self):
        """Загрузка истории из JSON"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_history(self):
        """Сохранение истории в JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {e}")

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()