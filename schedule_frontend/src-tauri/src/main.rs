#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    fs,
    io::{Read, Write},
    net::{SocketAddr, TcpStream},
    path::PathBuf,
    sync::Mutex,
    time::{Duration, Instant},
};
#[cfg(windows)]
use std::os::windows::process::CommandExt;

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, RunEvent,
};
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};
#[allow(unused_imports)]
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

const BACKEND_HOST: &str = "127.0.0.1";
const BACKEND_PORT: u16 = 18765;

struct BackendProcessState(Mutex<Option<CommandChild>>);

#[tauri::command]
fn read_text_file(path: String) -> Result<String, String> {
    let file_path = PathBuf::from(&path);
    let metadata =
        fs::metadata(&file_path).map_err(|error| format!("无法访问所选文件：{error}"))?;

    if !metadata.is_file() {
        return Err("所选路径不是文件。".to_string());
    }

    if let Some(extension) = file_path.extension().and_then(|value| value.to_str()) {
        let extension = extension.to_ascii_lowercase();
        if extension != "json" && extension != "txt" {
            return Err("仅支持 .json 或 .txt 文件。".to_string());
        }
    }

    fs::read_to_string(&file_path)
        .map_err(|error| format!("无法按 UTF-8 文本读取所选文件：{error}"))
}

fn reveal_main_window(app: &tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

fn backend_socket_addr() -> SocketAddr {
    SocketAddr::from(([127, 0, 0, 1], BACKEND_PORT))
}

fn backend_url() -> String {
    format!("http://{BACKEND_HOST}:{BACKEND_PORT}")
}

fn is_backend_port_open() -> bool {
    TcpStream::connect_timeout(&backend_socket_addr(), Duration::from_millis(500)).is_ok()
}

fn backend_health_ok() -> bool {
    let Ok(mut stream) =
        TcpStream::connect_timeout(&backend_socket_addr(), Duration::from_millis(700))
    else {
        return false;
    };

    let _ = stream.set_read_timeout(Some(Duration::from_millis(900)));
    let request = format!(
        "GET /api/health HTTP/1.1\r\nHost: {BACKEND_HOST}:{BACKEND_PORT}\r\nConnection: close\r\n\r\n"
    );
    if stream.write_all(request.as_bytes()).is_err() {
        return false;
    }

    let mut response = String::new();
    if stream.read_to_string(&mut response).is_err() {
        return false;
    }

    response.contains("200 OK")
        && response.contains("\"code\":0")
        && response.contains("\"status\":\"ok\"")
}

fn wait_backend_healthy(timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if backend_health_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(500));
    }
    false
}

fn backend_data_dir(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    if let Some(app_data) = std::env::var_os("APPDATA") {
        return Ok(PathBuf::from(app_data).join("日程安排"));
    }

    app.path()
        .app_data_dir()
        .map_err(|error| format!("无法获取用户数据目录：{error}"))
}

#[cfg(not(debug_assertions))]
fn ensure_backend_running(app: &tauri::AppHandle) -> Result<(), String> {
    if backend_health_ok() {
        return Ok(());
    }

    if is_backend_port_open() {
        return Err(format!(
            "本地服务端口 {BACKEND_PORT} 已被其他程序占用。\n请关闭占用该端口的程序后重新打开日程安排。"
        ));
    }

    let data_dir = backend_data_dir(app)?;
    fs::create_dir_all(&data_dir).map_err(|error| {
        format!(
            "无法创建用户数据目录：{}\n{error}",
            data_dir.to_string_lossy()
        )
    })?;

    let sidecar = app
        .shell()
        .sidecar("schedule-backend")
        .map_err(|error| format!("无法定位内置后端程序：{error}"))?
        .env("SCHEDULE_HOST", BACKEND_HOST)
        .env("SCHEDULE_PORT", BACKEND_PORT.to_string())
        .env("SCHEDULE_DATA_DIR", data_dir.to_string_lossy().to_string());

    let (mut rx, child) = sidecar
        .spawn()
        .map_err(|error| format!("无法启动内置后端程序：{error}"))?;

    {
        let state = app.state::<BackendProcessState>();
        let mut guard = state
            .0
            .lock()
            .map_err(|_| "后端进程状态锁定失败。".to_string())?;
        *guard = Some(child);
    }

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    let text = String::from_utf8_lossy(&line);
                    eprintln!("[schedule-backend] {text}");
                }
                CommandEvent::Stderr(line) => {
                    let text = String::from_utf8_lossy(&line);
                    eprintln!("[schedule-backend:error] {text}");
                }
                CommandEvent::Error(error) => {
                    eprintln!("[schedule-backend:error] {error}");
                }
                CommandEvent::Terminated(payload) => {
                    eprintln!("[schedule-backend] terminated: {payload:?}");
                    break;
                }
                _ => {}
            }
        }
    });

    if wait_backend_healthy(Duration::from_secs(120)) {
        return Ok(());
    }

    stop_backend(app);
    Err(format!(
        "内置后端启动超时。\n请确认本机安全软件没有拦截日程安排，并重新打开应用。\n健康检查地址：{}/api/health",
        backend_url()
    ))
}

#[cfg(debug_assertions)]
fn ensure_backend_running(_app: &tauri::AppHandle) -> Result<(), String> {
    Ok(())
}

fn stop_backend(app: &tauri::AppHandle) {
    let state = app.state::<BackendProcessState>();
    if let Ok(mut guard) = state.0.lock() {
        if let Some(child) = guard.take() {
            let _ = child.kill();
        }
    };

    #[cfg(windows)]
    {
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        let _ = std::process::Command::new("taskkill")
            .args([
                "/F",
                "/T",
                "/IM",
                "schedule-backend-x86_64-pc-windows-msvc.exe",
            ])
            .creation_flags(CREATE_NO_WINDOW)
            .output();
    }
}

fn show_startup_error(app: &tauri::AppHandle, message: &str) {
    app.dialog()
        .message(message)
        .title("日程安排启动失败")
        .kind(MessageDialogKind::Error)
        .blocking_show();
}

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            app.manage(BackendProcessState(Mutex::new(None)));

            if let Err(error) = ensure_backend_running(app.handle()) {
                show_startup_error(app.handle(), &error);
                app.handle().exit(1);
                return Ok(());
            }

            let show_item = MenuItem::with_id(app, "show", "显示主窗口", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "退出应用", true, None::<&str>)?;
            let tray_menu = Menu::with_items(app, &[&show_item, &quit_item])?;

            let mut tray_builder = TrayIconBuilder::new()
                .menu(&tray_menu)
                .show_menu_on_left_click(false)
                .tooltip("日程安排")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => reveal_main_window(app),
                    "quit" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        reveal_main_window(&app);
                    }
                });

            if let Some(icon) = app.default_window_icon() {
                tray_builder = tray_builder.icon(icon.clone());
            }

            tray_builder.build(app)?;
            reveal_main_window(app.handle());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![read_text_file])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let RunEvent::ExitRequested { .. } = event {
            stop_backend(app_handle);
        }
    });
}
