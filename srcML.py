import os
import subprocess
import csv
import threading
from threading import Thread
from queue import Queue
import sys
import tempfile
import functools
import time
from lxml import etree


def beautify_java_method(java_method, jar_path, timeout=3):
    """
    Beautify a Java method using google-java-format with a timeout.

    Args:
        java_method (str): The Java method code as a string.
        jar_path (str): Path to the google-java-format JAR file.
        timeout (int): Maximum allowable execution time in seconds.

    Returns:
        str: The beautified Java method or None if the process times out.
    """
    # Check if the JAR file exists
    if not os.path.isfile(jar_path):
        raise FileNotFoundError(f"google-java-format JAR file not found at {jar_path}")

    # Wrap the method in a fake Java class
    fake_class = f"""
    public class Scaffold {{
        {java_method}
    }}
    """

    # Create a temporary file to hold the Java code
    with tempfile.NamedTemporaryFile(delete=False, suffix=".java") as temp_file:
        temp_file.write(fake_class.encode('utf-8'))
        temp_file_path = temp_file.name

    try:
        # Use the google-java-format JAR to format the file
        command = ["java", "-jar", jar_path, "--replace", temp_file_path]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                raise Exception(f"Error during formatting: {result.stderr}")

            # Read the formatted content back
            with open(temp_file_path, "r") as formatted_file:
                formatted_code = formatted_file.read()

            # Extract the formatted method from the fake class
            start = formatted_code.index("{", formatted_code.index("class")) + 1
            end = formatted_code.rindex("}")
            formatted_method = formatted_code[start:end].strip()

            return formatted_method
        except subprocess.TimeoutExpired:
            print(f"Timeout: Formatting the Java method took longer than {timeout} seconds.")
            return None
    finally:
        # Clean up the temporary file
        os.remove(temp_file_path)



def extract_raw_java_tokens_from_xml(method_code_xml):
    """
    Extract raw Java tokens from method code in XML format.

    Args:
        method_code_xml (str): The method code in XML format.

    Returns:
        str: Raw Java code tokens.
    """
    parser = etree.XMLParser(ns_clean=True, recover=True)
    tree = etree.fromstring(method_code_xml.encode('utf-8'), parser)
    tokens = tree.xpath(".//text()")
    raw_code = ' '.join(tokens).strip()
    return raw_code

def extract_methods_with_srcml(repo_path, output_csv):
    """
    Extract methods from all Java classes in a cloned GitHub repository using srcML.

    Args:
        repo_path (str): Path to the cloned repository.
        output_csv (str): Path to the output CSV file.
    """
    if not os.path.isdir(repo_path):
        raise FileNotFoundError(f"Repository path '{repo_path}' does not exist or is not a directory.")

    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["File Name", "Method Name", "Method Code XML", "Method Java", "Method Java Formatted"])

        # Traverse the repository to find all Java files
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".java"):
                    java_file_path = os.path.join(root, file)
                    try:
                        # Use srcML to extract method declarations from the file
                        command = ["/content/bin/./srcml", java_file_path, "--position"]
                        result = subprocess.run(command, capture_output=True, text=True)

                        if result.returncode != 0:
                            print(f"Error processing file {java_file_path}: {result.stderr}")
                            continue

                        srcml_output = result.stdout
                        #print(srcml_output)
                        methods = parse_methods_from_srcml_output(srcml_output)

                        for method_name, method_code in methods:
                            java_code = extract_raw_java_tokens_from_xml(method_code)
                            #formatted_method = beautify_java_method(java_code, "/content/google-java-format-1.25.2-all-deps.jar")
                            # Example Usage
                            try:
                                formatted_method = run_with_timeout(
                                    beautify_java_method,
                                    args=(java_code, "/content/google-java-format-1.25.2-all-deps.jar"),
                                    timeout=3
                                )
                                #print("Formatted method:", formatted_method)
                            except TimeoutException as e:
                                pass
                                #print("Timeout occurred:", e)

                            csv_writer.writerow([java_file_path, method_name, method_code, java_code, formatted_method])

                        print(f"Processed: {java_file_path}")

                    except Exception as e:
                        print(f"Error extracting methods from {java_file_path}: {e}")

def parse_methods_from_srcml_output(srcml_output):
    """
    Parse methods from srcML output.

    Args:
        srcml_output (str): The output generated by srcML for a Java file.

    Returns:
        list: A list of tuples containing method names and their full source code.
    """
    methods = []
    current_method_code = []
    inside_function = False
    method_name = None

    lines = srcml_output.splitlines()

    for line in lines:
        line = line.strip()
        if "<function" in line:  # Start of a method
            inside_function = True
            current_method_code = [line]  # Start collecting lines for the method
        elif "</function>" in line:  # End of a method
            if inside_function:
                current_method_code.append(line)
                method_code_str = "\n".join(current_method_code)
                #print(current_method_code)
                # Extract the method name after collecting the function block
                method_name = extract_method_name_from_function_block(current_method_code)
                if method_name:
                    methods.append((method_name, method_code_str))

            # Reset for the next method
            inside_function = False
            current_method_code = []
        elif inside_function:  # Inside a method, accumulate lines
            current_method_code.append(line)

    return methods


def extract_method_name_from_function_block(function_lines):
    """
    Extract the method name from a function block.

    Args:
        function_lines (list): List of lines representing the function block.

    Returns:
        str: The method name, or None if not found.
    """
    srcml_input = "".join(function_lines)
    parser = etree.XMLParser(ns_clean=True, recover=True)
    tree = etree.fromstring(srcml_input.encode('utf-8'), parser)
    method_names = tree.xpath("//function/name[not(parent::type)]/text()")
    if len(method_names)==1:
      return method_names[0].replace("<name>", "").replace("</name>", "").strip()
    else:
      return None


if __name__ == "__main__":
    # Specify the path to the cloned GitHub repository
    repository_path = "/content/java-memcached-client"

    # Specify the path to the output CSV file
    output_csv_file = "extracted_java_methods.csv"

    # Extract methods
    extract_methods_with_srcml(repository_path, output_csv_file)

    print(f"Method extraction completed. Results saved to {output_csv_file}.")

    