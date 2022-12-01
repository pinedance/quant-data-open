---
layout: data
title:  "Coincidence Index Table"
categories: quant data
---

<table>
    <thead>
    <tr>
      <td> DATE </td>
      <td> VALUE </td>
    </tr>
    </thead>
  <tbody>
{% for c in site.data.CompositeIndex.CoincidenceIndex.data %}
    <tr>
      <td>{{c.d}}</td>
      <td>{{c.v}}</td>
    </tr>
{% endfor %}
  </tbody>
</table>



