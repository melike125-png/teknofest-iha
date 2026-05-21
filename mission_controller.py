# mission_controller.py

from state_machine import MissionState
from infinity8 import Infinity8Mission
from search import SearchMission
from memory import TargetMemorySystem


class MissionController:

    def __init__(self):

        self.state = MissionState.IDLE

        self.infinity8 = Infinity8Mission()
        self.search = SearchMission()
        self.memory = TargetMemorySystem()

        self.mission1_completed = False
        self.mission2_completed = False

    def start(self):

        self.state = MissionState.TAKEOFF

    def set_state(self, new_state):

        print(f"GOREV MODU DEGISTI: {self.state} -> {new_state}")

        self.state = new_state

    def update_after_takeoff(self):

        self.set_state(MissionState.MISSION_1_INFINITY8)

    def update_mission1(self):

        if self.infinity8.is_completed():

            self.mission1_completed = True

            self.set_state(MissionState.MISSION_2_SEARCH)

        else:

            target_point = self.infinity8.get_current_target_point()

            print(f"Sonsuz 8 hedef noktasi: {target_point}")

            self.infinity8.move_to_next_point()

    def update_search(self, target_data):

        if target_data is not None:

            self.memory.update(target_data)

            self.set_state(MissionState.TARGET_LOCK)

            return

        if self.search.is_completed():

            self.mission2_completed = True

            self.set_state(MissionState.FINISHED)

            return

        search_point = self.search.get_current_point()

        print(f"Alan tarama noktasi: {search_point}")

        self.search.move_next()

    def update_target_lock(self):

        remembered_target = self.memory.get_last_target()

        if remembered_target is None:

            self.set_state(MissionState.MISSION_2_SEARCH)

            return

        print(f"Hedefe kilitlenildi: {remembered_target['class_name']}")

        self.set_state(MissionState.APPROACH)

    def update_approach(self):

        print("Hedefe yaklasiliyor...")

        self.set_state(MissionState.DESCEND)

    def update_descend(self):

        print("Irtifa dusuruluyor...")

        self.set_state(MissionState.DROP_PAYLOAD)

    def update_drop(self):

        print("Yuk birakma asamasina gecildi.")

        self.set_state(MissionState.ASCEND)

    def update_ascend(self):

        print("Tekrar guvenli irtifaya cikiliyor...")

        self.set_state(MissionState.RETURN_TO_SEARCH)

    def update_return_to_search(self):

        print("Alan taramaya geri donuluyor...")

        self.set_state(MissionState.MISSION_2_SEARCH)

    def update(self, target_data=None):

        if self.state == MissionState.IDLE:
            self.start()

        elif self.state == MissionState.TAKEOFF:
            self.update_after_takeoff()

        elif self.state == MissionState.MISSION_1_INFINITY8:
            self.update_mission1()

        elif self.state == MissionState.MISSION_2_SEARCH:
            self.update_search(target_data)

        elif self.state == MissionState.TARGET_LOCK:
            self.update_target_lock()

        elif self.state == MissionState.APPROACH:
            self.update_approach()

        elif self.state == MissionState.DESCEND:
            self.update_descend()

        elif self.state == MissionState.DROP_PAYLOAD:
            self.update_drop()

        elif self.state == MissionState.ASCEND:
            self.update_ascend()

        elif self.state == MissionState.RETURN_TO_SEARCH:
            self.update_return_to_search()

        elif self.state == MissionState.FINISHED:
            print("Tum gorevler tamamlandi.")