use std::collections::HashSet;
use std::fs::{self, File};
use std::io::{self, BufRead, Write};
use std::path::{Path, PathBuf};

/// Heuristic: known standard library modules (you can expand this)
fn is_std_lib(module: &str) -> bool {
    matches!(
        module,
        "os" | "sys" | "math" | "time" | "json" | "re" | "random" |
        "datetime" | "subprocess" | "threading" | "itertools" | "collections"
    )
}

/// Heuristic: check if it's a local file or directory in the project
fn is_local_module(module: &str, base_path: &Path) -> bool {
    let mut path = base_path.to_path_buf();
    path.push(format!("{}.py", module));
    if path.exists() {
        return true;
    }

    path = base_path.to_path_buf();
    path.push(module);
    path.is_dir()
}

fn extract_imports<P: AsRef<Path>>(file_path: P) -> io::Result<HashSet<String>> {
    let file = File::open(&file_path)?;
    let reader = io::BufReader::new(file);
    let base_dir = file_path.as_ref().parent().unwrap_or(Path::new("."));

    let mut requirements = HashSet::new();

    for line in reader.lines() {
        let line = line?;
        let trimmed = line.trim();

        // Skip comments
        if trimmed.starts_with('#') {
            continue;
        }

        // Match `import module` or `from module import ...`
        let module_name_opt = if trimmed.starts_with("import ") {
            trimmed.split_whitespace().nth(1)
        } else if trimmed.starts_with("from ") {
            trimmed.split_whitespace().nth(1)
        } else {
            None
        };

        if let Some(module) = module_name_opt {
            let root_module = module.split('.').next().unwrap();

            if is_std_lib(root_module) || is_local_module(root_module, base_dir) {
                continue; // Ignore local or std lib
            }

            requirements.insert(root_module.to_string());
        }
    }

    Ok(requirements)
}

fn main() -> io::Result<()> {
    let py_file = "main.py";
    let requirements = extract_imports(py_file)?;

    let mut file = File::create("requirements.txt")?;
    for dep in requirements {
        writeln!(file, "{}", dep)?;
    }

    println!("requirements.txt generated.");
    Ok(())
}
