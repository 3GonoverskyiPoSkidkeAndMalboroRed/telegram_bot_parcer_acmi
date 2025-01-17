import requests
from bs4 import BeautifulSoup

async def search_drug(drug_name):
    try:
        url = "https://www.acmespb.ru/search.php"  # URL формы поиска
        
        # Данные для POST-запроса
        data = {
            "free_str": drug_name,
            "smode": "0",  # Поиск по торговому наименованию
            "source": "0"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        print(f"\n[DEBUG] Поиск препарата: {drug_name}")
        # Используем POST-запрос вместо GET
        response = requests.post(url, data=data, headers=headers)
        print(f"[DEBUG] Статус ответа: {response.status_code}")
        
        # Сохраняем ответ для отладки
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Ищем результаты поиска
        for item in soup.find_all('div', class_='trow'):
            try:
                # Пропускаем заголовок таблицы
                if 'thead' in item.get('class', []):
                    continue
                    
                name_elem = item.select_one('div.cell.name p.sra')
                if not name_elem:
                    continue
                    
                name = name_elem.text.strip()
                price = item.select_one('div.cell.pricefull').text.strip() if item.select_one('div.cell.pricefull') else "Цена не указана"
                pharmacy = item.select_one('div.cell.pharm a').text.strip() if item.select_one('div.cell.pharm a') else "Аптека не указана"
                address = item.select_one('div.cell.address a').text.strip() if item.select_one('div.cell.address a') else "Адрес не указан"
                
                result_item = f"💊 {name}\n💰 {price} руб.\n🏥 {pharmacy}\n📍 {address}\n"
                results.append(result_item)
                print(f"\n[DEBUG] Найден элемент:\n{result_item}")
                
            except Exception as e:
                print(f"[DEBUG] Ошибка при парсинге элемента: {str(e)}")
                continue
        
        print(f"\n[DEBUG] Всего найдено элементов: {len(results)}")
        return "\n".join(results) if results else "Препарат не найден"
        
    except Exception as e:
        print(f"[DEBUG] Критическая ошибка: {str(e)}")
        return f"Ошибка при поиске: {str(e)}" 