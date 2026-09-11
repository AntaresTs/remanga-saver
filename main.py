import requests, json, time, os

# url exemple
# https://img-reserve.reimg2.org/images/143191/f00c4f661f46016c4ffe7814815af2c4/ed5125c9b4b85d6dd0a9e10e8cbf6526.webp



# ID главы из URL страницы (например, .../job-search-guide/1743839/)

def log(massage, level="info"):
    print(f"[{level}]: {massage}")

class ReManga_downloader:
    def __init__(self):
        self.download_attempts = 3
        self.pause_between_download_attempts = 5
        self.comicsDir = "comics"

    
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

    def get_chapter_id_from_cash(self, cash):
        capter_id_list = []

        if cash == {}:
            log("Список хранимых в кеше id глав пуст")
            return capter_id_list

        for manga_name in cash:
            for json_data in cash[manga_name]:
                capter_id_list.append(json_data["id"])

        log("Из кэша загружен список id глав")
        return capter_id_list
        
    
    def get_json_data_from_server(self, chapter_id_list, test_mode=False):
        """
        Получает данные для каажой главы в списке.
        принимает на вход словарь формата:
            {
                "Manga name": [
                    "chapter_id",
                    "1744235"
                ]
            }

        """
        
        dataset = {}
        also_exist_id = []

        # получение данных записанных в кэше
        cash = self.work_wich_cash("serv_resp", "download")
        dataset = cash if not type(cash) == int else {}

        # Формирование id глав хранимых в хэше
        also_exist_id = self.get_chapter_id_from_cash(dataset)

        if test_mode:
            log(f"Входные данные: \n{chapter_id_list}\n")

        # Парсинг данных
        for manga_name, chapter_id_list in chapter_id_list.items():
            manga_name = manga_name.replace(" ", "_")

            server_json_list = []
            for chapter_id in chapter_id_list:
                data = {"error": None}

                if chapter_id in also_exist_id:
                    log(f"capter id: {chapter_id} alredy exist")
                    break

                for i in range(self.download_attempts):
                    url = f"https://api.remanga.org/api/v2/titles/chapters/{chapter_id}/"
                    
                    try:
                        if not test_mode:
                            response = self.reqSession.get(url)
                            response.raise_for_status()  # Проверка на ошибки HTTP
                            data = response.json()
                            log(f"Response successful received from server")
                        else:
                            log(f"Response from url: {url}")
                            data = {"test_mode": True, "messege": "test", "chapter_id": chapter_id, "request_url": url}

                        break

                    except Exception as e:
                        log(f"request error. attempt: {i+1}/{attempts}\nError: {e}", "error")
                        time.sleep(self.pause_between_download_attempts)

                server_json_list.append(data)
                
            dataset.setdefault(manga_name, []).extend(server_json_list)
            time.sleep(2)

        # Обновление хэша
        if not test_mode:
            status = work_wich_cash("serv_resp", "save", dataset)
        else:
            print(dataset)

        return dataset



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
        Берет на вход обработанные данные, и возвращает готовый лист с данными для вставки в функцию скачивания
        """
        
        out_list = []

        log("Преобразование данных для загрузки")

        for chapter in data:
            manga_name = chapter["manga_name"]
            tome = chapter["tome"]
            chapter_num = chapter["chapter"]
            chapter_name = chapter["name"]
            publ = chapter["publishers"][0]

            root = f"{publ}-{manga_name.replace(" ", "_")}"
            down_path = f"{chapter_num}-{chapter_name.replace(" ", "_")}" if not chapter_name == "" else chapter_num

            save_path = os.path.join(str(tome), f"{chapter_num}-{chapter_name.replace(" ", "_")}")
            
            full_path = os.path.join(self.comicsDir, root, save_path)
            #os.makedirs(pre_path, exist_ok=True)

            for num, page in chapter["pages"].items():
                name = f"{num}{os.path.splitext(page)[1]}"
                
                out_list.append([full_path, name, page])

        return out_list     # 


    def download_pic(self, download_data:list): 
        """
        Функция пакетного скачивания файлов
        принимает на вход лист формата:
        [[path, file_name, url], ...]
        [root, save_path, name, page]
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

    
    def work_wich_cash(self, cash_type, mode="auto", data=None):
        """
        Функция работы с кешем.
        """

        cash_dir = "cash"
        files = {
            "serv_resp": {
                "file_name": "cash_resp"
            },
            "procces": {
                "file_name": "cash_prrsp"
            }
        }
        
        os.makedirs(cash_dir, exist_ok=True)
        filename = (files[cash_type] or {}).get("file_name")
        path = os.path.join(cash_dir, filename)


        if not filename:
            raise Exception(f"Cash type: {cash_type} not supported")
            return 1

        if mode == "auto":
            pass
        elif mode == "save":
            if (not data) and (not type(data) == dict):
                raise Exception("The format of data is erroneous")
                return 3

            with open(path, "w") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            return 0

        elif mode == "download":
            if os.path.isfile(path):

                with open(path, "r") as f:
                    data = json.load(f)

                return (data or {})
            else:
                return {}

        else:
            raise Exception(f"Mode {mode} unknow")
            return 2

## Пока что начальная функция 

    def gen_info_file(self, proc_dataset, tags, genes language="ru"):

        for manga_name, json_data_list in proc_dataset.items():
            total_volumes = len(json_data_list) 
                
            authors = []
            for publisher in json_data_list[0]["publishers"]
                authors.append(publisher["name"])

            root = f"{authors[0]}-{manga_name.replace(" ", "_")}"
            title = manga_name.replace("_", " ")
            

#        self.root: str = ""                     #!< Путь к корневой папке произведения
#        self.authors: list = None               #!< Список авторов
#        self.title: str = None                  #!< Название
#        self.alt_titles: list = None            #!< Альтернативные назания
#        self.language: str = None               #!< Язык
#        self.tags: list = None                  #!< Список тегов
#        self.genes: list = None                 #!< Список жанров
#        self.book_type: Optional[str] = None    #!< Тип:
#        self.total_chapter: int = 0                #!< Общее количество томов
#        self.total_volumes: int = 0             #!< Общее количество глав
#        self.description: Optional[str] = None  #!< Описание
        pass
    
    def main(chapter_list):

        # Формируем первичные данные
        dataset = get_json_data_from_server(chapter_list)

        # Обрабатываем данные
        proc_dataset = pars_json_data()

        # Нормализуем данные для скачивания
        norm_download_data = convert_for_download()

        #gen_info_file(norm_download_data[0][0], proc_dataset)

        # Скачиваем данные
        download_pic(norm_download_data)
        pass

        
#    def load_data_from_cash(self):
#        cash_file_from_the_resp = "cash_resp"
#        cash_file_from_the_proc_resp = "cash_prrsp"
#
#        # Работа с кэшем запрощеных глав
#        if os.path.isfile(cash_file_from_the_resp) and self.use_cash[0]:
#
#            log("Использоание кеша данных с сервера")
#            with open(cash_file_from_the_resp, "r") as f:
#                dataset = json.load(f)
#
#        else:
#            log("Создание кеша данных сервера")
#            dataset = self.get_dataset_for_site(self.manga_download_data)
#
#            with open(cash_file_from_the_resp, "w") as f:
#                json.dump(dataset, f, indent=4, ensure_ascii=False)
#
#
#        # Работа с обработанным кэшем
#        if(os.path.isfile(cash_file_from_the_proc_resp) and self.use_cash[1]):
#            log("Использоание кеша обработанных данных")
#            with open(cash_file_from_the_proc_resp, "r") as f:
#                data = json.load(f)
#
#        else:
#            log("Создание кеша обработанных данных")
#            data = self.pars_json_data(dataset)
#
#            with open(cash_file_from_the_proc_resp, "w") as f:
#                json.dump(data, f, indent=4, ensure_ascii=False)
#
#        return data

#    def get_dataset_for_site(self, chapter_id_list:dict):
#        """
#        Отправлет запрос и получает json с сайта
#        """
#
#        # TODO Сдетать следующее:
#        # С начала загружается json c кэша
#        # Если в кэше нет главы с данным id то идет загрузка
#        # В конце полученный результат записывается в кэш
#        # Запись: cach = cash + new_data
#
#        out_data = {}
#        for manga_name, chapter_id_list in manga_download_list.items():
#
#            server_json_list = []
#            for chapter_id in chapter_id_list:
#                data = {"error": None}
#
#                for i in range(self.download_attempts):
#                    url = f"https://api.remanga.org/api/v2/titles/chapters/{chapter_id}/"
#                    
#                    try:
#                        response = self.reqSession.get(url)
#                        response.raise_for_status()  # Проверка на ошибки HTTP
#                        data = response.json()
#                        log(f"Response successful received from server")
#                        break
#                    except Exception as e:
#                        log(f"request error. attempt: {i+1}/{attempts}\nError: {e}", "error")
#                        time.sleep(self.pause_between_download_attempts)
#
#                server_json_list.append(data)
#
#            out_data[manga_name] = server_json_list
#
#            time.sleep(2)
#
#        return out_data

def main():

    print("OK")


if __name__ == "__main__":
    c = ReManga_downloader()

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

    c.main(c_data)



