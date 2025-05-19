def main(code):
    requirements = set()
    for line in code.split("\n"):
        line = line.strip()
        if line.startswith("import ") or line.startswith("from "):
            # Extract the module name
            if line.startswith("import "):
                module = line.replace("import ", "").split()[0]
            else:  # from ... import ...
                module = line.split()[1]

            # Remove any potential alias
            module = module.split(" as ")[0]

            # Add to requirements (using a set to avoid duplicates)
            requirements.add(module)

    # Convert requirements to a format suitable for requirements.txt
    return "\n".join(sorted(requirements))
