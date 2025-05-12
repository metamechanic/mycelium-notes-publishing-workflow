---
title: "{{title}}"
type: book
categories: [book, reading]
author: 
published: 
isbn: 
rating: 
date: {{date}}
format:
  html:
    toc: true
    toc-location: right
---

# {{title}}

:::{.column-margin}
![](../assets/books/{{slug}}.jpg)

**Author:** {{author}}  
**Published:** {{published}}  
**ISBN:** {{isbn}}  
**Rating:** {{rating}}/5
:::

## Summary

## Key Ideas

## Quotes

## Related Books

```{python}
#| echo: false
#| output: true

# This is where you would generate a visualization of related books
import matplotlib.pyplot as plt
import networkx as nx

# Example visualization - would be customized with actual data
# G = nx.Graph()
# G.add_node("{{title}}", type="focus")
# G.add_node("Related Book 1", type="related")
# G.add_node("Related Book 2", type="related")
# G.add_edge("{{title}}", "Related Book 1")
# G.add_edge("{{title}}", "Related Book 2")
# 
# pos = nx.spring_layout(G)
# plt.figure(figsize=(8, 6))
# nx.draw_networkx_nodes(G, pos, 
#                       node_color=['red' if n == "{{title}}" else 'blue' for n in G.nodes],
#                       node_size=[700 if n == "{{title}}" else 500 for n in G.nodes])
# nx.draw_networkx_edges(G, pos)
# nx.draw_networkx_labels(G, pos)
# plt.axis('off')
# plt.title("Books Related to {{title}}")
# plt.tight_layout()
# plt.show()
```

## Notes

## References