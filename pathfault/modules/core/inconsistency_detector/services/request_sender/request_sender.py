import socket
from multiprocessing import Process
import json
import urllib.parse
import copy
import threading
import uuid
import itertools
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

from pathfault.logger import setup_logger
from .input_tree import InputTree
from .helper_functions import _print_exception

logger = setup_logger(__name__)

class RequestSender:
    def __init__(self, config_file_path, num_procs):
        self._read_config_file(config_file_path)
        self.lock = threading.Lock()
        self.num_procs = num_procs

    def send_confusable_uri(self):
        logger.info("=== Starting confusable URI request sending sequence ===")

        # Non-standard inconsistency detection
        logger.info("[Non-Standard] Checking inconsistencies in transformation handling...")
        self._check_non_standard_inconsistency()
        logger.info("[Non-Standard] Completed check for transformation inconsistencies.")

        # Standard inconsistency detection: path normalization
        logger.info("[Standard] Checking path normalization behavior...")
        self._check_path_normalization()
        logger.info("[Standard] Completed path normalization check.")

        # Standard inconsistency detection: percent decoding
        logger.info("[Standard] Checking URI percent-decoding behavior...")
        self._check_decoding()
        logger.info("[Standard] Completed percent-decoding check.")

        logger.info("=== All confusable URI inconsistency checks finished ===")

    def _get_responses_about_non_standard_inconsistency_request(self, seed, request, char):
        threads = []
        list_responses = []
        for target_url in self.target_urls:
            request.seed = seed
            request.url = target_url
            request.host_header = self.target_hosts[target_url]

            request_copy = copy.deepcopy(request)

            # 1. Check composite value insertion in middle position. ex: /tmp1/{char}/tmp2
            thread = threading.Thread(target=self._send_data,
                                      args=(request_copy, list_responses,
                                            'tree_to_request_for_transformation_composite_middle', char))
            threads.append(thread)
            thread.start()

            # 2. Check composite value insertion in middle position without slash. ex: /tmp1/tmp2{char}tmp3/tmp4
            thread = threading.Thread(target=self._send_data,
                                      args=(request_copy, list_responses,
                                            'tree_to_request_for_transformation_composite_middle_without_slash', char))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(5)

        return list_responses

    def _run_for_transformation(self, char_pool_batch):
        """
        Process a batch of characters to test non-standard transformation inconsistencies.
        Each character is embedded in the URI to observe the server's handling behavior.
        Results are pushed into a multiprocessing-safe queue.
        """
        for i, char in enumerate(char_pool_batch):  # Iterate through assigned characters
            base_input = InputTree(self.grammar, i, "http://hostname/uri")
            base_input.build_tree(base_input.root)

            self._get_responses_about_non_standard_inconsistency_request(i, base_input, char)

    def _check_non_standard_inconsistency(self):
        """
        Launches multiprocessing jobs to check for non-standard transformation inconsistencies.
        Each process handles a subset of the extended ASCII character pool.
        Final results are written to 'transformation_results.out'.
        """
        char_pool = [chr(i) for i in range(0x00, 0x100)] + ['']
        char_batches = [char_pool[i::self.num_procs] for i in range(self.num_procs)]

        processes = [
            Process(target=self._run_for_transformation, args=(char_batches[i],))
            for i in range(self.num_procs)
        ]

        for proc in processes:
            proc.start()

        for proc in processes:
            proc.join()

    def _check_path_normalization(self):
        """
        Spawns threads to concurrently test path normalization behavior across all target URLs.
        Uses a fixed seed to generate consistent input structures.
        """
        seed = 1234
        base_input = InputTree(self.grammar, seed, "http://hostname/uri")
        base_input.build_tree(base_input.root)

        threads = []
        list_responses = []

        for target_url in self.target_urls:
            base_input.seed = seed
            base_input.url = target_url
            base_input.host_header = self.target_hosts[target_url]

            request_copy = copy.deepcopy(base_input)
            thread = threading.Thread(
                target=self._send_data,
                args=(request_copy, list_responses, 'tree_to_request_for_normalization')
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(5)

    def _check_decoding(self):
        """
        Spawns threads to test server behavior when presented with percent-encoded characters in the URI.
        Each thread sends a decoding-related request to a different target.
        """
        seed = 5678
        base_input = InputTree(self.grammar, seed, "http://hostname/uri")
        base_input.build_tree(base_input.root)

        threads = []
        list_responses = []

        for target_url in self.target_urls:
            base_input.seed = seed
            base_input.url = target_url
            base_input.host_header = self.target_hosts[target_url]

            request_copy = copy.deepcopy(base_input)
            decoding_in_range_thread = threading.Thread(
                target=self._send_data,
                args=(request_copy, list_responses, 'tree_to_request_for_decoding')
            )
            threads.append(decoding_in_range_thread)
            decoding_in_range_thread.start()

        for thread in threads:
            thread.join(5)

    def send_exploit_payload(self, inputdata, list_responses, application_comb_list=None, request_id=None, payload='/'):
        if application_comb_list is None:
            application_comb_list = []
        request = None
        _socket = None  # Initialize socket variable
        try:
            request = inputdata.tree_to_request_for_exploit_payload_validate(
                without_uri=True,
                application_comb_list=application_comb_list,
                request_id=request_id,
                payload=payload)

            print(f"Raw HTTP Request:\n{request.decode('utf-8', errors='ignore')}")

            # Create socket
            if inputdata.url.startswith('https'):
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _socket = context.wrap_socket(_socket, server_hostname=inputdata.host)
            else:
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect
            try:
                print(f"Connecting to {inputdata.host}:{inputdata.port}")
                _socket.connect((inputdata.host, int(inputdata.port)))
            except Exception as connect_exception:
                print(f"Failed to connect to {inputdata.host}:{inputdata.port} - {connect_exception}")
                return

            # Send request
            print(f"Sending raw HTTP request to {inputdata.host}:{inputdata.port}")
            _socket.sendall(request)

            # Set socket timeout
            _socket.settimeout(20)

            # Receive response
            response = b''
            while True:
                try:
                    data = _socket.recv(2048)
                    if not data:
                        break
                    response += data
                except socket.timeout:
                    print("Socket timed out while receiving data")
                    break

            print(f"Received raw HTTP Response:\n{response.decode('utf-8', errors='ignore')}")

            # Append response to list
            with self.lock:
                list_responses.append(response)

        except socket.timeout:
            with self.lock:
                list_responses.append(b"takes too long")
        except Exception as exception:
            # Safely handle request if None
            _print_exception([request if request is not None else b''])
            raise exception
        finally:
            # Ensure socket is closed
            if _socket is not None:
                try:
                    _socket.shutdown(socket.SHUT_RDWR)
                except OSError as shutdown_exception:
                    print(f"Socket shutdown error: {shutdown_exception}")
                finally:
                    _socket.close()

    def send_exploit_payload_for_experiment(self, exploit_option_file, max_threads=50):
        """
        Send all exploit payloads specified in *exploit_option_file* to every
        expanded URL combination derived from *self.target_urls* and *port_map*.
        Use a thread pool to limit the number of concurrent threads to *max_threads*.

        Args:
            exploit_option_file (str): Path to the JSON file containing exploit options.
            max_threads (int): Maximum number of concurrent threads (default: 50).

        The function keeps the original control-flow intact; only comments and
        user-facing messages have been translated from Korean → English.
        """

        print("Running exploit-validation phase …")

        # ── Load option.json ----------------------------------------------------
        try:
            with open(exploit_option_file, "r") as f:
                options = json.load(f)
                port_map_path = options.get("port_map_path")
                if not port_map_path:
                    print("❌  'port_map_path' is missing in exploit_option_file.json")
                    return
                exploit_payloads = options.get("exploit_payloads", [])
                # 'depth' option (default 2) – host is counted as depth-1
                depth = options.get("depth", 2)
        except Exception as e:
            print(f"❌  Failed to load exploit_option_file.json: {e}")
            return

        # ── Load port_map.json --------------------------------------------------
        try:
            with open(port_map_path, "r") as f:
                port_map = json.load(f)
        except Exception as e:
            print(f"❌  Failed to load port_map.json from {port_map_path}: {e}")
            return

        # Build reverse map {port → service_name}
        port_to_service = {int(port): name for name, port in port_map.items()}

        # Determine the *base* service for every target_url
        base_url_infos = []
        for target_url in self.target_urls:
            try:
                parsed = urllib.parse.urlparse(target_url)
                port = parsed.port
                svc = port_to_service.get(port)
                if svc:
                    base_url_infos.append((target_url, svc))
                    print(f"{target_url} → {svc}")
                else:
                    print(f"{target_url} → (no matching service)")
            except Exception as e:
                print(f"{target_url} → (failed to extract port: {e})")

        # ── Expand URL combinations --------------------------------------------
        expanded_combinations = []
        append_count = depth - 1  # host already counts as depth-1

        for base_url, base_service in base_url_infos:
            filtered = [s for s in port_map if s not in ("tmpserver", base_service)]
            if len(filtered) < append_count:
                print(f"❌  {base_url}: only {len(filtered)} usable services, "
                      f"but depth {depth} requested")
                continue

            for perm in itertools.permutations(filtered, append_count):
                path_components = list(perm)

                if "apachetrafficserver" in base_service:
                    # trafficserver as host → remove only the first element
                    if path_components:
                        path_components.pop(0)
                else:
                    # if trafficserver appears later, drop the element right after it
                    if "apachetrafficserver" in path_components:
                        idx = path_components.index("apachetrafficserver")
                        if idx + 1 < len(path_components):
                            path_components.pop(idx + 1)

                # Assemble full URL
                if base_url.endswith("/"):
                    full_url = base_url.rstrip("/") + "/" + "/".join(path_components)
                else:
                    full_url = base_url + "/" + "/".join(path_components)

                expanded_combinations.append((full_url, base_service, list(perm)))

        print(f"Generated {len(expanded_combinations)} combinations "
              f"(depth={depth}, appended services: {append_count})")

        # ── Assign a UUID to every payload --------------------------------------
        payload_to_uuid = {payload: str(uuid.uuid4()) for payload in exploit_payloads}

        seed = 12345
        list_responses = []
        lock = threading.Lock()  # Lock for thread-safe list_responses append

        # ── Fire requests using ThreadPoolExecutor -----------------------------
        def run_task(full_url, base_service, service_perm, payload):
            request_id = payload_to_uuid[payload]
            app_comb_list = [base_service] + list(service_perm)
            parsed_full = urllib.parse.urlparse(full_url)
            url_path = parsed_full.path.rstrip("/")

            combined_payload = url_path + payload
            print("Processing:",
                  full_url,
                  "| payload:", combined_payload,
                  "| request_id:", request_id,
                  "| app_comb_list:", app_comb_list)

            # Create a fresh InputTree per request
            base_input = InputTree(self.grammar, seed, full_url)
            base_input.build_tree(base_input.root)

            request_copy = copy.deepcopy(base_input)
            request_copy.seed = seed
            request_copy.url = full_url
            request_copy.host_header = parsed_full.hostname

            # Call send_exploit_payload
            self.send_exploit_payload(
                request_copy,
                list_responses,
                app_comb_list,
                request_id,
                combined_payload
            )

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [
                executor.submit(run_task, full_url, base_service, service_perm, payload)
                for full_url, base_service, service_perm in expanded_combinations
                for payload in exploit_payloads
            ]
            for future in as_completed(futures):
                try:
                    future.result()  # Wait for task completion
                except Exception as e:
                    print(f"Task failed with exception: {e}")

    # def send_exploit_payload_for_experiment(self, exploit_option_file):
    #     """
    #     Send all exploit payloads specified in *exploit_option_file* to every
    #     expanded URL combination derived from *self.target_urls* and *port_map*.
    #
    #     The function keeps the original control-flow intact; only comments and
    #     user-facing messages have been translated from Korean → English.
    #     """
    #
        # import json
        # import urllib.parse
        # import copy
        # import threading
        # import uuid
        # import csv
        # import itertools
    #
    #     print("Running exploit-validation phase …")
    #
    #     # ── Load option.json ----------------------------------------------------
    #     try:
    #         with open(exploit_option_file, "r") as f:
    #             options = json.load(f)
    #             port_map_path = options.get("port_map_path")
    #             if not port_map_path:
    #                 print("❌  'port_map_path' is missing in exploit_option_file.json")
    #                 return
    #             exploit_payloads = options.get("exploit_payloads", [])
    #             # 'depth' option (default 2) – host is counted as depth-1
    #             depth = options.get("depth", 2)
    #     except Exception as e:
    #         print(f"❌  Failed to load exploit_option_file.json: {e}")
    #         return
    #
    #     # ── Load port_map.json --------------------------------------------------
    #     try:
    #         with open(port_map_path, "r") as f:
    #             port_map = json.load(f)
    #     except Exception as e:
    #         print(f"❌  Failed to load port_map.json from {port_map_path}: {e}")
    #         return
    #
    #     # Build reverse map {port → service_name}
    #     port_to_service = {int(port): name for name, port in port_map.items()}
    #
    #     # Determine the *base* service for every target_url
    #     base_url_infos = []
    #     for target_url in self.target_urls:
    #         try:
    #             parsed = urllib.parse.urlparse(target_url)
    #             port = parsed.port
    #             svc = port_to_service.get(port)
    #             if svc:
    #                 base_url_infos.append((target_url, svc))
    #                 print(f"{target_url} → {svc}")
    #             else:
    #                 print(f"{target_url} → (no matching service)")
    #         except Exception as e:
    #             print(f"{target_url} → (failed to extract port: {e})")
    #
    #     # ── Expand URL combinations --------------------------------------------
    #     expanded_combinations = []
    #     append_count = depth - 1  # host already counts as depth-1
    #
    #     for base_url, base_service in base_url_infos:
    #         filtered = [s for s in port_map if s not in ("tmpserver", base_service)]
    #         if len(filtered) < append_count:
    #             print(f"❌  {base_url}: only {len(filtered)} usable services, "
    #                   f"but depth {depth} requested")
    #             continue
    #
    #         for perm in itertools.permutations(filtered, append_count):
    #             path_components = list(perm)
    #
    #             if "apachetrafficserver" in base_service:
    #                 # trafficserver as host → remove only the first element
    #                 if path_components:
    #                     path_components.pop(0)
    #             else:
    #                 # if trafficserver appears later, drop the element right after it
    #                 if "apachetrafficserver" in path_components:
    #                     idx = path_components.index("apachetrafficserver")
    #                     if idx + 1 < len(path_components):
    #                         path_components.pop(idx + 1)
    #
    #             # Assemble full URL
    #             if base_url.endswith("/"):
    #                 full_url = base_url.rstrip("/") + "/" + "/".join(path_components)
    #             else:
    #                 full_url = base_url + "/" + "/".join(path_components)
    #
    #             expanded_combinations.append((full_url, base_service, list(perm)))
    #
    #     print(f"Generated {len(expanded_combinations)} combinations "
    #           f"(depth={depth}, appended services: {append_count})")
    #
    #     # ── Assign a UUID to every payload --------------------------------------
    #     payload_to_uuid = {payload: str(uuid.uuid4()) for payload in exploit_payloads}
    #
    #     seed = 12345
    #     threads = []
    #     list_responses = []
    #
    #     # ── Fire requests -------------------------------------------------------
    #     for full_url, base_service, service_perm in expanded_combinations:
    #         for payload in exploit_payloads:
    #             request_id = payload_to_uuid[payload]
    #             app_comb_list = [base_service] + list(service_perm)
    #             parsed_full = urllib.parse.urlparse(full_url)
    #             url_path = parsed_full.path.rstrip("/")
    #
    #             combined_payload = url_path + payload
    #             print("Processing:",
    #                   full_url,
    #                   "| payload:", combined_payload,
    #                   "| request_id:", request_id,
    #                   "| app_comb_list:", app_comb_list)
    #
    #             # Create a fresh InputTree per request
    #             base_input = InputTree(self.grammar, seed, full_url)
    #             base_input.build_tree(base_input.root)
    #
    #             request_copy = copy.deepcopy(base_input)
    #             request_copy.seed = seed
    #             request_copy.url = full_url
    #             request_copy.host_header = parsed_full.hostname
    #
    #             t = threading.Thread(
    #                 target=self.send_exploit_payload,
    #                 args=(request_copy,
    #                       list_responses,
    #                       app_comb_list,
    #                       request_id,
    #                       combined_payload)
    #             )
    #             threads.append(t)
    #             t.start()
    #
    #     for t in threads:
    #         t.join(5)

    def _read_config_file(self, configfile):
        config_content = open(configfile).read().replace('config.', 'self.')
        exec(config_content)
        required_keys = [
            "target_urls", "target_host_headers", "grammar"
        ]
        for key in required_keys:
            if key not in self.__dict__:
                print(f"Missing required config key: {key}")
                exit(1)

        self.target_hosts = {
            self.target_urls[i]: self.target_host_headers[i]
            for i in range(len(self.target_urls))
        }

    def _send_data(self, inputdata, list_responses, opt='tree_to_request', char='/'):
        try:
            # Generate the request using the appropriate method
            if opt == 'tree_to_request':
                request = inputdata.tree_to_request(without_uri=True)
            elif opt == 'tree_to_request_for_normalization':
                request = inputdata.tree_to_request_for_normalization(without_uri=True)
            elif opt == 'tree_to_request_for_decoding':
                request = inputdata.tree_to_request_for_decoding(without_uri=True)
            elif opt == 'tree_to_request_for_transformation_composite_middle':
                request = inputdata.tree_to_request_for_transformation_composite_middle(without_uri=True, char=char)
            elif opt == 'tree_to_request_for_transformation_composite_middle_without_slash':
                request = inputdata.tree_to_request_for_transformation_composite_middle_without_slash(without_uri=True,
                                                                                                      char=char)

            logger.debug(f"Generated raw HTTP request:\n{request.decode('utf-8', errors='ignore')}")

            # Set up socket (SSL if needed)
            if inputdata.url.startswith('https'):
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _socket = context.wrap_socket(_socket, server_hostname=inputdata.host)
            else:
                _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                logger.debug(f"Connecting to {inputdata.host}:{inputdata.port}")
                _socket.connect((inputdata.host, int(inputdata.port)))
            except Exception as connect_exception:
                logger.debug(f"Failed to connect to {inputdata.host}:{inputdata.port} - {connect_exception}")
                return

            logger.debug(f"Sending HTTP request to {inputdata.host}:{inputdata.port}")
            _socket.sendall(request)
            _socket.settimeout(20)

            response = b''
            while True:
                try:
                    data = _socket.recv(2048)
                    if not data:
                        break
                    response += data
                except socket.timeout:
                    logger.debug("Socket timed out while receiving response")
                    break

            try:
                _socket.shutdown(socket.SHUT_RDWR)
            except OSError as shutdown_exception:
                logger.debug(f"Socket shutdown exception: {shutdown_exception}")

            _socket.close()

            logger.debug(f"Received raw HTTP response:\n{response.decode('utf-8', errors='ignore')}")

            # Append to shared response list with locking
            with self.lock:
                list_responses.append(response)

        except socket.timeout:
            with self.lock:
                list_responses.append(b"takes too long")
        except Exception as exception:
            _print_exception([request])
            raise exception