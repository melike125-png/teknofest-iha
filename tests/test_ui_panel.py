# test_ui_panel.py

import cv2
import numpy as np

from ui import UISystem, DISPLAY_WIDTH, DISPLAY_HEIGHT


WINDOW_NAME = "TEKNOFEST IHA GOREV PANEL TESTI"


def main():

    frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)

    panel_info = {
        "mission_state": "HEDEFE_HIZALANIYOR",
        "searched_target": "kirmizi_ucgen",
        "selected_target": "kirmizi_ucgen",
        "confidence_text": "0.87",
        "direction": "MERKEZDE",
        "stability": "3/5",
        "payload_status": "BEKLIYOR",
        "fps": 24.5,
    }

    ui = UISystem()
    ui.draw_mission_panel(frame, panel_info)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, DISPLAY_WIDTH, DISPLAY_HEIGHT)
    cv2.imshow(WINDOW_NAME, frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
