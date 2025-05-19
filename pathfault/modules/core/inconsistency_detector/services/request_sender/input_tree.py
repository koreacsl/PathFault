import uuid
import random
import re
from collections import deque

from .input_tree_node import Node
from .helper_functions import _parse_url


class InputTree:

    def __init__(self, grammar, seed, url):
        """ Constructs a request object.

        Args:
          grammar: input grammar for describing the structure
          seed: a value based on which random number is
            generated. It is used for reproducability.

          url: address of the target endpoint

        Returns:
          the constructed object
        """
        self.nonterminal_node_list = {}
        Node.symbol_counts = {}
        self.root = Node('<start>')
        self.grammar = grammar
        self.seed = seed
        random.seed(seed)
        self.url = url
        self.host_header = None

    def build_tree(self, start_node):
        self.nonterminal_node_list[start_node.id] = start_node

        node_queue = deque([start_node])
        while node_queue:
            current_node = node_queue.pop()

            possible_expansions = self.grammar[current_node.symbol]
            chosen_expansion = random.choices(possible_expansions, weights=[1.0])[0]

            for symbol in re.split(Node.RE_NONTERMINAL, chosen_expansion):
                if len(symbol) > 0:
                    new_node = Node(symbol)

                    current_node.children.append(new_node)

                    if not new_node.is_terminal:
                        node_queue.appendleft(new_node)
                        self.nonterminal_node_list[new_node.id] = new_node

        return start_node

    def tree_to_request(self, without_uri=False):
        self.request = b""
        self.expand_node(self.root)

        self.host, self.port, self.authority, self.uri = _parse_url(self.url)

        if self.host_header is None:
            self.host_header = self.authority

        request_id = str(uuid.uuid4())  # Generate unique request ID
        request_seed = str(self.seed)  # Use the current seed value

        if without_uri:
            total_uri = f"/"  # Use root path only
        else:
            total_uri = f"{self.uri}"  # Use full original URI

        body_start = self.request.find(b'\r\n\r\n') + 4  # Locate start of body
        body_length = len(self.request) - body_start  # Compute content length

        return (
            self.request
            .replace(b'_URI_', total_uri.encode('utf-8'))
            .replace(b'_HOST_', self.host_header.encode('utf-8'))
            .replace(b'_REQUEST_TYPE_', 'transformation'.encode('utf-8'))
            .replace(b'_REQUEST_ID_', request_id.encode('utf-8'))
            .replace(b'_REQUEST_SEED_', request_seed.encode('utf-8'))
            .replace(b'_CONTENT_LENGTH_', str(body_length).encode('utf-8'))
        )

    def tree_to_request_for_transformation_composite_middle_without_slash(self, without_uri=False, char='/'):
        self.request = b""
        self.expand_node(self.root)

        self.host, self.port, self.authority, self.uri = _parse_url(self.url)

        if self.host_header is None:
            self.host_header = self.authority

        request_id = str(uuid.uuid4())  # Generate unique request ID

        request_seed = f"{ord(char):X}" if char else 'EMPTY'  # Use character's ordinal value in hex

        if without_uri:
            total_uri = f"/tmp1/tmp2{char}tmp3/tmp4"  # Construct URI without base path
        else:
            total_uri = f"{self.uri}/tmp1/tmp2{char}tmp3/tmp4"  # Construct URI with base path

        body_start = self.request.find(b'\r\n\r\n') + 4  # Locate start of body
        body_length = len(self.request) - body_start  # Compute content length

        return (
            self.request
            .replace(b'_URI_', total_uri.encode('utf-8'))
            .replace(b'_HOST_', self.host_header.encode('utf-8'))
            .replace(b'_REQUEST_TYPE_', 'transformation_composite_middle_without_slash'.encode('utf-8'))
            .replace(b'_REQUEST_ID_', request_id.encode('utf-8'))
            .replace(b'_REQUEST_SEED_', request_seed.encode('utf-8'))
            .replace(b'_CONTENT_LENGTH_', str(body_length).encode('utf-8'))
        )

    def tree_to_request_for_transformation_composite_middle(self, without_uri=False, char='/'):
        self.request = b""
        self.expand_node(self.root)

        self.host, self.port, self.authority, self.uri = _parse_url(self.url)

        if self.host_header is None:
            self.host_header = self.authority

        request_id = str(uuid.uuid4())  # Generate unique request ID

        request_seed = f"{ord(char):X}" if char else 'EMPTY'  # Use character's ordinal value in hex

        if without_uri:
            total_uri = f"/tmp1/{char}/tmp2"  # Construct URI without base path
        else:
            total_uri = f"{self.uri}/tmp1/{char}/tmp2"  # Construct URI with base path

        body_start = self.request.find(b'\r\n\r\n') + 4  # Locate start of body
        body_length = len(self.request) - body_start  # Compute content length

        return (
            self.request
            .replace(b'_URI_', total_uri.encode('utf-8'))
            .replace(b'_HOST_', self.host_header.encode('utf-8'))
            .replace(b'_REQUEST_TYPE_', 'transformation_composite_middle'.encode('utf-8'))
            .replace(b'_REQUEST_ID_', request_id.encode('utf-8'))
            .replace(b'_REQUEST_SEED_', request_seed.encode('utf-8'))
            .replace(b'_CONTENT_LENGTH_', str(body_length).encode('utf-8'))
        )

    def tree_to_request_for_normalization(self, without_uri=False):
        self.request = b""
        self.expand_node(self.root)

        self.host, self.port, self.authority, self.uri = _parse_url(self.url)

        if self.host_header is None:
            self.host_header = self.authority

        request_id = str(uuid.uuid4())  # Generate unique request ID
        request_seed = str(self.seed)  # Use current seed value

        if without_uri:
            total_uri = f"/tmp1/../tmp2"  # Construct URI without base path
        else:
            total_uri = f"{self.uri}/tmp1/../tmp2"  # Construct URI with base path

        body_start = self.request.find(b'\r\n\r\n') + 4  # Locate start of body
        body_length = len(self.request) - body_start  # Compute content length

        return (
            self.request
            .replace(b'_URI_', total_uri.encode('utf-8'))
            .replace(b'_HOST_', self.host_header.encode('utf-8'))
            .replace(b'_REQUEST_TYPE_', 'normalization'.encode('utf-8'))
            .replace(b'_REQUEST_ID_', request_id.encode('utf-8'))
            .replace(b'_REQUEST_SEED_', request_seed.encode('utf-8'))
            .replace(b'_CONTENT_LENGTH_', str(body_length).encode('utf-8'))
        )

    def tree_to_request_for_decoding(self, without_uri=False):
        self.request = b""
        self.expand_node(self.root)

        self.host, self.port, self.authority, self.uri = _parse_url(self.url)

        if self.host_header is None:
            self.host_header = self.authority

        request_id = str(uuid.uuid4())  # Generate unique request ID
        request_seed = str(self.seed)  # Use current seed value

        if without_uri:
            total_uri = f"/%21"  # Construct URI with encoded character only
        else:
            total_uri = f"{self.uri}/%21"  # Construct URI with base + encoded

        body_start = self.request.find(b'\r\n\r\n') + 4  # Locate start of body
        body_length = len(self.request) - body_start  # Compute content length

        return (
            self.request
            .replace(b'_URI_', total_uri.encode('utf-8'))
            .replace(b'_HOST_', self.host_header.encode('utf-8'))
            .replace(b'_REQUEST_TYPE_', 'decoding_in_range'.encode('utf-8'))
            .replace(b'_REQUEST_ID_', request_id.encode('utf-8'))
            .replace(b'_REQUEST_SEED_', request_seed.encode('utf-8'))
            .replace(b'_CONTENT_LENGTH_', str(body_length).encode('utf-8'))
        )

    def tree_to_request_for_exploit_payload_validate(
            self,
            without_uri=False,
            application_comb_list=None,
            request_id=None,
            payload=''):

        if application_comb_list is None:
            application_comb_list = []

        self.request = b""
        self.expand_node(self.root)

        self.host, self.port, self.authority, self.uri = _parse_url(self.url)

        if self.host_header is None:
            self.host_header = self.authority

        request_seed = self.seed

        if without_uri:
            total_uri = f'{payload}'  # 문자열로 결합
        else:
            total_uri = f"{self.uri}{payload}"  # 문자열로 결합

        # 요청의 Body 길이 계산
        body_start = self.request.find(b'\r\n\r\n') + 4
        body_length = len(self.request) - body_start

        # 요청에 필요한 값을 치환
        return (
            self.request
            .replace(b'_URI_', total_uri.encode('utf-8'))
            .replace(b'_HOST_', self.host_header.encode('utf-8'))
            .replace(b'_REQUEST_TYPE_', f'{'_'.join(application_comb_list)}'.encode('utf-8'))
            .replace(b'_REQUEST_ID_', request_id.encode('utf-8'))
            .replace(b'_REQUEST_SEED_', str(request_seed).encode('utf-8'))
            .replace(b'_CONTENT_LENGTH_', str(body_length).encode('utf-8'))
        )

    def expand_node(self, node):
        if node.is_terminal:
            self.request += node.symbol.encode('utf-8')
        else:
            for child in node.children:
                self.expand_node(child)
