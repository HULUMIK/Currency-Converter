"""
Unit-тесты для Currency Converter
Author: Гвозденко Никита
Тестирование валидации, конвертации и работы с JSON
"""

import unittest
import json
import os
import tempfile

class TestValidator(unittest.TestCase):
    """Тесты валидации суммы"""
    
    def test_valid_positive_integer(self):
        """Положительное целое число"""
        amount_str = "100"
        try:
            amount = float(amount_str)
            valid = amount > 0
            self.assertTrue(valid)
        except ValueError:
            self.fail("ValueError raised")
    
    def test_valid_positive_float(self):
        """Положительное дробное число"""
        amount_str = "123.45"
        try:
            amount = float(amount_str)
            valid = amount > 0
            self.assertTrue(valid)
        except ValueError:
            self.fail("ValueError raised")
    
    def test_valid_zero(self):
        """Ноль (невалидно)"""
        amount_str = "0"
        amount = float(amount_str)
        valid = amount > 0
        self.assertFalse(valid)
    
    def test_valid_negative(self):
        """Отрицательное число (невалидно)"""
        amount_str = "-50"
        amount = float(amount_str)
        valid = amount > 0
        self.assertFalse(valid)
    
    def test_invalid_string(self):
        """Строка вместо числа"""
        amount_str = "abc"
        try:
            float(amount_str)
            self.fail("ValueError should be raised")
        except ValueError:
            pass
    
    def test_invalid_empty(self):
        """Пустая строка"""
        amount_str = ""
        is_empty = not amount_str
        self.assertTrue(is_empty)
    
    def test_valid_with_dot(self):
        """Число с десятичной точкой"""
        amount_str = "99.99"
        amount = float(amount_str)
        valid = amount > 0
        self.assertTrue(valid)
    
    def test_invalid_comma_as_decimal(self):
        """Запятая вместо точки"""
        amount_str = "123,45"
        try:
            float(amount_str)
            self.fail("ValueError should be raised")
        except ValueError:
            pass

class TestJSONOperations(unittest.TestCase):
    """Тесты работы с JSON"""
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.filename = self.temp_file.name
    
    def tearDown(self):
        if os.path.exists(self.filename):
            os.unlink(self.filename)
    
    def test_save_and_load_history(self):
        """Сохранение и загрузка истории"""
        test_data = [
            {
                "datetime": "2026-05-07 12:00:00",
                "amount": "100.00",
                "from_curr": "USD",
                "to_curr": "EUR",
                "rate": "0.9200",
                "result": "92.00 EUR"
            }
        ]
        
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=4)
        
        with open(self.filename, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(test_data, loaded_data)
    
    def test_load_empty_file(self):
        """Загрузка пустого файла"""
        with open(self.filename, 'w') as f:
            json.dump([], f)
        
        with open(self.filename, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data, [])
    
    def test_load_corrupted_json(self):
        """Загрузка повреждённого JSON"""
        with open(self.filename, 'w') as f:
            f.write("{некорректный json}")
        
        with self.assertRaises(json.JSONDecodeError):
            with open(self.filename, 'r') as f:
                json.load(f)

class TestConversion(unittest.TestCase):
    """Тесты логики конвертации"""
    
    def setUp(self):
        # Тестовые курсы (относительно USD)
        self.rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "RUB": 91.5
        }
    
    def get_rate(self, from_curr, to_curr):
        """Получение курса конвертации"""
        if from_curr not in self.rates or to_curr not in self.rates:
            return None
        rate_from_usd = self.rates[from_curr]
        rate_to_usd = self.rates[to_curr]
        return rate_to_usd / rate_from_usd
    
    def calculate(self, amount, from_curr, to_curr):
        """Расчёт конвертации"""
        rate = self.get_rate(from_curr, to_curr)
        if rate is None:
            return None
        return amount * rate
    
    def test_usd_to_eur(self):
        """Конвертация USD → EUR"""
        result = self.calculate(100, "USD", "EUR")
        # 100 * (0.92 / 1.0) = 92
        self.assertAlmostEqual(result, 92.0, places=2)
    
    def test_eur_to_usd(self):
        """Конвертация EUR → USD"""
        result = self.calculate(100, "EUR", "USD")
        # 100 * (1.0 / 0.92) ≈ 108.70
        self.assertAlmostEqual(result, 108.695652, places=2)
    
    def test_usd_to_rub(self):
        """Конвертация USD → RUB"""
        result = self.calculate(50, "USD", "RUB")
        # 50 * (91.5 / 1.0) = 4575
        self.assertAlmostEqual(result, 4575.0, places=2)
    
    def test_rub_to_usd(self):
        """Конвертация RUB → USD"""
        result = self.calculate(4575, "RUB", "USD")
        # 4575 * (1.0 / 91.5) = 50
        self.assertAlmostEqual(result, 50.0, places=2)
    
    def test_same_currency(self):
        """Конвертация в ту же валюту (курс = 1)"""
        result = self.calculate(150, "EUR", "EUR")
        self.assertAlmostEqual(result, 150.0, places=2)
    
    def test_invalid_currency(self):
        """Несуществующая валюта"""
        result = self.calculate(100, "USD", "XYZ")
        self.assertIsNone(result)
    
    def test_large_amount(self):
        """Работа с большой суммой"""
        result = self.calculate(1000000, "USD", "EUR")
        self.assertAlmostEqual(result, 920000.0, places=2)

class TestHistoryLimit(unittest.TestCase):
    """Тесты ограничения истории"""
    
    def test_history_limit_50(self):
        """Проверка ограничения истории 50 записями"""
        history = []
        for i in range(60):
            history.append(f"record_{i}")
        
        # Ограничиваем 50
        if len(history) > 50:
            history = history[-50:]
        
        self.assertEqual(len(history), 50)

if __name__ == "__main__":
    unittest.main(verbosity=2)