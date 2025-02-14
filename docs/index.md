---
title: Documentation Home
layout: default
---

# Documentation

## Latest Posts

{% assign notes_files = site.static_files | where: "extname", ".md" | where_exp: "file", "file.path contains '/notes/'" %}
{% for file in notes_files %}
{% assign note_content = file.path | remove_first: "/docs" | append: "" %}
{% assign page_data = site.pages | where: "path", note_content | first %}
* [{{ page_data.title }}]({{ file.path | remove_first: "/docs" | relative_url }}) - {{ page_data.pubDate | date: "%Y-%m-%d" }}
  {% if page_data.description %}
  > {{ page_data.description }}
  {% endif %}
{% endfor %}
