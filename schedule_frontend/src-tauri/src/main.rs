#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{fs, path::PathBuf};

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager,
};

#[tauri::command]
fn read_text_file(path: String) -> Result<String, String> {
    let file_path = PathBuf::from(&path);
    let metadata = fs::metadata(&file_path)
        .map_err(|error| format!("无法访问所选文件：{error}"))?;

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

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
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
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![read_text_file])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
