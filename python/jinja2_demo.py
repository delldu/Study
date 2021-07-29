from jinja2 import Template

t = Template("Hello {{name}}!!!")
ts = t.render(name="John")

print(ts)
