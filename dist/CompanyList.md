---
layout: data
title:  "Company List Table"
categories: quant data
---

<table>
    <thead>
    <tr>
      <td> TICKER </td>
      <td> NAME </td>
      <td> GROUP </td>
    </tr>
    </thead>
  <tbody>
{% for c in site.data.companylist.Co %}
    <tr>
      <td>{{c.cd}}</td>
      <td>{{c.nm}}</td>
      <td>{{c.gb}}</td>
    </tr>
{% endfor %}
  </tbody>
</table>



