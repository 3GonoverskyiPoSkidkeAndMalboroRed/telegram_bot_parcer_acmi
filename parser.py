import requests
from bs4 import BeautifulSoup
import re

async def search_drug(drug_name):
    try:
        url = "https://www.acmespb.ru/search.php"
        
        data = {
            "free_str": drug_name,
            "smode": "0",
            "source": "0"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        print(f"\n[DEBUG] Поиск препарата: {drug_name}")
        response = requests.post(url, data=data, headers=headers)
        print(f"[DEBUG] Статус ответа: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for item in soup.find_all('div', class_='trow'):
            try:
                if 'thead' in item.get('class', []):
                    continue
                    
                name_elem = item.select_one('div.cell.name p.sra')
                if not name_elem:
                    continue
                    
                name = name_elem.text.strip()
                price = item.select_one('div.cell.pricefull').text.strip() if item.select_one('div.cell.pricefull') else "Цена не указана"
                
                # Получаем элементы с ссылками
                pharmacy_elem = item.select_one('div.cell.pharm a')
                address_elem = item.select_one('div.cell.address a')
                
                # Получаем координаты из ссылки на карту
                map_link = address_elem.get('href', '') if address_elem else ''
                coords_match = re.search(r'text=([\d.,]+)', map_link)
                coords = coords_match.group(1) if coords_match else None
                
                # Формируем ссылку на Яндекс Карты
                yandex_map_link = f"https://maps.yandex.ru/?text={coords}" if coords else None
                
                # Получаем текст аптеки и адреса
                pharmacy = pharmacy_elem.text.strip() if pharmacy_elem else "Аптека не указана"
                address = address_elem.text.strip() if address_elem else "Адрес не указан"
                
                # Создаем блок с информацией, где названия аптеки и адрес являются ссылками
                result_item = (
                    f"💊 {name}\n"
                    f"💰 {price} руб.\n"
                )
                
                # Добавляем аптеку и адрес как ссылки, если есть координаты
                if yandex_map_link:
                    result_item += (
                        f"🏥 <a href='{yandex_map_link}'>{pharmacy}</a>\n"
                        f"📍 <a href='{yandex_map_link}'>{address}</a>\n"
                    )
                else:
                    result_item += (
                        f"🏥 {pharmacy}\n"
                        f"📍 {address}\n"
                    )
                
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