# flight_controller.py

class FlightController:

    def __init__(self):
        self.connected = False

    def connect(self):
        print("Pixhawk baglantisi simdilik test modunda.")
        self.connected = False

    def takeoff(self, altitude):
        print(f"TEST MODU -> {altitude} metreye kalkis")

    def move_to_point(self, x, y, altitude):
        print(f"TEST MODU -> Noktaya git: X={x}, Y={y}, Irtifa={altitude}")

    def search_forward(self):
        print("TEST MODU -> Ileri tarama")

    def yaw_scan(self, angle):
        print(f"TEST MODU -> Yaw tarama: {angle} derece")

    def approach_target(self, error_x, error_y):
        print(f"TEST MODU -> Hedefe yaklas | X hata: {error_x}, Y hata: {error_y}")

    def descend(self, altitude):
        print(f"TEST MODU -> {altitude} metreye alcal")

    def ascend(self, altitude):
        print(f"TEST MODU -> {altitude} metreye yuksel")

    def hover(self):
        print("TEST MODU -> Hover")

    def land(self):
        print("TEST MODU -> Inis")