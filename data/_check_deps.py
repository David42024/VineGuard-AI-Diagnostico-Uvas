import pkg_resources
for pkg in ['pydantic', 'pydantic-core', 'fastapi', 'starlette', 'sqlalchemy']:
    try:
        d = pkg_resources.get_distribution(pkg)
        reqs = d.requires()
        te_reqs = [str(r) for r in reqs if 'typing' in str(r)]
        msg = ", ".join(te_reqs) if te_reqs else "no typing-extensions constraint"
        print(f"{d.project_name} {d.version}: {msg}")
    except Exception as e:
        print(f"{pkg}: {e}")
