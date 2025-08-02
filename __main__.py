from oneXRD.main_app import MainApplication

def start_app():
    """
    Initializes and runs the main application.
    """
    try:
        app = MainApplication()
        app.run()
    except Exception as e:
        # A top-level catch for any unexpected startup errors
        print(f"FATAL ERROR: Could not start oneXRD application.")
        print(f"Reason: {e}")
        # In a real distribution, we would log this to a file.
        # For now, printing is sufficient.

if __name__ == "__main__":
    print("Starting oneXRD...")
    start_app()
    print("oneXRD has closed. Goodbye!")
