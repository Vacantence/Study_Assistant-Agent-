use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use tauri::Manager;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

include!(concat!(env!("OUT_DIR"), "/backend_files.rs"));

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let handle = app.handle();

            if cfg!(debug_assertions) {
                handle.plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let (_backend_dir, run_api_path, cwd) = prepare_backend(&handle);
            let _ = fs::create_dir_all(&cwd);

            let python_cmd = find_python(&cwd);

            // Spawn backend (hidden console window)
            let mut cmd = Command::new(&python_cmd);
            cmd.arg(&run_api_path)
                .current_dir(&cwd)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped());
            #[cfg(windows)]
            cmd.creation_flags(CREATE_NO_WINDOW);
            let mut child = match cmd.spawn() {
                Ok(c) => c,
                Err(e) => {
                    write_debug(&cwd, &format!("FAILED to spawn: {}", e));
                    return Err(e.into());
                }
            };
            write_debug(&cwd, "Backend spawned OK");

            // Log stdout
            let stdout = child.stdout.take().unwrap();
            let cwd_s = cwd.clone();
            std::thread::spawn(move || {
                let reader = BufReader::new(stdout);
                for line in reader.lines() {
                    if let Ok(line) = line {
                        log::info!("[backend] {}", line);
                    }
                }
            });

            // Log stderr AND write to file
            let stderr = child.stderr.take().unwrap();
            let cwd_e = cwd.clone();
            std::thread::spawn(move || {
                let mut log_file = fs::File::create(cwd_e.join("backend_stderr.log"))
                    .expect("create stderr log");
                let reader = BufReader::new(stderr);
                for line in reader.lines() {
                    if let Ok(line) = line {
                        log::error!("[backend] {}", &line);
                        let _ = writeln!(log_file, "{}", line);
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn write_debug(dir: &PathBuf, msg: &str) {
    let _ = fs::create_dir_all(dir);
    if let Ok(mut f) = fs::OpenOptions::new()
        .create(true).append(true).open(dir.join("startup_debug.log"))
    {
        let _ = writeln!(f, "{}", msg);
    }
}

fn prepare_backend(app: &tauri::AppHandle) -> (PathBuf, PathBuf, PathBuf) {
    #[cfg(debug_assertions)]
    {
        let backend_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("backend");
        let run_api_path = backend_dir.join("run_api.py");
        let cwd = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent().unwrap().parent().unwrap().to_path_buf();
        (backend_dir, run_api_path, cwd)
    }

    #[cfg(not(debug_assertions))]
    {
        let data_dir = app.path().app_data_dir()
            .expect("failed to get app data dir");
        let backend_dir = data_dir.join("backend");

        write_debug(&backend_dir, "Extracting backend files...");
        extract_backend(&backend_dir);
        write_debug(&backend_dir, "Extraction done");

        let run_api_path = backend_dir.join("run_api.py");
        (backend_dir.clone(), run_api_path, backend_dir)
    }
}

fn extract_backend(target_dir: &PathBuf) {
    fs::create_dir_all(target_dir).expect("create backend dir");
    for (relative_path, contents) in BACKEND_FILES {
        let path = target_dir.join(relative_path);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).expect("create subdir");
        }
        fs::write(&path, contents).expect("write backend file");
    }
}

fn find_python(debug_dir: &PathBuf) -> String {
    for cmd in &["python", "python3", "py"] {
        match Command::new(cmd).arg("--version").output() {
            Ok(out) => {
                let ver = String::from_utf8_lossy(&out.stdout).trim().to_string();
                write_debug(debug_dir, &format!("Found {}: {}", cmd, ver));
                return cmd.to_string();
            }
            Err(e) => {
                write_debug(debug_dir, &format!("{} not found: {}", cmd, e));
            }
        }
    }
    write_debug(debug_dir, "No Python found, using 'python' as fallback");
    "python".to_string()
}
