---
layout: data
title:  "Miscellaneous Data Table"
categories: quant data
---

<table>
    <thead>
    <tr>
      <td> Key </td>
      <td> Value </td>
    </tr>
    </thead>
  <tbody>
{% for c in site.data.misc %}
    <tr>
      <td>{{c.key }}</td>
      <td>{{c.value }}</td>
    </tr>
{% endfor %}
  </tbody>
</table>



