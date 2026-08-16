import sys
import argparse
from app.logger import get_logger
from ui.dashboard import DashboardApp

logger = get_logger("Main")

def parse_args():
    parser = argparse.ArgumentParser(description="GestureDrive - Virtual Gesture Steering Wheel")
    parser.add_argument("--simulation", action="store_true", help="Launch directly in Simulation mode without key injection")
    parser.add_argument("--camera", type=int, default=None, help="Specify default camera index")
    return parser.parse_args()

def main():
    args = parse_args()
    logger.info("Initializing GestureDrive Application...")

    app = DashboardApp()

    if args.simulation:
        logger.info("Starting directly in Simulation Mode via CLI flag.")
        app.combo_input_mode.set("SIMULATION")
        app._on_input_mode_change("SIMULATION")

    if args.camera is not None:
        app.config.camera.device_index = args.camera
        app.camera_manager.device_index = args.camera

    app.mainloop()

if __name__ == "__main__":
    main()
