use std::collections::HashSet;
use std::fs::{self, File};
use std::io::{self, BufRead, Write};
use std::path::{Path, PathBuf};

/// Determines if a module name matches a known Python standard library module.
///
/// Returns `true` if the provided module is recognized as a standard library module; otherwise, returns `false`.
///
/// # Examples
///
/// ```
/// assert!(is_std_lib("os"));
/// assert!(!is_std_lib("requests"));
/// ```
fn is_std_lib(module: &str) -> bool {
    matches!(
        module,
        "os" | "sys" | "math" | "time" | "json" | "re" | "random" |
        "datetime" | "subprocess" | "threading" | "itertools" | "collections"
    )
}

/// Determines if a module corresponds to a local Python file or directory within the given project path.
///
/// Returns `true` if a file named `<module>.py` or a directory named `<module>` exists in `base_path`; otherwise, returns `false`.
///
/// # Examples
///
/// ```
/// use std::path::Path;
/// assert!(is_local_module("my_module", Path::new("./src")));
/// assert!(!is_local_module("nonexistent", Path::new("./src")));
/// ```
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

/// Extracts external Python module dependencies from a source file.
///
/// Reads the specified Python file, parses import statements, and collects the names of modules that are neither standard library nor local project modules. Returns a set of root module names representing external dependencies.
///
/// # Returns
///
/// A `HashSet<String>` containing the names of external modules imported in the file.
///
/// # Errors
///
/// Returns an `io::Error` if the file cannot be read.
///
/// # Examples
///
/// ```
/// let deps = extract_imports("main.py")?;
/// assert!(deps.contains("requests"));
/// ```
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

/// Entry point for generating a `requirements.txt` file from a Python source file.
///
/// Analyzes `main.py` to extract external module dependencies and writes them to
/// `requirements.txt`, with one dependency per line. Prints a confirmation message upon success.
///
/// # Errors
///
/// Returns an error if reading `main.py` or writing `requirements.txt` fails.
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
