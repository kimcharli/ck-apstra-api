---
title: Notes
description: 
pubDate: 2025-02-15
keywords:
    - CK-Apstra-API
    - CMS
---

{% assign notes = site.pages | where_exp: "item", "item.path contains 'notes/'" %}
{% for note in notes %}
{% unless note.path contains 'assets' or note.name == 'index.md' %}
* [{{ note.title }}]({{ note.url | relative_url }}) {% if note.pubDate %}({{ note.pubDate | date: "%Y-%m-%d" }}){% endif %}
  {% if note.description %}
  > {{ note.description }}
  {% endif %}
{% endunless %}
{% endfor %}
