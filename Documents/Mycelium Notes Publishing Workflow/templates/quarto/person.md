---
title: "{{title}}"
type: person
categories: [person, people]
full_name: 
birth: 
death: 
nationality: 
occupation: 
date: {{date}}
format:
  html:
    toc: true
    toc-location: right
---

# {{title}}

:::{.column-margin}
![](../assets/{{slug}}.jpg)

**Born:** {{birth}}  
**Died:** {{death}}  
**Nationality:** {{nationality}}  
:::

## Bio

## Key Accomplishments

## Works

## Related Figures

```{python}
#| echo: false
#| output: true

# This is a programmatic element where you could
# visualize connections to other people in your notes
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

# Example visualization code - would be customized based on your actual data
# g = Network(height="400px", width="100%")
# g.add_node("{{title}}", size=20, title="{{title}}")
# g.add_node("Related Person 1", size=15)
# g.add_node("Related Person 2", size=15)
# g.add_edge("{{title}}", "Related Person 1")
# g.add_edge("{{title}}", "Related Person 2")
# g.show("person-network.html")
```

## References