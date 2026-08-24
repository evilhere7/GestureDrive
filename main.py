import sys
import argparse
from app.logger import get_logger

logger = get_logger("Main")


def parse_args():
    parser = argparse.ArgumentParser(
        description="GestureDrive — Virtual Gesture Steering Wheel for Racing Games"
    )
    parser.add_argument("--simulation", action="store_true",
                        help="Launch directly in Simulation Mode (no key injection)")
    parser.add_argument("--camera", type=int, default=None,
                        help="Specify camera device index")
    parser.add_argument("--profile", type=str, default=None,
                        help="Load a specific game profile on startup (e.g. forza, beamng, f1)")
    parser.add_argument("--racing", action="store_true",
                        help="Enable Racing Mode HUD on launch")
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info("Initializing GestureDrive...")

    from ui.dashboard import DashboardApp
    app = DashboardApp()

    if args.simulation:
        logger.info("Starting in Simulation Mode (--simulation flag).")
        app.combo_input_mode.set("SIMULATION")
        app._on_input_mode_change("SIMULATION")

    if args.camera is not None:
        app.config.camera.device_index = args.camera
        app.camera_manager.device_index = args.camera
        logger.info(f"Camera override: index {args.camera}")

    if args.profile is not None:
        logger.info(f"Loading profile: {args.profile}")
        app._on_profile_change(args.profile)
        app.combo_profiles.set(args.profile)

    if args.racing:
        app.racing_mode = True
        app.config.racing_mode = True
        app.lbl_mode_badge.configure(text="RACING MODE", text_color="#ff5500")

    app.lift()
    app.focus_force()
    app.attributes('-topmost', True)
    app.after(1200, lambda: app.attributes('-topmost', False))

    app.mainloop()


if __name__ == "__main__":
    main()
