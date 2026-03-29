import os
def write_to_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: f.write(content)
    print(f"✅ Done: {path}")

css = ":root { --p: #7c3aed; } body { background: #05070a; color: white; } .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(15px); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); }"
html = "{% extends \"base.html\" %} \n {% block content %} <div class=\"glass p-10\"> <h1 class=\"text-2xl\">MG Social Radar</h1> </div> {% endblock %}"

write_to_file("static/css/modern_style.css", css)
write_to_file("templates/discovery_radar.html", html)
print("🤖 Terminal has finished coding for you!")