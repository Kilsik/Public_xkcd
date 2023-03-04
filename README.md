# Публикация комиксов в сообществе фанатов xkcd сети vk.com
Приложение автоматизирует выбор (случайным образом) комикса, скачивает его с [сайта автора](https://xkcd.com/) и публикует его на стене [сообщества](https://vk.com/club219173551) с комментарием.
### Как установить

Python3 должен быть уже установлен.

Рекомендуется использовать [virtualenv/venv](https://docs.python.org/3/library/venv.html) для изоляции проекта.
Затем используйте pip (или pip3 если есть конфликт с Python2) для
установки зависимостей:
```
pip install -r requirements.txt
```
Предварительно [зарегистрируйте](https://vk.com/apps?act=manage) приложение в сети ВКонтакте.
Для работы также нужно указать в переменных окружения следующие параметры:
- в VK_XKCD_ID поместите идентификатор сообщества;
- VK_USER_ID - идентификатор пользователя с правами администратора сообщества (либо с правами photo и wall по минимуму);
- VK_ACCESS_TOKEN - ключ доступа приложения к аккаунту пользователя, о котором говорилось выше.

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).