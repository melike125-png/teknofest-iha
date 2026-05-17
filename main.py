# main.py

from config import PROJECT_NAME
from mission import MissionSystem

def main():

    print("=" * 50)
    print(PROJECT_NAME)
    print("Sistem baslatiliyor...")
    print("=" * 50)

    mission = MissionSystem()

    mission.start()

if __name__ == "__main__":
    main()