
RUN apt-get update && apt-get install -y \
    libpcap-dev \
    zlib1g-dev \
    libpcre2-8-0 \
    libpcre2-dev \
    iproute2 \
    git \
    make \
    gcc \
    g++ \
    wget \
    xz-utils \
    cmake \
    libglib2.0-dev \
    libgcrypt20-dev \
    flex \
    bison \
    libpcap-dev \
    qtbase5-dev \
    libssh-dev \
    libsystemd-dev \
    qtmultimedia5-dev \
    libqt5svg5-dev \
    qttools5-dev-tools \
    libc-ares-dev \
    libspeexdsp-dev \
    asciidoctor \
    xsltproc \
    doxygen \
    libpcre2-dev \
    libxml2-dev


# Wireshark 최신 소스 다운로드
RUN wget https://www.wireshark.org/download/src/wireshark-4.4.10.tar.xz -O /tmp/wireshark-4.4.10.tar.xz

# 소스 파일 압축 해제
RUN mkdir -p /build/wireshark && tar -xvf /tmp/wireshark-4.4.10.tar.xz -C /build/wireshark --strip-components=1

# CMake로 빌드 설정
RUN cmake -S /build/wireshark -B /build/wireshark/build -DBUILD_wireshark=OFF

# 소스 빌드
RUN make -C /build/wireshark/build

# 빌드 결과 설치
RUN make -C /build/wireshark/build install

# 동적 라이브러리 경로 업데이트
RUN ldconfig

# 불필요한 파일 정리
RUN rm -rf /tmp/wireshark-latest.tar.xz /build/wireshark

# 엔트리포인트 스크립트 복사
COPY entrypoint.sh /app/entrypoint.sh

# 스크립트 실행 권한 부여
RUN chmod +x /app/entrypoint.sh

# 엔트리포인트 설정
ENTRYPOINT ["/app/entrypoint.sh"]