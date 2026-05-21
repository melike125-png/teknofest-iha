# test_mission_controller.py

from mission_controller import MissionController


controller = MissionController()

for i in range(120):

    print("-" * 40)
    print(f"ADIM: {i}")

    if i == 90:
        fake_target = {
            "class_name": "mavi_altigen",
            "confidence": 0.88,
            "error_x": 10,
            "error_y": -5
        }

        controller.update(fake_target)

    else:
        controller.update()