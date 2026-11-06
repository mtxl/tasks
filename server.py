import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs


def load():
    with open("data.json", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_tasks_html(tasks):
    items = ""
    for t in tasks:
        item = "<li>"
        item += "<span>" + t["title"] + "</span>"
        item += '<form method="POST" action="/delete/' + str(t["id"]) + '" style="display:inline">'
        item += '<button class="del">Удалить</button>'
        item += "</form>"
        item += "</li>"
        items += item
    return items


def build_page(tasks):
    items = build_tasks_html(tasks)
    if not items:
        items = '<li class="empty">Пока задач нет</li>'

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
    html += "ul { list-style: none; padding: 0; }"
    html += "li { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: white; margin: 8px 0; border-radius: 6px; }"
    html += ".empty { color: #999; text-align: center; }"
    html += "</style>"
    html += "</head>"
    html += "<body>"
    html += "<h1>Таск-трекер</h1>"
    html += '<form method="POST" action="/add" class="add-form">'
    html += '<input type="text" name="title" placeholder="Новая задача..." required>'
    html += '<button class="add">Добавить</button>'
    html += "</form>"
    html += "<ul>" + items + "</ul>"
    html += "</body>"
    html += "</html>"
    return html


class Handler(BaseHTTPRequestHandler):

    def send_html(self, html, code=200):
        self.send_response(code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def redirect(self):
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        return parse_qs(body)

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
                new_id = max((t["id"] for t in data["tasks"]), default=0) + 1
                data["tasks"].append({"id": new_id, "title": title, "done": False})
                save(data)
            self.redirect()
            return

        if self.path.startswith("/delete/"):
            tid = int(self.path.split("/")[-1])
            data = load()
            data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
            save(data)
            self.redirect()
            return

        self.send_html("<h1>404</h1>", code=404)


if __name__ == "__main__":
    print("Сервер: http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
