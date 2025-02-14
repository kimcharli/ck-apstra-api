---
title: Documentation Home
layout: default
---

# Documentation

## Latest Posts

{% for post in site.pages %}
  {% if post.path contains '/notes/' %}
* [{{ post.title }}]({{ post.url | relative_url }}) - {{ post.pubDate | date: "%Y-%m-%d" }}
    {% if post.description %}
    > {{ post.description }}
    {% endif %}
  {% endif %}
{% endfor %}
