import qrcode
import os
import subprocess
import sys

# --- 設定 ---
CONFIG = {
    "text": "https://mihatama.com/",  # QRコードにするテキスト
    "line_width": 0.8,              # 1ドットの幅 (mm)
    "base_thickness": 2.0,          # ベースの厚み (mm)
    "qr_height": 1.0,               # QRコードの高さ (mm)
    "taper_angle": 0.0,             # 垂直からのテーパー角度 (度)
    "corner_radius": 0.1,           # 外周の角の丸め半径 (mm)
    "output_filename_scad": "qrcode_model.scad",
}
# --- 設定ここまで ---

def create_scad_file(config):
    """設定に基づいて.scadファイルを生成する"""

    # 1. QRコードのデータを生成
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=4,
    )
    qr.add_data(config["text"])
    qr.make(fit=True)
    qr_matrix = [[bool(cell) for cell in row] for row in qr.get_matrix()]
    module_count = len(qr_matrix)
    print(f"QRコードのデータを生成しました ({module_count}x{module_count} モジュール)")

    # 2. .scadファイルの内容を準備
    scad_content = f'''
// qr2step.pyによって生成されました
// --- パラメータ ---
line_width = {config["line_width"]};
base_thickness = {config["base_thickness"]};
qr_height = {config["qr_height"]};
taper_angle = {config["taper_angle"]};
corner_radius = {config.get("corner_radius", 0.1)};

// --- QRデータ ---
qr_matrix = {str(qr_matrix).replace("False", "0").replace("True", "1")};

// --- モデル ---
module_count = len(qr_matrix);
total_width = module_count * line_width;

// テーパー計算 (taper_angle=0 の場合は scale=1)
taper_top_reduction = qr_height * tan(taper_angle) * 2;
final_scale = (line_width > taper_top_reduction) ? (line_width - taper_top_reduction) / line_width : 0.01;

// ベースプレート
cube([total_width, total_width, base_thickness]);

// QRコードブロック
translate([0, 0, base_thickness]) {{
    linear_extrude(height = qr_height, scale = final_scale, convexity = 10) {{
        // 二重のoffsetを使い、外周の角のみを丸める
        // これにより、全体の寸法と線幅を維持する
        offset(r = -corner_radius, $fn=32) {{
            offset(r = corner_radius, $fn=32) {{
                union() {{
                    for (r = [0:module_count-1]) {{
                        for (c = [0:module_count-1]) {{
                            if (qr_matrix[r][c] == 1) {{
                                translate([c * line_width, (module_count - 1 - r) * line_width, 0]) {{
                                    square(line_width);
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
'''

    # 3. .scadファイルを書き出す
    try:
        with open(config["output_filename_scad"], "w", encoding='utf-8') as f:
            f.write(scad_content)
        print(f"'{config['output_filename_scad']}' を正常に保存しました。")
    except IOError as e:
        print(f"エラー: ファイルの書き込みに失敗しました。 {e}", file=sys.stderr)
        return False
    return True

if __name__ == '__main__':
    create_scad_file(CONFIG)