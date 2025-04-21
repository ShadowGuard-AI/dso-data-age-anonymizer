import argparse
import datetime
import logging
import random
import re
import os
import chardet
from faker import Faker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description='Shifts dates in data by a random interval to anonymize them.')
    parser.add_argument('input_file', help='Path to the input file.')
    parser.add_argument('output_file', help='Path to the output file.')
    parser.add_argument('--max_shift_days', type=int, default=365, help='Maximum number of days to shift dates by. Defaults to 365.')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility. Defaults to None.')
    parser.add_argument('--date_format', type=str, default='%Y-%m-%d', help='Date format to search for. Defaults to %Y-%m-%d.')
    parser.add_argument('--encoding', type=str, default=None, help='Encoding of the input file. If not specified, it will be detected automatically.')
    return parser.parse_args()

def detect_encoding(file_path):
    """
    Detects the encoding of a file.
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception as e:
        logging.error(f"Error detecting encoding: {e}")
        return None

def shift_date(date_str, max_shift_days, date_format, random_state):
    """
    Shifts a date by a random interval.

    Args:
        date_str (str): The date string to shift.
        max_shift_days (int): The maximum number of days to shift.
        date_format (str): The format of the date string.
        random_state (random.Random): Random number generator.

    Returns:
        str: The shifted date string, or None if an error occurred.
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, date_format).date()
        shift_days = random_state.randint(-max_shift_days, max_shift_days)
        shifted_date = date_obj + datetime.timedelta(days=shift_days)
        return shifted_date.strftime(date_format)
    except ValueError as e:
        logging.warning(f"Invalid date format or value: {date_str}. Error: {e}")
        return None
    except Exception as e:
        logging.error(f"Error shifting date {date_str}: {e}")
        return None

def anonymize_data(input_file, output_file, max_shift_days, seed, date_format, encoding=None):
    """
    Anonymizes dates in the input file and writes the result to the output file.

    Args:
        input_file (str): Path to the input file.
        output_file (str): Path to the output file.
        max_shift_days (int): Maximum number of days to shift dates by.
        seed (int): Random seed for reproducibility.
        date_format (str): Date format to search for.
        encoding (str, optional): Encoding of the input file. If None, autodetect.
    """

    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        return

    if encoding is None:
        encoding = detect_encoding(input_file)
        if encoding is None:
            logging.error("Could not detect file encoding. Please specify it using --encoding.")
            return

    try:
        with open(input_file, 'r', encoding=encoding, errors='ignore') as infile, \
                open(output_file, 'w', encoding=encoding) as outfile:

            random_state = random.Random(seed)  # Initialize random number generator
            date_regex = re.compile(r'\d{4}-\d{2}-\d{2}') # Basic YYYY-MM-DD regex

            for line in infile:
                def replace_date(match):
                    date_str = match.group(0)
                    shifted_date = shift_date(date_str, max_shift_days, date_format, random_state)
                    if shifted_date:
                        return shifted_date
                    else:
                        return date_str  # Return original date if shifting fails
                    
                anonymized_line = date_regex.sub(replace_date, line)
                outfile.write(anonymized_line)
        logging.info(f"Successfully anonymized data from {input_file} to {output_file}")

    except Exception as e:
        logging.error(f"An error occurred during anonymization: {e}")

def main():
    """
    Main function to parse arguments and run the anonymization process.
    """
    args = setup_argparse()

    # Input validation: Ensure max_shift_days is a positive integer
    if args.max_shift_days <= 0:
        logging.error("max_shift_days must be a positive integer.")
        return
    
    anonymize_data(args.input_file, args.output_file, args.max_shift_days, args.seed, args.date_format, args.encoding)


if __name__ == "__main__":
    main()