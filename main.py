import argparse
import json
import logging
import os
import re
import sys
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define constants for supported manifest types and their associated files
MANIFEST_TYPES = {
    "npm": "package.json",
    "pip": "requirements.txt",
    "maven": "pom.xml",
}

class ManifestLinter:
    """
    A class to validate package manifest files against best practices.
    """

    def __init__(self, manifest_type: str, manifest_file: str) -> None:
        """
        Initializes the ManifestLinter with the manifest type and file path.

        Args:
            manifest_type (str): The type of manifest file (e.g., npm, pip, maven).
            manifest_file (str): The path to the manifest file.
        """
        self.manifest_type = manifest_type
        self.manifest_file = manifest_file
        self.manifest_data = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """
        Loads the manifest file based on its type.

        Returns:
            Dict[str, Any]: The loaded manifest data as a dictionary.

        Raises:
            FileNotFoundError: If the manifest file does not exist.
            ValueError: If the manifest file is not valid JSON (for npm).
            Exception: For other loading errors (e.g., parsing errors).
        """
        if not os.path.exists(self.manifest_file):
            logging.error(f"Manifest file not found: {self.manifest_file}")
            raise FileNotFoundError(f"Manifest file not found: {self.manifest_file}")

        try:
            if self.manifest_type == "npm":
                with open(self.manifest_file, 'r') as f:
                    data = json.load(f)
                return data
            elif self.manifest_type == "pip":
                with open(self.manifest_file, 'r') as f:
                    data = f.readlines()
                # Convert to a dictionary-like structure for easier processing
                return {"dependencies": [line.strip() for line in data if line.strip() and not line.startswith("#")]}
            elif self.manifest_type == "maven":
                # Implement XML parsing and data extraction for Maven POM files here
                # (requires using an XML parsing library like lxml or ElementTree)
                logging.warning("Maven linting is not fully implemented yet.")
                return {}  # Placeholder for future implementation
            else:
                logging.error(f"Unsupported manifest type: {self.manifest_type}")
                raise ValueError(f"Unsupported manifest type: {self.manifest_type}")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON in {self.manifest_file}: {e}")
            raise ValueError(f"Invalid JSON in {self.manifest_file}") from e
        except Exception as e:
            logging.error(f"Error loading manifest file {self.manifest_file}: {e}")
            raise Exception(f"Error loading manifest file: {self.manifest_file}") from e

    def lint(self) -> List[str]:
        """
        Performs linting checks on the loaded manifest data.

        Returns:
            List[str]: A list of linting messages (errors/warnings).
        """
        linting_messages = []

        # Check for common issues based on the manifest type
        if self.manifest_type == "npm":
            linting_messages.extend(self._lint_npm())
        elif self.manifest_type == "pip":
            linting_messages.extend(self._lint_pip())
        elif self.manifest_type == "maven":
            linting_messages.extend(self._lint_maven())

        return linting_messages

    def _lint_npm(self) -> List[str]:
        """
        Linting rules specific to npm (package.json) files.

        Returns:
            List[str]: A list of npm-specific linting messages.
        """
        messages = []

        # Example: Check for missing description
        if not self.manifest_data.get("description"):
            messages.append("Warning: 'description' field is missing in package.json")

        # Example: Check for missing repository URL
        if not self.manifest_data.get("repository"):
            messages.append("Warning: 'repository' field is missing in package.json")

        # Example: Check for development dependencies in production dependencies
        if "dependencies" in self.manifest_data and "devDependencies" in self.manifest_data:
            common_deps = set(self.manifest_data["dependencies"].keys()) & set(self.manifest_data["devDependencies"].keys())
            if common_deps:
                messages.append(f"Warning: The following dependencies exist in both 'dependencies' and 'devDependencies': {', '.join(common_deps)}")

        # Example:  Check for wildcard dependencies.  Avoid these.
        for dep_type in ["dependencies", "devDependencies"]:
            if dep_type in self.manifest_data:
                for dep, version in self.manifest_data[dep_type].items():
                  if "*" in version:
                      messages.append(f"Warning: Dependency {dep} has a wildcard version: {version}")

        return messages

    def _lint_pip(self) -> List[str]:
        """
        Linting rules specific to pip (requirements.txt) files.

        Returns:
            List[str]: A list of pip-specific linting messages.
        """
        messages = []

        if "dependencies" in self.manifest_data:
            for dep in self.manifest_data["dependencies"]:
                if "==" not in dep and ">=" not in dep and "<=" not in dep and "~=" not in dep:
                    messages.append(f"Warning: Dependency '{dep}' does not have a specific version specified. Consider using '==' for reproducible builds.")

                if dep.startswith("-r"):
                    messages.append(f"Info: Dependency includes another requirement file '{dep}'.  Verify included files are present.")
        return messages

    def _lint_maven(self) -> List[str]:
        """
        Linting rules specific to Maven (pom.xml) files.  This is a placeholder.

        Returns:
            List[str]: A list of Maven-specific linting messages.
        """
        #Implement XML Parsing and extraction here
        return ["Maven linting is not fully implemented yet.  This is a placeholder."]


def setup_argparse() -> argparse.ArgumentParser:
    """
    Sets up the argument parser for the command-line interface.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Validates package manifest files against best practices."
    )
    parser.add_argument(
        "--type",
        dest="manifest_type",
        required=True,
        choices=MANIFEST_TYPES.keys(),
        help="The type of manifest file (e.g., npm, pip, maven).",
    )
    parser.add_argument(
        "--file",
        dest="manifest_file",
        required=True,
        help="The path to the manifest file.",
    )
    return parser


def main() -> int:
    """
    The main function that parses arguments, performs linting, and prints results.

    Returns:
        int: The exit code (0 for success, 1 for error).
    """
    parser = setup_argparse()
    args = parser.parse_args()

    try:
        linter = ManifestLinter(args.manifest_type, args.manifest_file)
        linting_messages = linter.lint()

        if linting_messages:
            print("Linting results:")
            for message in linting_messages:
                print(message)
            return 1  # Indicate that linting issues were found
        else:
            print("No linting issues found.")
            return 0  # Indicate success

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    # Example Usage
    # Assuming you have a package.json file:
    #   python main.py --type npm --file package.json
    #
    # Assuming you have a requirements.txt file:
    #   python main.py --type pip --file requirements.txt
    #
    # Assuming you have a pom.xml file:
    #   python main.py --type maven --file pom.xml
    sys.exit(main())