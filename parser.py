import requests
from bs4 import BeautifulSoup

async def search_drug(drug_name):
    try:
        url = f"https://www.acmespb.ru/preparaty/{drug_name.lower()}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        print(f"\n[DEBUG] Поиск по URL: {url}")
        response = requests.get(url, headers=headers)
        print(f"[DEBUG] Статус ответа: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Сохраняем HTML в файл для проверки
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        results = []
        print("\n[DEBUG] Начинаем парсинг элементов...")
        
        for item in soup.find_all('tr'):
            try:
                # Название препарата
                name_elem = item.select_one('p.sra')
                if not name_elem:
                    continue
                name = name_elem.text.strip()
                
                # Цена
                price_elem = item.select_one('div.cell.pricefull')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                # Аптека
                pharmacy_elem = item.select_one('div.cell.pharm a')
                pharmacy = pharmacy_elem.text.strip() if pharmacy_elem else "Аптека не указана"
                
                # Адрес
                address_elem = item.select_one('div.cell.address a')
                address = address_elem.text.strip() if address_elem else "Адрес не указан"
                
                result_item = f"💊 {name}\n💰 {price} руб.\n🏥 {pharmacy}\n📍 {address}\n"
                results.append(result_item)
                
                # Выводим каждый найденный элемент
                print(f"\n[DEBUG] Найден элемент:\n{result_item}")
                
            except (AttributeError, IndexError) as e:
                print(f"[DEBUG] Ошибка при парсинге элемента: {str(e)}")
                continue
        
        print(f"\n[DEBUG] Всего найдено элементов: {len(results)}")
        
        return "\n".join(results) if results else "Препарат не найден"
        
    except Exception as e:
        print(f"[DEBUG] Критическая ошибка: {str(e)}")
        return f"Ошибка при поиске: {str(e)}" 