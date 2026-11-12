import json
import os
import tempfile
import unittest

import server


class ToggleTests(unittest.TestCase):

    def test_toggle_switches_done(self):
        tasks = [{"id": 1, "title": "Тест", "done": False}]

        self.assertTrue(server.toggle_task(tasks, 1))
        self.assertTrue(tasks[0]["done"])

        self.assertTrue(server.toggle_task(tasks, 1))
        self.assertFalse(tasks[0]["done"])

    def test_toggle_missing_returns_false(self):
        self.assertFalse(server.toggle_task([], 99))


class HtmlTests(unittest.TestCase):

    def test_script_is_escaped(self):
        tasks = [{"id": 1, "title": "<script>alert(1)</script>", "done": False}]

        page = server.build_tasks_html(tasks)

        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_done_has_class(self):
        tasks = [{"id": 1, "title": "Готово", "done": True}]

        page = server.build_tasks_html(tasks)

        self.assertIn('class="done"', page)


class LoadTests(unittest.TestCase):

    def test_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = server.load(os.path.join(tmp, "missing.json"))

        self.assertEqual(data, {"tasks": []})

    def test_loads_tasks_from_file(self):
        payload = {"tasks": [{"id": 1, "title": "Из файла", "done": False}]}

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "data.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)

            data = server.load(path)

        self.assertEqual(data, payload)


if __name__ == "__main__":
    unittest.main()
