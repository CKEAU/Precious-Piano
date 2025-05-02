import time
import arcade
import os
import sys
import logging
import pyglet
from pathlib import Path
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('piano_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

SCREEN_WIDTH = 1380
SCREEN_HEIGHT = 1280
SCREEN_TITLE = "PRECIOUS PIANO"


def generate_note_map():
    note_names = []
    for midi_num in range(21, 109):
        note_index = (midi_num - 12) % 12
        octave = (midi_num - 12) // 12
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note_names.append(f"{notes[note_index]}{octave}")
    return {name: idx + 1 for idx, name in enumerate(note_names)}


NOTE_MAP = generate_note_map()
KEY_MAPPING = {
    (arcade.key.D, arcade.key.O): 'C4',
    (arcade.key.R, arcade.key.E): 'D4',
    (arcade.key.M, arcade.key.I): 'E4',
    (arcade.key.F, arcade.key.A): 'F4',
    (arcade.key.S, arcade.key.O,arcade.key.L): 'G4',
    (arcade.key.L, arcade.key.A): 'A4',
    (arcade.key.S, arcade.key.I): 'B4',
    arcade.key.A: 'C5',
    arcade.key.W: 'D5',
    arcade.key.S: 'E5',
    arcade.key.E: 'F5',
    arcade.key.D: 'G5',
    arcade.key.F: 'A5',
    arcade.key.T: 'B5',
    arcade.key.MOD_SHIFT: +1,
    arcade.key.MOD_CAPSLOCK: -1
}


class VirtualPiano(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.sounds = {}
        self.audio_dir = self.auto_detect_audio_dir()
        self.load_sounds()
        self.set_vsync(True)  # 启用垂直同步

        self.pressed_keys = set()
        self.check_key_combinations()
        self.current_octave = 5  # 初始八度（C4）
        self.setup_ui()
        self.check_key_combinations()
        self.set_update_rate(1 / 60)
        arcade.set_background_color(arcade.color.BLACK)

    def auto_detect_audio_dir(self):
        possible_paths = [
            Path(__file__).parent,
            Path.home() / "Downloads" / "钢琴88键独立音频文件",
            Path.cwd()
        ]
        for path in possible_paths:
            if (path / "tone (1).wav").exists():
                return str(path.resolve())
        raise FileNotFoundError("音频目录未找到")

    def load_sounds(self):
        logging.info(f"加载音频文件，目录: {self.audio_dir}")
        for i in range(1, 89):
            for fmt in [f"tone{i:03d}.wav", f"tone {i}.wav", f"tone ({i}).wav"]:
                full_path = Path(self.audio_dir) / fmt
                if full_path.exists():
                    try:
                        self.sounds[f"tone{i:03d}"] = arcade.load_sound(str(full_path))
                        logging.info(f"已加载: {full_path}")
                        break
                    except Exception as e:
                        logging.error(f"加载失败 {full_path}: {str(e)}")

    def setup_ui(self):
        self.key_display = arcade.Text(
            "八度: "+str(self.current_octave)+" | 组合键示例: D+O=C | 单键示例: A=C | Caps=↑Oct | Shift=↓Oct",
            x=10, y=SCREEN_HEIGHT - 30, color=arcade.color.ARCADE_GREEN, font_size=14
        )

    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 40, SCREEN_HEIGHT, arcade.color.ANDROID_GREEN)
        self.key_display.draw()

    def on_key_press(self, key, modifiers):
        self.pressed_keys.add(key)
        #self.check_key_combinations()
        #if arcade.key.CAPSLOCK:
            #try:
            #self.current_octave+=1
            #except IndexError:
            #    logging.log(f"太高了啦")
        #if arcade.key.LSHIFT:
            #print("1")
            #try:
            #self.current_octave -= 1
            #except IndexError:
             #   logging.log(f"这有点低了哦")
        self.update_ui()
    def on_key_release(self, key, modifiers):
        #self.check_key_combinations()
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        self.update_ui()

    def update_ui(self):
        self.check_key_combinations()
        keys_text = ", ".join(
            self.key_to_string(k)
            for k in sorted(self.pressed_keys)
        )
        self.key_display.text = (
            f"八度: {self.current_octave} | 按下的键: {keys_text}"
        )

    def check_key_combinations(self):
        pressed = self.pressed_keys
        if arcade.key.LSHIFT in pressed:
            if self.current_octave<=8:
                self.current_octave += 1
                logging.info(f"八度升高至: {self.current_octave}")
            else:
                logging.info(f"超出音域")
        if arcade.key.CAPSLOCK in pressed:
            if self.current_octave>=1:
                self.current_octave -= 1
                logging.info(f"八度降低至: {self.current_octave}")
            else:
                logging.info(f"超出音域")
        for combo, note in KEY_MAPPING.items():
            if isinstance(combo, tuple):
                if all(k in pressed for k in combo):
                    self.play_note(note)
                    return
            else:
                if combo in pressed:
                    self.play_note(note)
                    return

    def play_note(self, base_note):
        note_name = f"{base_note[0]}{self.current_octave}"
        if note_name in NOTE_MAP:
            self.play_sound(NOTE_MAP[note_name])
        else:
            logging.error(f"无效音高: {note_name}")

    def play_sound(self, note_number):
        tone_num = max(1, min(88, note_number))
        sound_key = f"tone{tone_num:03d}"
        if sound_key in self.sounds:
            arcade.play_sound(self.sounds[sound_key])
            logging.info(f"播放: {sound_key}")
        else:
            logging.error(f"音频未找到: {sound_key}")

    def key_to_string(self, key):
        for name, val in vars(arcade.key).items():
            if val == key:
                if name.startswith('KEY_'):
                    return name[4:].replace('_', '')
                return name
        return f"KEY_{key}"


def main():
    try:
        window = VirtualPiano()
        arcade.run()
    except Exception as e:
        logging.exception("程序炸了（不是，崩溃）")


if __name__ == "__main__":
    main()