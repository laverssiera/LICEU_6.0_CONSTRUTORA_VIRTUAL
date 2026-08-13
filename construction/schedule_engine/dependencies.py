def apply_dependencies(tasks):
    for t in tasks:
        name = t.name.lower()
        if "fundacao" in name:
            t.dependencies = []
        elif "estrutura" in name:
            t.dependencies = [dep.id for dep in tasks if "fundacao" in dep.name.lower()]
        elif "alvenaria" in name:
            t.dependencies = [dep.id for dep in tasks if "estrutura" in dep.name.lower()]
        elif "acabamento" in name:
            t.dependencies = [dep.id for dep in tasks if "alvenaria" in dep.name.lower()]
