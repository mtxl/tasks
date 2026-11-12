import html
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

DATA_FILE = "data.json"


def load(path=DATA_FILE):
    """Читает данные. При ошибке возвращает пустой список задач."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"tasks": []}
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        return {"tasks": []}
    return data


def save(data, path=DATA_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def toggle_task(tasks, tid):
    """Переключает done. Возвращает True, если задача найдена."""
    for task in tasks:
        if task.get("id") == tid:
            task["done"] = not bool(task.get("done", False))
            return True
    return False


def task_id(task):
    """Возвращает id задачи числом или None, если id некорректный."""
    try:
        return int(task.get("id"))
    except (TypeError, ValueError):
        return None


def valid_tasks(tasks):
    """Оставляет только записи с корректным id."""
    return [task for task in tasks if task_id(task) is not None]


def build_tasks_html(tasks):
    items = ""
    for t in tasks:
        tid = task_id(t)
        if tid is None:
            continue

        title = html.escape(str(t.get("title", "")))
        done = bool(t.get("done", False))
        css = ' class="done"' if done else ""
        mark = "↺" if done else "✓"

        item = "<li%s>" % css
        item += '<span class="title">' + title + "</span>"
        item += '<span class="actions">'
        item += '<form method="POST" action="/toggle/%d" style="display:inline">' % tid
        item += '<button class="toggle">%s</button>' % mark
        item += "</form>"
        item += '<form method="POST" action="/delete/%d" style="display:inline">' % tid
        item += '<button class="del">Удалить</button>'
        item += "</form>"
        item += "</span>"
        item += "</li>"
        items += item
    return items


def build_page(tasks):
    items = build_tasks_html(tasks)
    if not items:
        items = '<li class="empty">Пока задач нет</li>'

    checked = valid_tasks(tasks)
    total = len(checked)
    done_count = sum(1 for t in checked if t.get("done"))

    html = "<!DOCTYPE html>"
    html += '<html lang="ru">'
    html += "<head>"
    html += '<meta charset="utf-8">'
    html += "<title>Таск-трекер</title>"
    html += "<style>"
    html += "body { font-family: Arial; max-width: 600px; margin: 40px auto; padding: 0 20px; background: #fafafa; }"
    html += "h1 { border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }"
    html += "form.add-form { display: flex; gap: 8px; margin: 20px 0; }"
    html += 'input[type="text"] { flex: 1; padding: 10px; font-size: 15px; border: 1px solid #ccc; border-radius: 5px; }'
    html += "button { padding: 10px 16px; font-size: 15px; border: none; border-radius: 5px; cursor: pointer; color: white; }"
    html += ".add { background: #4CAF50; }"
    html += ".del { background: #e74c3c; }"
    html += ".toggle { background: #2196F3; }"
    html += "ul { list-style: none; padding: 0; }"
    html += "li { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: white; margin: 8px 0; border-radius: 6px; }"
    html += ".actions { display: flex; gap: 6px; }"
    html += ".done .title { text-decoration: line-through; color: #999; }"
    html += ".stats { color: #666; }"
    html += ".empty { color: #999; text-align: center; }"
    html += "</style>"
    html += "</head>"
    html += "<body>"
    html += "<h1>Таск-трекер</h1>"
    html += '<form method="POST" action="/add" class="add-form">'
    html += '<input type="text" name="title" placeholder="Новая задача..." required>'
    html += '<button class="add">Добавить</button>'
    html += "</form>"
    html += '<p class="stats">Всего: %d, выполнено: %d</p>' % (total, done_count)
    html += "<ul>" + items + "</ul>"
    html += "</body>"
    html += "</html>"
    return html


class Handler(BaseHTTPRequestHandler):

    def send_html(self, html, code=200):
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self):
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        return parse_qs(body)

    def parse_id(self):
        """Достаёт числовой id из пути или возвращает None."""
        try:
            return int(self.path.rsplit("/", 1)[-1])
        except (TypeError, ValueError):
            return None

    def do_GET(self):
        if self.path == "/":
            data = load()
            html = build_page(data["tasks"])
            self.send_html(html)
            return
        self.send_html("<h1>404</h1>", code=404)

    def do_POST(self):
        if self.path == "/add":
            form = self.read_form()
            title = form.get("title", [""])[0].strip()
            if title:
                data = load()
                ids = [task_id(t) for t in data["tasks"]]
                new_id = max([i for i in ids if i is not None], default=0) + 1
                data["tasks"].append({"id": new_id, "title": title, "done": False})
                save(data)
            self.redirect()
            return

        if self.path.startswith("/toggle/"):
            tid = self.parse_id()
            if tid is None:
                self.send_html("<h1>400</h1>", code=400)
                return
            data = load()
            if toggle_task(data["tasks"], tid):
                save(data)
            self.redirect()
            return

        if self.path.startswith("/delete/"):
            tid = self.parse_id()
            if tid is None:
                self.send_html("<h1>400</h1>", code=400)
                return
            data = load()
            data["tasks"] = [t for t in data["tasks"] if task_id(t) != tid]
            save(data)
            self.redirect()
            return

        self.send_html("<h1>404</h1>", code=404)


if __name__ == "__main__":
    print("Сервер: http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
