import requests, json, time, os

# url exemple
# https://img-reserve.reimg2.org/images/143191/f00c4f661f46016c4ffe7814815af2c4/ed5125c9b4b85d6dd0a9e10e8cbf6526.webp



# ID главы из URL страницы (например, .../job-search-guide/1743839/)

manga_download_list = {
    "Пособие по поиску работы": [
        "1743839",
        "1744235"
    ]
}


def log(massage, level="info"):
    print(f"[{level}]: {massage}")

class ReManga_downloader:
    def __init__(self, ):
        self.download_attempts = 3
        self.pause_between_download_attempts = 5
        self.use_cash = [1, 0]      # включение использования кеша данных парсера и обработанных данных

    
    def manga_download_url_to_id_formater(self, title_name, url_list:list):
        """
        Нужна для преобразования списка ссылок на главы манги в список id глав
        """

        log("Преобразование списка ссылок всписок id глав")
        url_list = list(dict.fromkeys(url_list))
        chapter_id_list = {title_name:[url.rsplit("/", 1)[-1] for url in url_list]}

        print(chapter_id_list)

        return chapter_id_list

        
    def init_parser(self, manga_download_list):
        self.manga_download_data = manga_download_list

        try:
            init_request_session()
            log("Request session init")

        except Exception as e:
            log(f"Error request session init. Exception: {e}")
    

    def init_request_session(self):
        
        # Задаем заголовки
        headers = {
            "Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://remanga.org/",
            "Origin": "https://remanga.org",
            "content-type": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd"
        }

        # Укажем куки
        cookies = {
            "yandexuid": "9111597671788425404",
            "yashr": "8854492401788425404",

        }

        s = requests.Session()
        s.headers.update(headers)
        s.cookies.update(cookies)

        self.reqSession = s


    def get_dataset_for_site(self, chapter_id_list:dict):
        """
        Отправлет запрос и получает json с сайта
        """

        # TODO Сдетать следующее:
        # С начала загружается json c кэша
        # Если в кэше нет главы с данным id то идет загрузка
        # В конце полученный результат записывается в кэш
        # Запись: cach = cash + new_data

        attempts = 3

        out_data = {}
        for manga_name, chapter_id_list in manga_download_list.items():

            server_json_list = []
            for chapter_id in chapter_id_list:
                data = {"error": None}


                for i in range(self.download_attempts):
                    url = f"https://api.remanga.org/api/v2/titles/chapters/{chapter_id}/"
                    
                    try:
                        response = self.reqSession.get(url)
                        response.raise_for_status()  # Проверка на ошибки HTTP
                        data = response.json()
                        log(f"Response successful received from server")
                        break
                    except Exception as e:
                        log(f"request error. attempt: {i+1}/{attempts}\nError: {e}", "error")
                        time.sleep(self.pause_between_download_attempts)

                server_json_list.append(data)

            out_data[manga_name] = server_json_list

            time.sleep(2)

        return out_data


    def pars_json_data(self, data):
        """
        Парсит данные полученные от запроса к API
        """

        proces_data = []

        for manga_name, json_resp_list in data.items():
            for json_resp in json_resp_list: 

                # Парсятся страницы
                pages_list = {}
                for page in json_resp["pages"]:
                    page_id = page[0]["id"]
                    page_url = page[0]["link"]
                    pages_list[page_id] = page_url

                # Издатеть / переводчик / автор
                publisher_list = [publisher.get("name") for publisher in json_resp["publishers"]]

        #        publisher_list = []
        #        for publisher in data["publishers"]:
        #            publisher_list.append(publisher.get("name"))

                chapt_pars_data = {
                    "manga_name": manga_name,
                    "tome": json_resp.get("tome"),
                    "chapter": json_resp.get("chapter"),
                    "name": json_resp.get("name"),
                    "pages": pages_list,
                    "publishers": publisher_list,
                    "previous": (json_resp["previous"] or {}).get("id"),
                    "next": (json_resp["next"] or {}).get("id"),
                }

                proces_data.append(chapt_pars_data)

        return proces_data


    def convert_for_download(self, data):
        """
        Берет на вход сформированные данные, и возвращает готовый лист с данными для вставки в функцию скачивания
        """
        
        out_list = []

        log("Преобразование данных для загрузки")

        for chapter in data:
            manga_name = chapter["manga_name"]
            tome = chapter["tome"]
            chapter_num = chapter["chapter"]
            chapter_name = chapter["name"]
            publ = chapter["publishers"][0]

            up_path = f"{publ}-{manga_name.replace(" ", "_")}"
            down_path = f"{chapter_num}-{chapter_name.replace(" ", "_")}" if not chapter_name == "" else chapter_num

            path = os.path.join(up_path, str(tome), f"{chapter_num}-{chapter_name.replace(" ", "_")}")

            #os.makedirs(pre_path, exist_ok=True)

            for num, page in chapter["pages"].items():
                name = f"{num}{os.path.splitext(page)[1]}"
                
                out_list.append([path, name, page])

        return out_list     # 


    def download_pic(self, download_data:list): 
        """
        Функция пакетного скачивания файлов
        принимает на вход лист формата:
        [[path, file_name, url], ...]
        """
        
        over_parts = len(download_data)
        for i, part in enumerate(download_data, start=1):
            path = part[0]
            file_name = part[1]
            url = part[2]

            log(f"Загрузка страницы: {i}/{over_parts}")

            os.makedirs(path, exist_ok=True)
            log(f"Create dirs: {path}")

            # Загружаем по чанкам
            with self.reqSession.get(url, stream=True) as r:
                r.raise_for_status()
                lof("Start download page")
                with open(os.path.join(path, file_name), 'wb') as f:
                    for chunk in r.iter_content(chunk_size=4024):
                        f.write(chunk)

        
    def load_data_from_cash(self):
        cash_file_from_the_resp = "cash_resp"
        cash_file_from_the_proc_resp = "cash_prrsp"

        # Работа с кэшем запрощеных глав
        if os.path.isfile(cash_file_from_the_resp) and self.use_cash[0]:

            log("Использоание кеша данных с сервера")
            with open(cash_file_from_the_resp, "r") as f:
                dataset = json.load(f)

        else:
            log("Создание кеша данных сервера")
            dataset = self.get_dataset_for_site(self.manga_download_data)

            with open(cash_file_from_the_resp, "w") as f:
                json.dump(dataset, f, indent=4, ensure_ascii=False)


        # Работа с обработанным кэшем
        if(os.path.isfile(cash_file_from_the_proc_resp) and self.use_cash[1]):
            log("Использоание кеша обработанных данных")
            with open(cash_file_from_the_proc_resp, "r") as f:
                data = json.load(f)

        else:
            log("Создание кеша обработанных данных")
            data = self.pars_json_data(dataset)

            with open(cash_file_from_the_proc_resp, "w") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)


        return data

def main():

    print("OK")


if __name__ == "__main__":
    c = ReManga_downloader(manga_download_list)
    #c.init_request_session()
    #load_data = c.load_data_from_cash()
    #c_data = c.convert_for_download(load_data)

    url_set = [
        "https://remanga.org/manga/job-search-guide/1743839",
        "https://remanga.org/manga/job-search-guide/1744235",
        "https://remanga.org/manga/job-search-guide/1744236",
        "https://remanga.org/manga/job-search-guide/1744259",
        "https://remanga.org/manga/job-search-guide/1744279",
        "https://remanga.org/manga/job-search-guide/1744321",
        "https://remanga.org/manga/job-search-guide/1787409",
        "https://remanga.org/manga/job-search-guide/1836908",
        "https://remanga.org/manga/job-search-guide/1854806",
        "https://remanga.org/manga/job-search-guide/1869503",
        "https://remanga.org/manga/job-search-guide/1887781",
        "https://remanga.org/manga/job-search-guide/1895269",
        "https://remanga.org/manga/job-search-guide/1911994",
        "https://remanga.org/manga/job-search-guide/1925105",
        "https://remanga.org/manga/job-search-guide/1938334",
        "https://remanga.org/manga/job-search-guide/1954644"
    ]


    c_data = c.manga_download_url_to_id_formater("Пособие по поиску работы", url_set)

    for i in c_data:
        for i1 in c_data[i]:

            print(i, i1)

    pass


#with open("cash.json", "w") as f:
#    json.dump(data, f, indent=4, ensure_ascii=False)
#
#pages = data.get("pages")
#image_urls = [page["link"] for page in pages]
#
#print(image_urls)



# Достаём массив страниц. Структура может отличаться, но обычно это data["pages"]
# Каждая страница — это массив изображений.
#pages = data.get("pages", [])
#
## Собираем все URL в один плоский список
#image_urls = [img["link"] for page in pages for img in page]
#
#print(f"Найдено {len(image_urls)} изображений:")
#for i, img_url in enumerate(image_urls, 1):
#    print(f"{i}. {img_url}")
