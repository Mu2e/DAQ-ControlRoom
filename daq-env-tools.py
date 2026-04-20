#!/usr/bin/env python

import os          # For interacting with the operating system
import sys         # For system-specific parameters and functions
import argparse    # For parsing command-line arguments
import subprocess  # For executing system commands
import json        # For working with JSON data

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Process input and output files.")
# Options to control verbosity and debugging
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
parser.add_argument("-d", "--debug",   action="store_true", help="Enable debug output")
parser.add_argument("-s", "--silent",  action="store_true", help="Suppress all output")
# Options to capture and restore environment
parser.add_argument("-c", "--capture", action="store_true", help="Capture Environment (default: default_input.txt)")
parser.add_argument("-r", "--restore", action="store_true", help="Restore Environment (default: default_output.txt)")
parser.add_argument("-i", "--input",   type=str, default="default_env_in.json", help="Input filename (default: default_env_in.json)")
parser.add_argument("-o", "--output",  type=str, default="default_env_out.json", help="Output filename (default: default_env_out.json)")
parser.add_argument("-f", "--force",   action="store_true", help="Force operation even if conditions are not met")
parser.add_argument("--config",        type=str, default="env_config.json", help="Path to the configuration file")
parser.add_argument("-e", "--exec",    type=str, default=1, help="Command to execute")
                    
# Parse the arguments
args = parser.parse_args()

# Print the parsed arguments (for debugging purposes)
print(f"Input File: {args.input}")
print(f"Output File: {args.output}")

# Check if the input file exists
if args.restore and not os.path.isfile(args.input): 
    print(f"Error: Input file '{args.input}' does not exist.")
    exit(1)

# Check if the output file exists
if args.capture:
    if os.path.isfile(args.output) and not args.force:
        print(f"Error: Output file '{args.output}' already exists. Use --force to overwrite.")
        exit(1)

# Check if the configuration file exists
#if args.config and not os.path.isfile(args.config):
#    print(f"Error: Configuration file '{args.config}' does not exist.")
#    exit(1)

# Read the configuration file
#with open(args.config, 'r') as config_file:
#    config_data = config_file.read()
#    print(f"Configuration Data: {config_data}")

def get_environment_variables():
    """
    Dumps the Linux environment variables into a dictionary.
    Returns:
        dict: A dictionary containing the environment variables.
    """
    myEnv = dict(os.environ)  # Convert environment variables to a dictionary
    return myEnv

def clear_environment_variables():
    """
    Clears the current environment variables.
    This function will remove all environment variables from the current process.
    """
    for key in list(os.environ.keys()):
        del os.environ[key]
    print("Environment variables cleared.")

def store_environment_variables_json(filename):
    """
    Stores the environment variables in a JSON file.
    Args:
        env_vars (dict): The environment variables to store.
        filename (str): The name of the file to store the variables in.
    """
    env_vars = get_environment_variables()
    with open(filename, 'w') as f:
        json.dump(env_vars, f, indent=4)
    print(f"Environment variables stored in {filename}")

def restore_environment_variables_json(filename):
    """
    Restores the environment variables from a JSON file.
    Args:
        filename (str): The name of the file to restore the variables from.
    """
    with open(filename, 'r') as f:
        env_vars = json.load(f)
        for key, value in env_vars.items():
            os.environ[key] = value
    print(f"Environment variables restored from {filename}")
#
# Store environment variables in a file
def store_environment_variables(filename):
    """
    Stores the environment variables in a file.
    Args:
        env_vars (dict): The environment variables to store.
        filename (str): The name of the file to store the variables in.
    """
    env_vars = get_environment_variables
    with open(filename, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    print(f"Environment variables stored in {filename}")
#
# Restore environment variables from a file
def restore_environment_variables(filename):
    """
    Restores the environment variables from a file.
    Args:
        filename (str): The name of the file to restore the variables from.
    """
    with open(filename, 'r') as f:
        for line in f:
            key, value = line.strip().split('=', 1)
            os.environ[key] = value
    print(f"Environment variables restored from {filename}")

#
# Execute a system command
def execute_command(command):
    """
    Executes a system command and returns the output.
    Args:
        command (str): The command to execute.
    Returns:
        str: The output of the command.
    """
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while executing system command: {e}")
        return None

def store_restore_exec_command(environmentFile, command):
    """
    Stores the environment,
    Loads a new environment,
    Excutes the command, 
    and then restores the original environment.
    Args:
        command (str): The command to execute.
    """
    tempfile = "temp_env.json"
    store_environment_variables_json(tempfile)  # Store current environment
    clear_environment_variables()  # Clear current environment
    restore_environment_variables_json(environmentFile)  # Restore new environment
    # Execute the command in the new environment
    execute_command(command)
    print(f"Command executed: {command}")   
    # Clean up the environment again
    clear_environment_variables()  # Clear the new environment
    print(f"Command executed: {command}")   
    # Restore the original environment
    restore_environment_variables_json(tempfile)  # Restore original environment
    # We should have the original environment back now and can return back
    


if __name__ == "__main__":

    # Dump the environment variables
    if args.capture:    
        env = get_environment_variables()
        print("Environment Variables:")
        for key, value in env.items():
            print(f"{key}: {value}")
        # Store environment variables in a file
        store_environment_variables_json(env, args.output)
    
    # Restore variables from a file to the active environment
    if args.restore:
        restore_environment_variables_json(args.input)

# Return out successfully
exit(0)