import os
import sys
import platform
import subprocess
import shutil

# =============================================================================
# Configuration
# =============================================================================
GSASII_SVN_URL = "https://subversion.xray.aps.anl.gov/pyGSAS/trunk/GSASII"
INSTALL_DIR_NAME = "GSASII"


# =============================================================================
# Helper for Colored Output
# =============================================================================
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_color(text, color, bold=False):
    """Prints text in a given color."""
    if bold:
        print(f"{color}{Colors.BOLD}{text}{Colors.ENDC}")
    else:
        print(f"{color}{text}{Colors.ENDC}")


# =============================================================================
# The Installer Class
# =============================================================================

class Gsas2Installer:
    """Handles the step-by-step installation of GSAS-II."""

    def __init__(self):
        self.os_type = platform.system()
        self.install_path = os.path.join(os.path.expanduser('~'), INSTALL_DIR_NAME)

    def run(self):
        """Executes the full installation process."""
        self._print_welcome()

        if self.os_type not in ["Windows", "Linux"]:
            print_color(f"Unsupported OS: {self.os_type}. This script supports Windows and Linux.", Colors.FAIL)
            sys.exit(1)

        if not self._check_svn():
            if not self._install_svn():
                sys.exit(1)

        if not self._checkout_gsas2():
            sys.exit(1)

        if not self._install_gsas2_dependencies():
            sys.exit(1)

        self._print_success()

    def _print_welcome(self):
        print_color("--- oneXRD GSAS-II Dependency Installer ---", Colors.HEADER, bold=True)
        print("This script will guide you through installing GSAS-II and its dependencies.")
        print(f"GSAS-II will be installed in: {self.install_path}\n")

    def _check_svn(self):
        """Checks if the 'svn' command is available in the system PATH."""
        print_color("Step 1: Checking for SVN (Subversion)...", Colors.OKCYAN)
        try:
            subprocess.run(["svn", "--version"], check=True, capture_output=True)
            print_color("--> SVN is already installed. Proceeding.", Colors.OKGREEN)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_color("--> SVN is not found.", Colors.WARNING)
            return False

    def _install_svn(self):
        """Guides the user through installing SVN."""
        print_color("\nStep 2: Installing SVN...", Colors.OKCYAN)
        if self.os_type == "Windows":
            return self._install_svn_windows()
        elif self.os_type == "Linux":
            return self._install_svn_linux()
        return False

    def _install_svn_windows(self):
        print("On Windows, SVN must be installed manually.")
        print_color("Please follow these steps:", Colors.HEADER, bold=True)
        print("1. Download the VisualSVN command-line tools from here:")
        print_color("   https://www.visualsvn.com/visualsvn/download/tortoisesvn/", Colors.OKBLUE)
        print("2. Run the installer.")
        print_color("3. IMPORTANT: During installation, ensure you enable the 'command-line client tools'.",
                    Colors.WARNING, bold=True)
        print("   This option ensures the 'svn' command is added to your system's PATH.")
        print("4. After installation is complete, you may need to restart your terminal or command prompt.")

        input(
            f"\n{Colors.BOLD}Press Enter here after you have successfully installed the SVN command-line tools...{Colors.ENDC}")

        return self._check_svn()

    def _install_svn_linux(self):
        print("This script will attempt to install SVN using 'apt-get'.")
        print_color("This requires administrator (sudo) privileges.", Colors.WARNING)

        cmd = "sudo apt-get update && sudo apt-get install -y subversion"
        print(f"Running command: {cmd}")

        try:
            subprocess.run(cmd, shell=True, check=True)
            print_color("SVN installed successfully.", Colors.OKGREEN)
            return True
        except subprocess.CalledProcessError as e:
            print_color(f"SVN installation failed. Please try running '{cmd}' manually in your terminal.", Colors.FAIL)
            return False

    def _checkout_gsas2(self):
        """Checks out GSAS-II from the SVN repository."""
        print_color(f"\nStep 3: Checking out GSAS-II from SVN repository...", Colors.OKCYAN)
        if os.path.exists(self.install_path):
            print_color(f"--> Directory '{self.install_path}' already exists. Skipping checkout.", Colors.WARNING)
            return True

        try:
            # We stream the output so the user can see the progress
            process = subprocess.run(
                ["svn", "checkout", GSASII_SVN_URL, self.install_path],
                check=True
            )
            print_color("GSAS-II checked out successfully.", Colors.OKGREEN)
            return True
        except subprocess.CalledProcessError:
            print_color("Failed to check out GSAS-II from SVN.", Colors.FAIL)
            return False

    def _install_gsas2_dependencies(self):
        """Runs the GSAS-II bootstrap script to install Python packages."""
        print_color("\nStep 4: Installing GSAS-II Python dependencies...", Colors.OKCYAN)
        bootstrap_script = os.path.join(self.install_path, "bootstrap.py")

        if not os.path.exists(bootstrap_script):
            print_color(f"Could not find bootstrap.py at '{bootstrap_script}'.", Colors.FAIL)
            return False

        print(f"Running {bootstrap_script} with Python executable: {sys.executable}")
        print("This may take several minutes...")

        try:
            # Run bootstrap.py using the *same* python that is running this script
            subprocess.run([sys.executable, bootstrap_script], check=True, cwd=self.install_path)
            print_color("GSAS-II dependencies installed successfully.", Colors.OKGREEN)
            return True
        except subprocess.CalledProcessError:
            print_color("Failed to install GSAS-II dependencies.", Colors.FAIL)
            print_color("Please try running 'python bootstrap.py' manually inside the GSASII directory.",
                        Colors.WARNING)
            return False

    def _print_success(self):
        print_color("\n--- Installation Complete! ---", Colors.OKGREEN, bold=True)
        print("GSAS-II and its dependencies should now be installed.")
        print_color("What to do next:", Colors.HEADER, bold=True)
        print("1. Add the GSAS-II installation directory to your system's PYTHONPATH.")
        print_color(f"   Directory to add: {self.install_path}", Colors.OKCYAN, bold=True)
        print("2. Restart the oneXRD application.")
        print("The Rietveld refinement plugin should now be available.")


if __name__ == "__main__":
    installer = Gsas2Installer()
    installer.run()